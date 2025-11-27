<div style="text-align: center; margin-bottom: 20px;">
  <a href="README.md" style="padding: 8px 16px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin-right: 20px;">English</a> |
  <a href="README.zh.md" style="padding: 8px 16px; background-color: #f1f1f1; color: #333; text-decoration: none; border-radius: 4px;">中文</a>
</div>

# EasyBookmark

<div align="center">
  <img src="assets/logo.svg" alt="EasyBookmark Logo" width="200" height="200">
</div>

How to add bookmarks to PDFs using AI?

A powerful and user-friendly PDF processing tool that provides table of contents extraction and bookmarking features to help you handle PDF documents more efficiently.

## Features

- **PDF Table of Contents Extraction**: Automatically or manually extract the table of contents structure from PDF documents
- **Intelligent Content Analysis**: Use LLM (Large Language Model) technology to analyze PDF content and extract key information
- **User-Friendly Interface**: Intuitive graphical interface
- **Configuration Management**: Flexible configuration options to meet different user needs

## Installation Methods

### Method 1: Using Precompiled Executable

1. Download the installation package suitable for your operating system from the [releases page](https://github.com/JackLee404/EasyBookmark/releases)
2. Windows users: Run the `.exe` file to install
3. Mac users: Drag the `.app` file to the Applications folder

### Method 2: Install from Source Code

1. Clone or download this repository
   ```bash
   git clone https://github.com/JackLee404/EasyBookmark.git
   cd EasyBookmark
   ```

2. Create a virtual environment (recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application
   ```bash
   python src/main.py
   ```

## Usage Instructions

### 1. Launch the Application

Windows users: Double-click the EasyBookmark shortcut on the desktop or launch from the Start menu

Mac users: Launch EasyBookmark from the Applications folder

### 2. Open a PDF File

- Click "File" > "Open", or use the shortcut `Ctrl+O` (Windows)/`Cmd+O` (Mac)
- Browse and select the PDF file you want to process
- Enter LLM API parameters (optional):
  - API Base URL
  - API Key
  - Model name (e.g., `gpt-4o-mini`)

### 3. Extract Table of Contents

#### Method 1: AI Automatic Extraction
- After opening a PDF file, click "Tools" > "Extract Table of Contents" > "AI Automatic Extraction"
- Set the page range where the table of contents is located
- Click the "Start Extraction" button, and the program will use AI to extract the table of contents from the PDF
- After extraction is complete, you can view the results in the preview area below

#### Method 2: Import JSON Format Table of Contents

If you don't have an LLM API, you can also copy the table of contents text (if available) and send the text to an LLM along with the required JSON format

```
PROMPT:
You are a professional PDF table of contents extraction assistant. Please extract table of contents information from the provided text and PDF page images, and output in the specified format.
                
                Extraction rules:
                1. Combine text content and page images to identify the title, page number, and hierarchical relationship of each table of contents item
                2. Ignore irrelevant information such as headers, footers, and page numbers
                3. Correctly determine the level of each table of contents item (usually determined by indentation or number format)
                4. For items without clear page numbers, try to infer or mark as -1
                
                The output format must be a JSON array, each item containing three fields:
                - title: Table of contents item title
                - page: Page number (integer)
                - level: Level (starting from 1)
                
                Example output:
                [{"title": "Chapter 1 Introduction", "page": 1, "level": 1}, {"title": "1.1 Background", "page": 2, "level": 2}]
                
                Important: Please ensure the output is in pure JSON format without any additional text explanations.
                
                {Paste your copied table of contents text here}
```

- After opening a PDF file, click "Tools" > "Extract Table of Contents" > "Import JSON Table of Contents"
- Prepare a JSON format table of contents file (format reference: docs/toc_example.json)
- Select the JSON file, and the program will validate and display the imported table of contents

- Regardless of which method you use to extract the table of contents, you can:
  - Set the "Page Offset Value" to adjust the table of contents page numbers
  - Edit table of contents entries
  - Save the processed PDF file

### 4. Configuration Settings

- You can configure the following options:
  - Default save location
  - LLM settings (API key, etc.)
  - Interface language (if supported)

### Notes

- The model needs to support the OpenAI interface specification. The program will prioritize using multimodal methods for processing, otherwise it will attempt text extraction
- The accuracy of table of contents extraction depends on PDF quality and the standardization of the table of contents format
- The page offset value is used to adjust the actual page numbers of bookmarks. Positive numbers indicate backward offset, negative numbers indicate forward offset
- JSON table of contents files must follow the specified format, containing three fields: title, page, and level
- Imported table of contents page numbers are automatically validated to be within the valid range of the PDF
- Both multimodal and non-multimodal models are supported. Multimodal models will extract images, while non-multimodal models will extract text to send to the LLM

## Configuration File Description

The application uses a JSON format configuration file, which is stored in a file named `config.json` in the program's root directory the first time it is run

Main configuration items:

- `default_save_path`: Default save path
- `openai_api_key`: OpenAI API key (encrypted storage)
- `model_name`: Name of the LLM model used
- `api_base_url`: Base URL for the LLM API (e.g., `https://api.openai.com/v1`)

## Frequently Asked Questions

### 1. Unable to Extract PDF Table of Contents

- Ensure the PDF file is not a scanned document or encrypted file
- Try using the "Manual Extraction" feature
- Check if you have sufficient permissions to access the PDF file

### 2. Content Analysis Failed

- Ensure you have correctly configured an LLM API key that complies with the OpenAI interface specification
- Check if the network connection is normal, and if proxy is disabled
- Try reducing the range of pages to analyze

### 3. Application Crashes

- Ensure your system meets the requirements
- Update to the latest version of the application
- If the problem persists, please contact the email or submit issues

## Command Line Tools

EasyBookmark also provides command line tools for batch processing or automated operations:

```bash
# Extract PDF table of contents to JSON file
python -m src.cli --input document.pdf --output toc.json --action extract_toc

# Analyze PDF content
python -m src.cli --input document.pdf --output analysis.txt --action analyze --pages 1-10
```

## Development Guide

If you want to participate in development or customize features:

1. Follow the steps in the "Install from Source Code" section to set up the development environment
2. Code structure:
   - `src/`: Main source code directory
   - `tests/`: Test files
   - `assets/`: Icons and other resources

3. Run tests:
   ```bash
   python -m unittest discover -s tests
   ```

4. Run the application:
   ```bash
   # Run directly
   python main.py
   
   # Or run through the src directory
   python src/main.py
   ```

5. Package the application (if needed):
   ```bash
   python package_app.py
   ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

- Project Homepage: [https://github.com/JackLee404/EasyBookmark](https://github.com/JackLee404/EasyBookmark)
- Issues: [https://github.com/JackLee404/EasyBookmark/issues](https://github.com/JackLee404/EasyBookmark/issues)
- 📫: deepsea404@hotmail.com

## Acknowledgments

This project uses the following open source libraries:

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [pypdf](https://pypi.org/project/pypdf/) - PDF processing
- [LangChain](https://www.langchain.com/) - LLM application framework
- [OpenAI Python](https://github.com/openai/openai-python) - OpenAI API client

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=JackLee404/EasyBookmark&type=date&legend=top-left)](https://www.star-history.com/#JackLee404/EasyBookmark&type=date&legend=top-left)

## Changelog

### v1.0.0
- Initial version release
- Support for PDF table of contents extraction
- Support for content analysis functionality
- Provides graphical interface and command line interface