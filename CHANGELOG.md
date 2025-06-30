# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2025-01-27

### Added
- **📄 File Content Preview**: New feature to preview the first 10 lines of selected files
  - Shows file information (name, size, encoding, detection method)
  - Displays line numbers and handles empty lines
  - Provides encoding confidence warnings for better user guidance
- **🔍 Enhanced Encoding Detection**: Comprehensive multi-method encoding detection system
  - BOM (Byte Order Mark) detection for UTF variants
  - chardet library integration for automatic detection
  - Chinese character ratio analysis for better Asian text handling
  - Fallback mechanisms with multiple common encodings
  - Supports: UTF-8, GBK, GB2312, Big5, UTF-16, UTF-32, ASCII
- **📁 Improved File Selection System**: Individual file management instead of bulk selection
  - "Add File to List" functionality for one-by-one file addition
  - File list display with size information
  - "Clear All" button to remove all selected files
  - Duplicate file detection and prevention
  - Bilingual file management interface

### Fixed
- **🐛 Gradio Compatibility**: Resolved `AttributeError: 'State' object has no attribute 'change'`
  - Fixed compatibility issues with Gradio 3.50.2
  - Removed unsupported `file_list_state.change()` event handler
  - Modified functions to return preview content directly
- **📝 Syntax Errors**: Fixed Chinese quote character issues in UI_TEXT dictionary
  - Resolved string literal syntax errors in Chinese interface text
  - Improved text encoding handling throughout the application
- **🔧 UI Event Handling**: Enhanced event handler management for better user experience
  - Updated event outputs to include file preview updates
  - Improved state management for file selection workflow

### Enhanced
- **🌐 Bilingual Support**: Improved Chinese and English language switching
  - Better text encoding for Chinese characters in UI
  - Enhanced file preview display in both languages
  - Improved error messages and user guidance
- **📊 User Experience**: Better visual feedback and information display
  - Real-time file content preview when files are added
  - Detailed encoding information with confidence levels
  - Warning indicators for low-confidence encoding detection
  - Improved file list formatting with size information

### Technical
- **Encoding Detection Methods**: BOM detection → chardet → pattern matching → fallback
- **File Management**: Individual file selection with list-based state management
- **Error Handling**: Enhanced error recovery and user feedback systems
- **UI Responsiveness**: Improved component updates and state synchronization

---

## [0.1.2] - 2025-01-26

### Fixed
- **🌐 Connection Fix**: Resolved gradio.live public link issue causing "Connection errored out" errors
- **🔗 Local Server**: Changed from `share=True` to `share=False` for stable local connection
- **📚 Dependency Stability**: Downgraded to Gradio 3.50.2 with compatible dependency versions:
  - gradio==3.50.2 (stable release)
  - fastapi==0.104.1  
  - pydantic==2.4.2
  - starlette==0.27.0
  - uvicorn==0.24.0
- **🛠️ ASGI Errors**: Fixed PydanticSchemaGenerationError and FastAPI compatibility issues
- **📱 Progress API**: Removed incompatible `gr.Progress` for Gradio 3.x compatibility

### Added
- **📍 Address Display**: Clear local/network access URLs in startup scripts and application
- **🔗 GitHub Integration**: Added project repository links to WebUI interface (bilingual)
- **🧭 README Navigation**: Enhanced documentation with language switching and quick navigation
- **📋 User Guidance**: Improved startup messages with connection URLs

### Technical
- **Local Access**: `http://localhost:7860` (primary)
- **Network Access**: `http://0.0.0.0:7860` (same network devices)
- **Offline Mode**: No external dependencies for core functionality
- **Stable Stack**: Tested dependency combination for Windows/macOS/Linux

---

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