

### **Bundle All Dependencies Automatically**
If you want to bundle multiple dependencies (like `openai`, `typing_extensions`, etc.) at once:

1. Use Poetry to export all installed libraries:
   ```bash
   poetry export -f requirements.txt --without-hashes -o requirements.txt
   ```

2. Use `pip` to install these into your `libs` folder:
   ```bash
   pip install -r requirements.txt --target ./src/intelli_deck_addon/libs
   ```

This will install all dependencies (including transitive ones) into the `libs` directory, ensuring everything is available in Anki.


### **Set Python Version Correctly**
To set the Python version correctly, run the following command:

```bash
pyenv local 3.9.15 && poetry env use 3.9.15 && python --version
```

### **Make sure the link is setup**

```bash
./setup_symlink.sh
```

### **Create Release Package**
To create the zip file for publishing to AnkiWeb:

```bash
cd src/intelli_deck_addon && find . -name "__pycache__" -type d -exec rm -r {} + && find . -name ".DS_Store" -type f -delete && zip -r ../../intelli_deck_addon.ankiaddon * -x "*.pyc" "*.pyo" "*.pyd" "*__pycache__*" "*.DS_Store"
```
