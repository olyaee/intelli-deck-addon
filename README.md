# Intelli-Deck: An Open-Source Anki Add-on for German Language Learners

[![intelli-deck.png](https://i.postimg.cc/NfMvL96G/intelli-deck.png)](https://postimg.cc/BtdVVv7R)

Intelli-Deck is a specialized, **open-source** Anki add-on designed to support German language learners in creating high-quality study materials quickly and efficiently. By integrating AI tools like OpenAI's GPT and DALL-E, this add-on automates the generation of comprehensive flashcards that include:

- **Translations:** Accurate translations between German and supported source languages (e.g., English, Farsi, Spanish, and more).  
- **Grammatical Information:** Detailed data for German articles, plural forms, verb conjugations (Präsens, Präteritum, Perfekt), and word classifications (noun, verb, adjective).  
- **Example Sentences:** CEFR-level-appropriate example sentences (A1–C2), translated into the source language.  
- **Audio Pronunciations:** Text-to-speech audio for vocabulary words and example sentences.  
- **AI-Generated Images:** Visual aids created using DALL-E to enhance learning and retention.  

## Why Intelli-Deck?

Intelli-Deck eliminates the time-consuming task of manually creating flashcards by automating the entire process. Whether you're expanding your vocabulary, mastering German grammar, or preparing for exams, this add-on provides a seamless and efficient way to enhance your language learning experience.

## Development Setup

### **Set Python Version**
First, set up the correct Python environment:
```bash
pyenv local 3.9.15 && poetry env use 3.9.15 && python --version
```

### **Install and Bundle Dependencies**
To manage project dependencies:

1. Install project dependencies using Poetry:
   ```bash
   poetry install
   ```

2. Export dependencies to requirements.txt:
   ```bash
   poetry export -f requirements.txt --without-hashes -o requirements.txt
   ```

3. Bundle dependencies into the addon's libs folder:
   ```bash
   pip install -r requirements.txt --target ./src/intelli_deck_addon/libs
   ```

This process ensures all dependencies (including transitive ones) are available in Anki.

### **Setup Development Link**
For development purposes, we need to create a symbolic link between the addon source code and Anki's addon directory. This allows you to make changes to the code and see them reflected immediately in Anki without having to manually copy files.

To create the symlink:
```bash
./setup_symlink.sh
```

### **Create Release Package**
To create a clean distribution package for AnkiWeb:

1. Clean up temporary and system files:
2. Create the .ankiaddon package:

```bash
cd src/intelli_deck_addon && \
find . -name "__pycache__" -type d -exec rm -r {} + && \
find . -name ".DS_Store" -type f -delete && \
zip -r ../../intelli_deck_addon.ankiaddon * \
    -x "*.pyc" "*.pyo" "*.pyd" "*__pycache__*" "*.DS_Store"
```

This will create `intelli_deck_addon.ankiaddon` in the project root directory, ready for uploading to AnkiWeb.

## Availability

Intelli-Deck is currently focused on German learners. However, if there's enough interest, the project may expand to support other languages. The project is open source and available on GitHub: [https://github.com/olyaee/intelli-deck-addon](https://github.com/olyaee/intelli-deck-addon).

Feel free to share your feedback at **olyaee.ehsan@gmail.com**.

⚠️ **Note:** The add-on currently works only on Mac. Windows users may encounter the following error:
```
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```

Contributions are welcome to resolve this issue and make the add-on Windows-compatible.

## Shared Decks

The following decks were generated using Intelli-Deck:  
- [Deck 1](https://ankiweb.net/shared/info/1298768926)  
- [Deck 2](https://ankiweb.net/shared/info/248140551)  

Start transforming your German learning experience today!