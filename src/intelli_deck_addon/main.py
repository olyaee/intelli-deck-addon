import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))
from aqt import mw
from aqt.utils import showInfo
from aqt.qt import (
    QAction, QDialog, QVBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMovie, QHBoxLayout,
    QTextEdit, QCheckBox, QPixmap, QSize, QWidget
)
from aqt.qt import Qt
from aqt.sound import av_player
from .utils.config_utils import load_config, load_config_anki, save_config_anki
from .utils.example_generator import TranslationWorker, TTSWorker, ImageWorker
from .utils.anki_utils import add_note_to_deck, get_all_decks

def setup_menu():
    """
    Initializes the add-on's menu integration in Anki.
    
    Creates a new menu item "Add New Word" under Anki's Tools menu that launches
    the word addition dialog when clicked. This serves as the primary entry point
    for users to access the add-on's functionality.
    """
    action = QAction("Add New Word", mw)
    action.triggered.connect(show_add_word_dialog)
    mw.form.menuTools.addAction(action)

class AddWordDialog(QDialog):
    """
    Interactive dialog for adding vocabulary words to Anki decks.
    
    This dialog provides a complete interface for:
    - Word input and language selection
    - CEFR level selection (A1-C2)
    - AI-powered content generation:
        * Translations and grammatical information
        * Example sentences with translations
        * Audio pronunciation (optional)
        * Related images (optional)
    - Deck selection and card creation
    
    Features:
    - Real-time progress indicators for async operations
    - Audio playback for generated pronunciations
    - Preview of generated content before adding
    - Error handling and user feedback
    - Configurable notifications
    
    The dialog maintains state for translation, audio, and image generation
    to ensure all requested content is ready before allowing card creation.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()  # Store the global config as instance variable
        self.anki_config = load_config_anki()  # Add Anki config loading
        
        self.setWindowTitle("AI Anki Card Generator")
        self.setMinimumWidth(800)  # Wider window to accommodate columns
        
        # Main layout
        main_layout = QHBoxLayout()  # Changed to horizontal layout for columns
        
        # Create a widget to hold both image and spinner with relative positioning
        self.image_widget = QWidget()  # Make it an instance variable
        self.image_widget.setFixedSize(200, 200)
        image_layout = QVBoxLayout(self.image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #CCCCCC;
                background-color: #F5F5F5;
                border-radius: 4px;
            }
        """)
        image_layout.addWidget(self.image_label)
        
        # Set up spinner
        self.image_spinner_label = QLabel(self.image_widget)
        self.image_spinner_movie = QMovie(os.path.join(os.path.dirname(__file__), "assets", "spinner.gif"))
        self.image_spinner_movie.setScaledSize(QSize(40, 40))
        self.image_spinner_label.setMovie(self.image_spinner_movie)
        self.image_spinner_label.hide()
        
        # Center the spinner by calculating the position
        spinner_x = (200 - 40) // 2
        spinner_y = (200 - 40) // 2
        self.image_spinner_label.move(spinner_x, spinner_y)
        
        # Left Column (Input Controls)
        left_column = QVBoxLayout()
        
        # Title
        title_label = QLabel("Enter a German or source language word to generate an Anki card with detailed information.")
        title_label.setWordWrap(True)
        left_column.addWidget(title_label)
        
        # Checkboxes
        checkbox_layout = QVBoxLayout()
        self.generate_image_checkbox = QCheckBox("Generate Image")
        self.generate_audio_checkbox = QCheckBox("Generate Audio")
        self.generate_audio_checkbox.stateChanged.connect(self.on_audio_checkbox_changed)
        checkbox_layout.addWidget(self.generate_image_checkbox)
        checkbox_layout.addWidget(self.generate_audio_checkbox)
        left_column.addLayout(checkbox_layout)
        
        # Language Selection
        language_label = QLabel("Select the source language:")
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(self.config.get('languages', {}).get('supported_source_languages', []))
        left_column.addWidget(language_label)
        left_column.addWidget(self.language_dropdown)

        # Proficiency Level
        level_label = QLabel("Select the proficiency level:")
        self.level_dropdown = QComboBox()
        self.level_dropdown.addItems(self.config.get('language_levels', []))
        left_column.addWidget(level_label)
        left_column.addWidget(self.level_dropdown)

        # Word Input
        word_label = QLabel("Enter a German or source language word:")
        self.word_input = QLineEdit()
        left_column.addWidget(word_label)
        left_column.addWidget(self.word_input)

        # Deck Selection
        self.decks = get_all_decks()
        deck_label = QLabel("Select Deck:")
        self.deck_dropdown = QComboBox()
        self.deck_dropdown.addItems(self.decks.keys())
        
        # Set default deck from anki config
        default_deck = self.anki_config.get("default_deck", "Default")
        if default_deck in self.decks:
            self.deck_dropdown.setCurrentText(default_deck)
            
        left_column.addWidget(deck_label)
        left_column.addWidget(self.deck_dropdown)

        # Generate Button
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_translation)
        left_column.addWidget(self.generate_button)

        # Add Button
        self.add_button = QPushButton("Add to Anki")
        self.add_button.clicked.connect(self.add_word)
        self.add_button.setEnabled(False)
        left_column.addWidget(self.add_button)

        left_column.addStretch()  # Pushes everything up
        
        # Right Column (Results)
        right_column = QVBoxLayout()
        
        # Create header layout with translation label and audio player
        header_layout = QHBoxLayout()

        # Left side: Translation label and its spinner
        translation_left_layout = QHBoxLayout()
        translation_label = QLabel("Word and Grammar Information:")
        self.spinner_label = QLabel()  # Translation spinner
        self.spinner_movie = QMovie(os.path.join(os.path.dirname(__file__), "assets", "spinner.gif"))
        self.spinner_movie.setScaledSize(QSize(20, 20))
        self.spinner_label.setMovie(self.spinner_movie)
        self.spinner_label.hide()
        translation_left_layout.addWidget(translation_label)
        translation_left_layout.addWidget(self.spinner_label)
        header_layout.addLayout(translation_left_layout)

        # Right side: Audio button and its spinner
        header_layout.addStretch()  # Push audio controls to the right
        self.play_audio_button = QPushButton("Play Audio")
        self.play_audio_button.clicked.connect(self.play_audio)
        self.play_audio_button.setEnabled(False)
        self.play_audio_button.hide()
        header_layout.addWidget(self.play_audio_button)

        # # Audio spinner
        self.audio_spinner_label = QLabel()
        self.audio_spinner_movie = QMovie(os.path.join(os.path.dirname(__file__), "assets", "spinner.gif"))
        self.audio_spinner_movie.setScaledSize(QSize(20, 20))
        self.audio_spinner_label.setMovie(self.audio_spinner_movie)
        self.audio_spinner_label.hide()
        header_layout.addWidget(self.audio_spinner_label)

        # Add header layout to right column
        right_column.addLayout(header_layout)
        
        # Create horizontal layout for translation and image
        translation_image_layout = QHBoxLayout()
        
        # Add translation display
        self.translation_display = QTextEdit()
        self.translation_display.setReadOnly(True)
        self.translation_display.setFixedHeight(210)
        translation_image_layout.addWidget(self.translation_display)

        # Create vertical layout for image and its spinner with proper alignment
        image_container = QVBoxLayout()
        image_container.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Add image container to translation image layout
        translation_image_layout.addWidget(self.image_widget)
        right_column.addLayout(translation_image_layout)

        # Examples label
        example_label = QLabel("Examples:")
        right_column.addWidget(example_label)

        # Examples layout
        self.examples_layout = QVBoxLayout()
        
        # Initialize placeholder examples
        self.reset_example_placeholder()

        right_column.addLayout(self.examples_layout)

        # Add columns to main layout
        main_layout.addLayout(left_column, 1)
        main_layout.addLayout(right_column, 3)

        self.setLayout(main_layout)

        # Initialize word_profile
        self.word_profile = None

        # Add state tracking variables
        self.translation_ready = False
        self.audio_ready = False
        self.image_ready = False

        # Add OpenAI API Key Section
        api_section = QVBoxLayout()
        api_label = QLabel("OpenAI API Key (required for AI features):")
        
        # Create horizontal layout for API key input and save button
        api_input_layout = QHBoxLayout()
        
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Enter your OpenAI API key")
        
        # Load API key from anki config
        saved_api_key = self.anki_config.get('openai_api_key', '')
        if saved_api_key:
            self.api_input.setText(saved_api_key)
        
        # Create save button
        save_api_button = QPushButton("Save")
        save_api_button.clicked.connect(self.save_api_key)
        
        # Add widgets to horizontal layout
        api_input_layout.addWidget(self.api_input)
        api_input_layout.addWidget(save_api_button)
        
        # Add to API section
        api_section.addWidget(api_label)
        api_section.addLayout(api_input_layout)
        left_column.addLayout(api_section)

    def update_add_button_state(self):
        """
        Updates the state of the Add to Anki button based on generation status and checkbox states
        """
        can_add = self.translation_ready  # Base requirement: translation must be ready

        # Check audio status if audio generation is enabled
        if self.generate_audio_checkbox.isChecked():
            can_add = can_add and self.audio_ready

        # Check image status if image generation is enabled
        if self.generate_image_checkbox.isChecked():
            can_add = can_add and self.image_ready

        self.add_button.setEnabled(can_add)

    def generate_translation(self):
        """
        Initiates asynchronous word profile generation.
        """
        # Validate API key if premium features are selected
        api_key = self.api_input.text().strip()
        if not api_key:
            showInfo("Please enter your OpenAI API key to use the features")
            return
        
        # Save API key to anki config
        self.anki_config['openai_api_key'] = api_key
        save_config_anki(self.anki_config)
        
        # Reset states
        self.translation_ready = False
        self.audio_ready = False
        self.image_ready = False
        self.update_add_button_state()
        self.update_generate_button_state()

        word = self.word_input.text().strip()
        language_level = self.level_dropdown.currentText()
        if not word:
            showInfo("Please enter a word to translate")
            return

        # Show loading state
        self.generate_button.setEnabled(False)
        self.translation_display.clear()
        self.spinner_label.show()
        self.spinner_movie.start()

        # Hide the play button when generating new translation
        self.play_audio_button.hide()
        self.reset_image_placeholder()
        self.reset_example_placeholder()

        # Show audio loading state if audio generation is enabled
        if self.generate_audio_checkbox.isChecked():
            self.play_audio_button.show()
            self.play_audio_button.setEnabled(False)
            self.audio_spinner_label.show()
            self.audio_spinner_movie.start()

        # Show image loading state if image generation is enabled
        if self.generate_image_checkbox.isChecked():
            self.reset_image_placeholder()
            self.image_spinner_label.show()
            self.image_spinner_movie.start()

        # Create and start worker with generation preferences
        self.worker = TranslationWorker(
            word,
            self.language_dropdown.currentText(),
            language_level,
            generate_image=self.generate_image_checkbox.isChecked(),
            generate_audio=self.generate_audio_checkbox.isChecked()
        )
        self.worker.finished.connect(self.on_translation_complete)
        self.worker.error.connect(self.on_translation_error)
        self.worker.start()

    def on_translation_complete(self, word_profile):
        """
        Handles successful translation completion and initiates audio/image generation if requested.
        """
        # Store word profile and update translation state
        self.word_profile = word_profile
        self.translation_ready = True

        # Handle audio generation
        if not self.generate_audio_checkbox.isChecked():
            self.audio_ready = True
        else:
            self.generate_audio()

        # Handle image generation
        if not self.generate_image_checkbox.isChecked():
            self.image_ready = True
        else:
            self.generate_image()

        # Display word profile
        self.display_word_profile(word_profile)

        # Enable generate button and hide the spinner
        self.spinner_label.hide()
        self.spinner_movie.stop()

        # Update add button state
        self.update_add_button_state()
        self.update_generate_button_state()

    def generate_audio(self):
        """
        Initiates audio generation process.
        """
        try:
            self.audio_ready = False
            self.audio_spinner_label.show()
            self.audio_spinner_movie.start()
            
            self.tts_worker = TTSWorker(self.word_profile)
            self.tts_worker.finished.connect(self.on_audio_complete)
            self.tts_worker.error.connect(self.on_audio_error)
            self.tts_worker.start()
        except Exception as e:
            showInfo(f"Audio generation failed: {str(e)}")
            self.word_profile['audio_filename'] = None
            self.audio_ready = True
            self.update_add_button_state()

    def on_audio_complete(self, audio_paths):
        """
        Handles successful audio generation.
        """
        if isinstance(audio_paths, dict):
            self.word_profile.update(audio_paths)
            self.audio_ready = True
            self.update_add_button_state()

            # Update UI for main word audio
            if 'audio_filename' in audio_paths:
                self.play_audio_button.setEnabled(True)
                self.audio_spinner_label.hide()
                self.audio_spinner_movie.stop()

            # Update example audio buttons
            for i in range(self.examples_layout.count()):
                layout_item = self.examples_layout.itemAt(i)
                if layout_item and layout_item.layout():
                    example_layout = layout_item.layout()
                    play_button = example_layout.itemAt(1).widget()
                    spinner_label = example_layout.itemAt(2).widget()
                    
                    example_key = f"example_{i+1}_audio_filename"
                    if example_key in audio_paths:
                        play_button.setEnabled(True)
                        spinner_label.hide()

            if self.anki_config.get("show_notifications", False):
                showInfo("Audio generated successfully")
        else:
            showInfo("Error: Invalid audio paths format received")
            self.audio_spinner_label.hide()
            self.audio_spinner_movie.stop()
        self.update_generate_button_state()

    def on_audio_error(self, error_message):
        """
        Handles errors during audio generation.
        """
        showInfo(f"Audio generation failed: {error_message}")
        self.word_profile['audio_filename'] = None
        self.audio_ready = True
        self.update_add_button_state()
        self.play_audio_button.hide()

    def play_audio(self):
        """
        Plays the generated audio file for the main word.
        """
        if self.word_profile and self.word_profile.get('audio_filename'):
            # Construct full path by joining addon folder path with relative path
            audio_path = os.path.join(mw.addonManager.addonsFolder(), self.word_profile['audio_filename'])
            if os.path.exists(audio_path):
                av_player.play_file(audio_path)
            else:
                showInfo(f"Audio file not found at: {audio_path}")
                self.play_audio_button.hide()

    def play_example_audio(self, index):
        """
        Plays the audio for the specified example index.
        """
        example_key = f"example_{index+1}_audio_filename"
        if self.word_profile and self.word_profile.get(example_key):
            # Construct full path by joining addon folder path with relative path
            audio_path = os.path.join(mw.addonManager.addonsFolder(), self.word_profile[example_key])
            if os.path.exists(audio_path):
                av_player.play_file(audio_path)
            else:
                showInfo(f"Audio file not found at: {audio_path}")

    def display_word_profile(self, word_profile):
        """
        Displays the word profile information in the UI.
        """
        # Extract word profile information
        Wort_DE = word_profile['german_word']
        Wort_SL = word_profile['source_language_translation']
        Wortarten = word_profile['classification']

        # Extract grammar information
        additional_info = word_profile.get('additional_grammatical_info', {})
        noun_info = additional_info.get('noun', {})
        verb_info = additional_info.get('verb', {})

        # Build translation and grammar HTML content
        translation_html = f"""
        <p><b>German Word:</b> {Wort_DE}</p>
        <p><b>Translation:</b> {Wort_SL}</p>
        <p><b>Classification:</b> {Wortarten}</p>
        """

        # Add grammar information if available
        if noun_info.get('article'):
            translation_html += f"<p><b>Article:</b> {noun_info['article']}</p>"
        if noun_info.get('plural_form'):
            translation_html += f"<p><b>Plural:</b> {noun_info['plural_form']}</p>"
        if verb_info.get('praesens'):
            translation_html += f"<p><b>Präsens:</b> {', '.join(verb_info['praesens'])}</p>"
        if verb_info.get('praeteritum'):
            translation_html += f"<p><b>Präteritum:</b> {', '.join(verb_info['praeteritum'])}</p>"
        if verb_info.get('perfekt'):
            translation_html += f"<p><b>Perfekt:</b> {', '.join(verb_info['perfekt'])}</p>"

        self.translation_display.setHtml(translation_html)

        # Display Image
        if 'image_path' in word_profile and word_profile['image_path']:
            pixmap = QPixmap(word_profile['image_path'])
            self.image_label.setPixmap(pixmap.scaledToWidth(200))  # Adjust size as needed
            self.image_label.show()
        else:
            self.reset_image_placeholder()

        # Clear previous examples
        for i in reversed(range(self.examples_layout.count())):
            item = self.examples_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

        # Display Examples with Play Buttons and Spinners
        examples = word_profile.get('examples', [])
        for i, ex in enumerate(examples):
            example_layout = QHBoxLayout()

            # Create QTextEdit for example text
            example_text = QTextEdit()
            example_text.setReadOnly(True)
            example_text.setMaximumHeight(80)
            
            # Format example text
            example_html = f"""
            {i+1}. {ex.get('german_example', '---')}
            <br>
            {ex.get('source_example_translation', '---')}
            """
            example_text.setHtml(example_html)

            # Play Button
            play_button = QPushButton("Play Audio")
            play_button.setEnabled(False)  # Initially disabled
            play_button.setVisible(self.generate_audio_checkbox.isChecked())
            play_button.clicked.connect(lambda _, idx=i: self.play_example_audio(idx))

            # Add spinner for example audio
            spinner_label = QLabel()
            spinner_movie = QMovie(os.path.join(os.path.dirname(__file__), "assets", "spinner.gif"))
            spinner_movie.setScaledSize(QSize(20, 20))
            spinner_label.setMovie(spinner_movie)
            if self.generate_audio_checkbox.isChecked():
                spinner_label.show()
                spinner_movie.start()
            else:
                spinner_label.hide()

            # Add to Example Layout
            example_layout.addWidget(example_text)
            example_layout.addWidget(play_button)
            example_layout.addWidget(spinner_label)

            # Add Example Layout to Examples Layout
            self.examples_layout.addLayout(example_layout)

    def clear_layout(self, layout):
        """
        Recursively clear a layout.
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def on_translation_error(self, error_message):
        """
        Handles errors during the translation process.
        
        Args:
            error_message (str): Description of the error that occurred
        
        Actions:
        - Displays error message to user
        - Resets UI to enable new attempts
        - Stops loading indicators
        - Re-enables generation button
        """
        showInfo(f"Translation error: {error_message}")
        self.generate_button.setEnabled(True)
        self.spinner_label.hide()
        self.spinner_movie.stop()

    def add_word(self):
        """
        Creates a new Anki note from the generated word profile.
        
        Workflow:
        1. Validates existence of word profile
        2. Retrieves selected deck information
        3. Creates note using add_note_to_deck utility
        4. Provides user feedback based on configuration
        5. Closes dialog on successful addition
        
        Note: Requires prior generation of word profile through generate_translation()
        """
        selected_deck_name = self.deck_dropdown.currentText()
        selected_deck_id = self.decks[selected_deck_name]

        if not self.word_profile:
            showInfo("Please generate a translation first.")
            return

        success = add_note_to_deck(
            self.word_profile,
            selected_deck_id,
            self.anki_config.get("show_notifications", False)
        )

        if success:
            if self.anki_config.get("show_notifications", False):
                showInfo(f"Added word '{self.word_profile['original_word']}' to deck '{selected_deck_name}'.")
            # Reset the form for the next word
            self.word_input.clear()
            self.translation_display.clear()
            self.reset_image_placeholder()
            self.reset_example_placeholder()
            self.word_profile = None
            self.translation_ready = False
            self.audio_ready = False
            self.image_ready = False
            self.update_add_button_state()
            self.update_generate_button_state()

    def on_audio_checkbox_changed(self, state):
        """
        Checkbox state changes only affect future generations, not current content
        """
        # Only update the add button state if we have a word profile
        if self.word_profile:
            self.update_add_button_state()

    def generate_image(self):
        """
        Initiates image generation process.
        """
        try:
            self.image_ready = False
            self.image_spinner_label.show()
            self.image_spinner_movie.start()
            
            self.image_worker = ImageWorker(self.word_profile)
            self.image_worker.finished.connect(self.on_image_complete)
            self.image_worker.error.connect(self.on_image_error)
            self.image_worker.start()
        except Exception as e:
            showInfo(f"Image generation failed: {str(e)}")
            self.word_profile['image_path'] = None
            self.image_ready = True
            self.update_add_button_state()

    def on_image_complete(self, image_path):
        """
        Handles successful image generation.
        """
        self.word_profile['image_path'] = image_path
        self.image_ready = True
        self.image_spinner_label.hide()
        self.image_spinner_movie.stop()

        if image_path:
            # For Anki media files, just use the filename
            pixmap = QPixmap(os.path.join(mw.addonManager.addonsFolder(), image_path))
            self.image_label.setPixmap(pixmap.scaledToWidth(200))
            self.image_label.show()

        self.update_add_button_state()
        
        if self.anki_config.get("show_notifications", False):
            showInfo("Image generated successfully")
        self.update_generate_button_state()

    def reset_image_placeholder(self):
        """
        Reset the image label to show the placeholder styling
        """
        self.image_label.setPixmap(QPixmap())  # Clear any existing image
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #CCCCCC;
                background-color: #F5F5F5;
                border-radius: 4px;
            }
        """)

    def on_image_error(self, error_message):
        """
        Handles errors during image generation.
        """
        showInfo(f"Image generation failed: {error_message}")
        self.word_profile['image_path'] = None
        self.image_ready = True
        self.image_spinner_label.hide()
        self.image_spinner_movie.stop()
        self.reset_image_placeholder()
        self.update_add_button_state()

    def update_generate_button_state(self):
        """
        Updates the state of the Generate button based on generation status
        """
        # Enable generate button only when all requested content is ready
        can_generate = True
        
        # Check if translation is still processing
        if not self.translation_ready and self.spinner_label.isVisible():
            can_generate = False
        
        # Check audio status if audio generation is enabled
        if self.generate_audio_checkbox.isChecked() and not self.audio_ready and self.audio_spinner_label.isVisible():
            can_generate = False
        
        # Check image status if image generation is enabled
        if self.generate_image_checkbox.isChecked() and not self.image_ready and self.image_spinner_label.isVisible():
            can_generate = False
        
        self.generate_button.setEnabled(can_generate)
        
    def reset_example_placeholder(self):
        """
        Reset the examples section to show placeholder content
        """
        # Clear existing examples
        for i in reversed(range(self.examples_layout.count())):
            item = self.examples_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

        # Add placeholder examples
        for i in range(3):
            example_layout = QHBoxLayout()

            # Create QTextEdit for example text
            example_text = QTextEdit()
            example_text.setReadOnly(True)
            example_text.setMaximumHeight(80)
            
            # Set empty initial text
            example_html = f"""
            {i+1}. ---
            <br>
            ---
            """
            example_text.setHtml(example_html)

            # Play Button (initially hidden)
            play_button = QPushButton("Play Audio")
            play_button.hide()
            play_button.clicked.connect(lambda _, idx=i: self.play_example_audio(idx))

            # Add to Example Layout
            example_layout.addWidget(example_text)
            example_layout.addWidget(play_button)

            # Add Example Layout to Examples Layout
            self.examples_layout.addLayout(example_layout)

    def save_api_key(self):
        """
        Saves the OpenAI API key to the Anki config and shows confirmation.
        """
        api_key = self.api_input.text().strip()
        if api_key:
            self.anki_config['openai_api_key'] = api_key
            save_config_anki(self.anki_config)
            if self.anki_config.get("show_notifications", False):
                showInfo("API key saved successfully")
        else:
            showInfo("Please enter an OpenAI API key")

def show_add_word_dialog():
    """
    Creates and displays the word addition dialog.
    
    Creates a modal dialog instance that blocks interaction with the main
    Anki window until the dialog is closed. This ensures proper handling
    of the word addition workflow.
    """
    dialog = AddWordDialog(mw)
    dialog.exec()

# Initialize the menu and functionality
setup_menu()