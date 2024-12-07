import openai
from .config_utils import load_config, load_config_anki

# Add the libs folder to the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".", "libs"))
from openai import APIConnectionError, AuthenticationError, OpenAIError
from openai import OpenAI
from aqt.qt import QThread, pyqtSignal
import json
import random
import logging
from aqt import mw
from PIL import Image
import requests


files_dir = os.path.join(os.path.dirname(__file__), "audio_files")
os.makedirs(files_dir, exist_ok=True)  # Ensure the directory exists

config = load_config()
anki_config = load_config_anki()
# Initialize OpenAI API key
openai.api_key = anki_config.get('openai_api_key', '')

class TranslationWorker(QThread):
    """
    Asynchronous worker thread for generating word translations and examples.
    
    Signals:
        finished (dict): Emitted with complete word profile on successful generation
        error (str): Emitted with error message if generation fails
    
    Uses OpenAI API to generate comprehensive word profiles including:
    - Translations
    - Grammatical information
    - Context-appropriate example sentences
    """

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, word, source_language, language_level, generate_image=True, generate_audio=True):
        super().__init__()
        self.word = word
        self.source_language = source_language
        self.language_level = language_level
        self.generate_image = generate_image
        self.generate_audio = generate_audio
        self.config = load_config()
        self.anki_config = load_config_anki()

    def run(self):
        try:
            client = OpenAI(api_key=self.anki_config.get('openai_api_key', ''))

            # Load and format the prompt from the configuration
            prompt_template = self.config.get('openai', {}).get('translation_prompt', '')
            prompt = prompt_template.format(
                source_language=self.source_language,
                language_level=self.language_level
            )
            model = self.config.get('openai', {}).get('text_model', '')
            json_schema = self.config.get('openai', {}).get('schema', {})

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": self.word
                    }
                ],
                functions=[
                    {
                        "name": "generate_word_profile",
                        "description": "Generates a word profile with translations and examples.",
                        "parameters": json_schema
                    }
                ],
                function_call={"name": "generate_word_profile"}
            )
            word_profile_arguments = response.choices[0].message.function_call.arguments
            word_profile_arguments = json.loads(word_profile_arguments)
            self.finished.emit(word_profile_arguments)  # Emit the dictionary
        except (APIConnectionError, AuthenticationError, OpenAIError) as e:
            logging.error(f"OpenAI error: {e}")
            self.error.emit(str(e))
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            self.error.emit(str(e))


def get_media_folder():
    """
    Get the directory path for storing media files (audio, images) within the add-on's folder.
    Ensures the directory exists.
    """
    # Get the add-on's directory
    addon_dir = os.path.join(mw.addonManager.addonsFolder(), "intelli_deck_addon")
    media_dir = os.path.join(addon_dir, "media_files")
    os.makedirs(media_dir, exist_ok=True)  # Ensure the directory exists
    return media_dir


class TTSWorker(QThread):
    """
    Asynchronous worker thread for generating text-to-speech audio.
    
    Signals:
        finished (dict): Emitted with dictionary of audio file paths on successful generation
        error (str): Emitted with error message if generation fails
    """
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, word_profile):
        super().__init__()
        self.word_profile = word_profile
        self.config = load_config()
        self.anki_config = load_config_anki()
        
    def run(self):
        try:
            voice = random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
            main_word = self.word_profile['german_word']
            audio_files_dir = get_media_folder()
            audio_paths_dict = {}
            
            client = OpenAI(api_key=self.anki_config.get('openai_api_key', ''))
            tts_model = self.config.get('openai', {}).get('tts_model', 'tts-1')
            
            # Generate audio for examples
            for index, example in enumerate(self.word_profile.get('examples', [])):
                example_audio_path = os.path.join(audio_files_dir, f"{main_word}_example_{index + 1}.mp3")
                response = client.audio.speech.create(
                    model=tts_model,
                    input=example['german_example'],
                    voice=voice
                )
                with open(example_audio_path, 'wb') as audio_file:
                    audio_file.write(response.content)
                audio_paths_dict[f'example_{index+1}_audio_filename'] = os.path.relpath(example_audio_path, mw.addonManager.addonsFolder())

            self.finished.emit(audio_paths_dict)
            
        except Exception as e:
            logging.error(f"Error generating TTS audio: {e}")
            self.error.emit(str(e))


class ImageWorker(QThread):
    """
    Asynchronous worker thread for generating images using DALL-E.
    
    Signals:
        finished (str): Emitted with image file path on successful generation
        error (str): Emitted with error message if generation fails
    """
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, word_profile):
        super().__init__()
        self.word_profile = word_profile
        self.config = load_config()
        self.anki_config = load_config_anki()
        
    def run(self):
        try:
            client = OpenAI(api_key=self.anki_config.get('openai_api_key', ''))
            image_model = self.config.get('openai', {}).get('image_model', 'dall-e-3')
            image_size = self.config.get('openai', {}).get('image_size', '1024x1024')
            word = self.word_profile['german_word']

            # Generate image prompt based on word profil
            image_prompt = f"Create a clear, simple illustration representing the word '{self.word_profile['german_word']}'. The image should be easily recognizable and suitable for language learning. The image should focus on the word itslef not the examples. the image should not have any letters on it."
            # Generate image using DALL-E
            image_response = client.images.generate(
                model=image_model,
                prompt=image_prompt,
                n=1,
                size=image_size,
            )
            
            # Download and process image
            image_url = image_response.data[0].url
            image_data = requests.get(image_url).content
            
            # Get media folder path and create file paths
            media_dir = get_media_folder()
            temp_image_path = os.path.join(media_dir, "temp_image.jpg")
            final_image_path = os.path.join(media_dir, f"{word}_image.jpg")
            
            # Save temporary image
            with open(temp_image_path, 'wb') as temp_image_file:
                temp_image_file.write(image_data)
            
            # Resize and save final image
            with Image.open(temp_image_path) as img:
                resized_img = img.resize((256, 256))
                resized_img.save(final_image_path)
            
            # Clean up temporary file
            os.remove(temp_image_path)
            
            # Emit relative path for Anki media
            relative_path = os.path.relpath(final_image_path, mw.addonManager.addonsFolder())
            self.finished.emit(relative_path)
            
        except Exception as e:
            logging.error(f"Error generating image: {e}")
            self.error.emit(str(e))