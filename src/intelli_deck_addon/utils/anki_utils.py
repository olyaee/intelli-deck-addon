from aqt import mw
from aqt.utils import showInfo
from .config_utils import load_config  # Import the config loader
import os
import shutil


def create_custom_note_type():
    """
    Creates a specialized note type for language learning cards if it doesn't exist.
    
    Features:
    - Dual-sided cards (source language ↔ target language)
    - Fields for grammatical information (articles, plural forms, verb conjugations)
    - Example sentence fields with translations
    - Audio and image support
    - Customizable formatting templates
    """
    # Load note type name from config
    config = load_config()
    note_type_name = config.get("note_model_name", "Custom Note Type")

    # Check if the note type already exists
    existing_model = mw.col.models.by_name(note_type_name)
    if existing_model:
        showInfo(f"Note type '{note_type_name}' already exists.")
        return  # Note type already exists, no need to create it again

    # Create a new model
    mm = mw.col.models
    model = mm.new(note_type_name)

    # Define fields
    fields = [
        {"name": "Wort_DE"},
        {"name": "Wort_SL"},
        {"name": "Wortarten"},
        {"name": "Audio_Wort"},
        {"name": "Artikel"},
        {"name": "Plural"},
        {"name": "Praesens"},
        {"name": "Praeteritum"},
        {"name": "Perfekt"},
        {"name": "Picture"},
        {"name": "Satz1_DE"},
        {"name": "Satz1_SL"},
        {"name": "Audio_S1"},
        {"name": "Satz2_DE"},
        {"name": "Satz2_SL"},
        {"name": "Audio_S2"},
        {"name": "Satz3_DE"},
        {"name": "Satz3_SL"},
        {"name": "Audio_S3"}
    ]
    for field in fields:
        mm.add_field(model, mm.new_field(field["name"]))

    # Define templates
    templates = [
        {
            "name": "Card 1 DE->SL",
            "qfmt": "{{Wort_DE}}{{Wortarten}}{{Audio_Wort}}",
            "afmt": """
                {{#Artikel}}{{Artikel}}{{/Artikel}}
                {{Wort_DE}}{{Wortarten}}
                {{#Plural}}{{Plural}}{{/Plural}}
                <div>{{Picture}}</div>
                <div style='font-family: Arial; font-size: 16px;'>
                {{#Praesens}}<br>Präsens: {{Praesens}}{{/Praesens}}
                {{#Praeteritum}}<br>Präteritum: {{Praeteritum}}{{/Praeteritum}}
                {{#Perfekt}}<br>Perfekt: {{Perfekt}}{{/Perfekt}}
                </div>
                <hr id=answer>
                {{Wort_SL}}
                <hr>
                <div style="display:none">[sound:_LongSilence.mp3]</div>
                {{#Satz1_DE}}
                <div style='font-family: Arial; font-size: 16px;'>{{Satz1_DE}}{{Audio_S1}}</div>
                <div style='font-family: Arial; font-size: 14px;'>{{Satz1_SL}}</div><br>
                {{/Satz1_DE}}
                {{#Satz2_DE}}
                <div style='font-family: Arial; font-size: 16px;'>{{Satz2_DE}}{{Audio_S2}}</div>
                <div style='font-family: Arial; font-size: 14px;'>{{Satz2_SL}}</div><br>
                {{/Satz2_DE}}
                {{#Satz3_DE}}
                <div style='font-family: Arial; font-size: 16px;'>{{Satz3_DE}}{{Audio_S3}}</div>
                <div style='font-family: Arial; font-size: 14px;'>{{Satz3_SL}}</div><br>
                {{/Satz3_DE}}
            """
        },
        {
            "name": "Card 2 SL->DE",
            "qfmt": "{{Wort_SL}}",
            "afmt": """
                {{Wort_SL}}
                <hr id=answer>
                {{#Artikel}}{{Artikel}}{{/Artikel}}
                {{Wort_DE}}{{Wortarten}}
                {{#Plural}}{{Plural}}{{/Plural}}
                {{Audio_Wort}}
                <div>{{Picture}}</div>
                <div style='font-family: Arial; font-size: 16px;'>
                {{#Praesens}}<br>Präsens: {{Praesens}}{{/Praesens}}
                {{#Praeteritum}}<br>Präteritum: {{Praeteritum}}{{/Praeteritum}}
                {{#Perfekt}}<br>Perfekt: {{Perfekt}}{{/Perfekt}}
                </div>
                <hr>
                <div style="display:none">[sound:_LongSilence.mp3]</div>
                {{#Satz1_SL}}
                <div style='font-family: Arial; font-size: 16px;'>{{Satz1_SL}}</div>
                <div style='font-family: Arial; font-size: 14px;'>{{Satz1_DE}}{{Audio_S1}}</div><br>
                {{/Satz1_SL}}
                {{#Satz2_SL}}
                <div style='font-family: Arial; font-size: 16px;'>{{Satz2_SL}}</div>
                <div style='font-family: Arial; font-size: 14px;'>{{Satz2_DE}}{{Audio_S2}}</div><br>
                {{/Satz2_SL}}
                {{#Satz3_SL}}
                <div style='font-family: Arial; font-size: 16px;'>{{Satz3_SL}}</div>
                <div style='font-family: Arial; font-size: 14px;'>{{Satz3_DE}}{{Audio_S3}}</div><br>
                {{/Satz3_SL}}
            """
        }
    ]
    for template in templates:
        card_template = mm.new_template(template["name"])
        card_template['qfmt'] = template["qfmt"]
        card_template['afmt'] = template["afmt"]
        mm.add_template(model, card_template)

    # Add the new model to the collection
    mm.add(model)
    showInfo(f"Note type '{note_type_name}' created successfully.")


def add_note_to_deck(word_profile, deck_id, show_notifications=True):
    """
    Creates and adds a new vocabulary note to the specified Anki deck.
    
    Args:
        word_profile (dict): Dictionary containing:
            - german_word: The German word
            - source_language_translation: Translation in source language
            - classification: Word type (noun, verb, etc.)
            - additional_grammatical_info: Dictionary of grammar details
            - examples: List of example sentences
            - audio_filename: Path to pronunciation audio (optional)
        deck_id (int): Target Anki deck identifier
        show_notifications (bool): Whether to display success/error messages
    
    Returns:
        bool: True if note was added successfully, False otherwise
    
    Raises:
        Exception: If note type creation fails or required fields are missing
    """
    try:
        # Load config to get note type name
        config = load_config()
        note_type_name = config.get("note_model_name", "Custom Note Type")
        
        # Get the note type
        model = mw.col.models.by_name(note_type_name)
        if not model:
            if show_notifications:
                showInfo("Note type not found. Creating it now...")
            create_custom_note_type()
            model = mw.col.models.by_name(note_type_name)
            if not model:
                raise Exception("Failed to create note type")

        # Create a new note
        note = mw.col.new_note(model)
        
        # Map word profile to note fields
        note['Wort_DE'] = word_profile['german_word']
        note['Wort_SL'] = word_profile['source_language_translation']
        note['Wortarten'] = word_profile['classification']
        
        # Handle additional grammatical info based on word type
        additional_info = word_profile.get('additional_grammatical_info', {})
        
        noun_info = additional_info.get('noun', {})
        note['Artikel'] = noun_info.get('article', '')
        note['Plural'] = noun_info.get('plural_form', '')
            
        # Handle verb-specific fields
        verb_info = additional_info.get('verb', {})
        if verb_info.get('irregular_verb'):
            note['Praesens'] = ', '.join(verb_info.get('praesens', []))
            note['Praeteritum'] = ', '.join(verb_info.get('praeteritum', []))
            note['Perfekt'] = ', '.join(verb_info.get('perfekt', []))
            
        # Handle example sentences
        examples = word_profile.get('examples', [])
        for i, example in enumerate(examples, 1):
            if i <= 3:  # We have fields for up to 3 examples
                note[f'Satz{i}_DE'] = example.get('german_example', '')
                note[f'Satz{i}_SL'] = example.get('source_example_translation', '')

        # Handle audio files
        if word_profile.get('audio_filename'):
            audio_path = os.path.join(mw.addonManager.addonsFolder(), word_profile['audio_filename'])
            if os.path.exists(audio_path):
                filename = os.path.basename(audio_path)
                media_filename = f"ai_anki_{filename}"
                shutil.copy2(audio_path, os.path.join(mw.col.media.dir(), media_filename))
                note['Audio_Wort'] = f"[sound:{media_filename}]"

        # Handle example audio files
        for i in range(len(examples)):
            if i < 3:  # Only process up to 3 examples
                example_key = f"example_{i+1}_audio_filename"
                if word_profile.get(example_key):
                    audio_path = os.path.join(mw.addonManager.addonsFolder(), word_profile[example_key])
                    if os.path.exists(audio_path):
                        filename = os.path.basename(audio_path)
                        media_filename = f"ai_anki_{filename}"
                        shutil.copy2(audio_path, os.path.join(mw.col.media.dir(), media_filename))
                        note[f'Audio_S{i+1}'] = f"[sound:{media_filename}]"

        # Handle image file
        if word_profile.get('image_path'):
            image_path = os.path.join(mw.addonManager.addonsFolder(), word_profile['image_path'])
            if os.path.exists(image_path):
                filename = os.path.basename(image_path)
                media_filename = f"ai_anki_{filename}"
                shutil.copy2(image_path, os.path.join(mw.col.media.dir(), media_filename))
                note['Picture'] = f'<img src="{media_filename}">'

        # Set the deck for the note
        note.note_type()['did'] = deck_id
        
        # Add the note to the collection
        mw.col.add_note(note, deck_id)
        
        # Save changes
        mw.col.save()
        
        return True
        
    except Exception as e:
        if show_notifications:
            showInfo(f"Error adding note: {str(e)}")
        return False


def get_all_decks():
    """
    Gets all available decks from Anki.
    
    Returns:
        dict: Dictionary of deck names to deck IDs
    """
    decks = mw.col.decks.all_names_and_ids()
    return {deck.name: deck.id for deck in decks}