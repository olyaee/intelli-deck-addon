# Development Setup

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
Create a symlink for development:
```bash
./setup_symlink.sh
```

### **Create Release Package**
To create the distribution package for AnkiWeb:
```bash
cd src/intelli_deck_addon && \
find . -name "__pycache__" -type d -exec rm -r {} + && \
find . -name ".DS_Store" -type f -delete && \
zip -r ../../intelli_deck_addon.ankiaddon * \
    -x "*.pyc" "*.pyo" "*.pyd" "*__pycache__*" "*.DS_Store"
```
