import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".", "libs"))
import yaml
from aqt import mw

def load_config():
    """
    Loads and parses the add-on's YAML configuration file.
    
    Returns:
        dict: Configuration dictionary containing:
            - note_model_name: Custom note type name
            - language_levels: List of supported CEFR levels
            - languages.supported_source_languages: List of available languages
            - openai.text_model: Model ID for text generation
            - openai.tts_model: Model ID for audio generation
            - openai.translation_prompt: Template for translation requests
    
    Raises:
        FileNotFoundError: If config.yml is missing
        yaml.YAMLError: If config file contains invalid YAML syntax
    """
    # Get the root addon directory (two levels up from config_utils.py)
    addon_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(addon_dir, "config.yml")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise e

def load_config_anki():
    """
    Loads configuration from Anki's meta.json
    
    Returns:
        dict: Configuration dictionary containing Anki-specific settings like:
            - default_deck: Name of the default deck
            - show_notifications: Boolean for notification preferences
            - user_email: Email address for subscription verification
            - openai_api_key: OpenAI API authentication key
    """
    config = mw.addonManager.getConfig(__name__)
    if not config:
        default_config = {
            "default_deck": "Default",
            "show_notifications": False,
            "user_email": "",
            "openai_api_key": ""
        }
        mw.addonManager.writeConfig(__name__, default_config)
        return default_config
    
    # Ensure required fields exist in config
    required_fields = {
        "user_email": "",
        "openai_api_key": ""
    }
    
    config_modified = False
    for field, default_value in required_fields.items():
        if field not in config:
            config[field] = default_value
            config_modified = True
    
    if config_modified:
        mw.addonManager.writeConfig(__name__, config)
    
    return config

def save_config_anki(config):
    """
    Saves the configuration to Anki's meta.json
    
    Args:
        config (dict): Configuration dictionary to save
    """
    mw.addonManager.writeConfig(__name__, config)

