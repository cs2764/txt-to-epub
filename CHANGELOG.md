# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-01-26

### Fixed
- **Critical Bug Fix** 🐛 Fixed gradio compatibility issue causing TypeError in chapter detection
- **Gradio Version**: Downgraded from 4.25.0 to 4.20.0 for enhanced stability
- **Preview Functionality**: Resolved "argument of type 'bool' is not iterable" error
- **ASGI Exceptions**: Fixed application crashes during chapter preview operations
- **Auto-Compatibility**: Automatically installs compatible gradio-client 0.11.0

### Changed
- Updated requirements.txt with stable gradio versions
- Improved error handling in chapter detection workflow

---

## [0.1.0] - 2025-01-26

### Added
- **Initial Release** 🎉
- Intelligent chapter detection using heuristic-based engine
- Batch processing for multiple TXT files
- Bilingual user interface (English/Chinese)
- Text cleaning options (merge empty lines, remove extra spaces)
- Custom regex pattern support for chapter detection
- Chapter preview functionality
- Metadata support (author, cover image)
- Flexible output options:
  - Save to default `epub_output` folder
  - Save to custom directory
  - Save to source file location with automatic fallback
- Web-based interface using Gradio
- Cross-platform support (Windows, macOS, Linux)

### Features
- **Smart Chapter Detection**: Automatically identifies chapter headings in both Chinese and English
- **Preview Functionality**: Preview detected chapters before conversion
- **Network Drive Support**: Intelligent handling of network drives and permission issues
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **AI-Generated**: Developed using AI-powered tools (gemini_cli + Cursor)

### Deployment
- **Automated Installation Scripts**:
  - `run_windows.bat` - Windows double-click installer
  - `run_macos.sh` - macOS optimized installer (Intel & Apple Silicon)
  - `run_unix.sh` - Universal Linux/Unix installer
- **Environment Cleanup Scripts**:
  - `cleanup_windows.bat`
  - `cleanup_macos.sh` 
  - `cleanup_unix.sh`
- **Conda Environment Management**: Automated virtual environment creation and management
- **Fixed Dependencies**: Locked versions to ensure stability

### Technical Details
- Python 3.10 support
- Gradio 4.25.0 (stable version)
- EbookLib for EPUB generation
- Cross-platform file handling
- Unicode text processing with error tolerance

### Dependencies
- gradio==4.25.0
- ebooklib==0.18
- numpy==1.24.3
- tqdm==4.66.1

---

**Note**: This project was created entirely through AI-powered development using `gemini_cli` and `Cursor`, demonstrating the potential of AI-assisted software development. 