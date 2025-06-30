# TXT to EPUB Converter

> **Language / 语言:** [English](#txt-to-epub-converter) | [中文说明](#txt-转-epub-转换器)
> 
> **Project Repository / 项目地址:** [https://github.com/cs2764/txt-to-epub](https://github.com/cs2764/txt-to-epub)

## 📋 Quick Navigation / 快速导航

### English Documentation
- [🚀 Quick Start](#quick-start-recommended) - Get up and running in minutes
- [📖 Features](#features) - What this tool can do
- [🛠️ Manual Installation](#manual-installation) - Step-by-step setup
- [❓ Troubleshooting](#troubleshooting) - Common issues and solutions

### 中文文档  
- [🚀 快速开始](#快速开始推荐) - 几分钟内启动运行
- [📖 功能特性](#功能特性) - 工具功能介绍
- [🛠️ 手动安装](#手动安装) - 详细安装步骤
- [❓ 故障排除](#故障排除) - 常见问题解决方案

---

This is a powerful and intelligent tool for converting plain text (`.txt`) files into EPUB format. The application is built with Gradio, providing a user-friendly web interface for batch processing, text cleaning, and advanced chapter detection.

## Features

*   **Intelligent Chapter Detection:** Automatically analyzes the text to identify chapter headings using a sophisticated, heuristic-based engine. It is specifically optimized for both English and Chinese literary conventions.
*   **Batch Processing:** Convert multiple `.txt` files to EPUB in a single operation.
*   **Text Cleaning:** Optional tools to merge empty lines and remove extra whitespace for a cleaner output.
*   **Customizable Chapter Rules:** For advanced users, the option to provide a custom regex pattern to define chapter breaks.
*   **Chapter Preview:** Before converting, you can preview the chapters that the detection engine has found to ensure accuracy.
*   **Metadata Support:** Add author information and a cover image to your generated EPUB files.
*   **Flexible Output:** Save converted files to a default `epub_output` folder, specify a custom directory, or save directly to the source file location with automatic fallback for network drives and protected directories.
*   **Smart Port Management:** Automatic port detection and fallback (7860-7869) for seamless startup even when ports are busy.
*   **Web Interface:** Easy-to-use interface that runs locally and can be accessed from other devices on your network.

## How to Use

### Quick Start (Recommended)

Use the provided automated scripts for your platform:

**Installation & Launch:**
*   **Windows:** Double-click `run_windows.bat`
*   **macOS:** Run `./run_macos.sh` in terminal (optimized for both Intel and Apple Silicon)
*   **Linux:** Run `./run_unix.sh` in terminal

**Environment Cleanup:**
*   **Windows:** Double-click `cleanup_windows.bat`
*   **macOS:** Run `./cleanup_macos.sh` in terminal
*   **Linux:** Run `./cleanup_unix.sh` in terminal

These scripts will automatically:
- **Installation:** Check for conda installation, create virtual environment, install dependencies, launch application
- **Cleanup:** Safely remove the virtual environment when you're done with the project

### Manual Installation

1.  **Prerequisites:**
    *   Install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
    *   Clone this repository to your local machine

2.  **Environment Setup:**
    ```bash
    # Create conda environment
    conda create -n txt-to-epub python=3.10 -y
    
    # Activate environment
    conda activate txt-to-epub
    
    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Running the Application:**
    ```bash
    # Make sure conda environment is activated
    conda activate txt-to-epub
    
    # Run the application
    python webui.py
    ```
    *   The application will automatically open in your default web browser.

### Deployment Notes

*   The application runs on `0.0.0.0:7860` by default and is accessible from other devices on your network
*   For production deployment, consider using reverse proxy (nginx) and process managers
*   The conda environment ensures consistent dependencies across different systems

### Troubleshooting

**Common Issues:**

1. **"Failed to create conda environment" on first run**
   - This is now fixed in the latest version
   - If you encounter this, simply run the script again
   - The environment creation and activation logic has been improved

2. **Port 7860 already in use (Auto-Fixed in v0.1.3+)**
   - ✅ **Automatic Detection**: The application now automatically detects port conflicts
   - ✅ **Smart Fallback**: Automatically tries ports 7861-7869 if 7860 is busy
   - ✅ **Clear Messages**: Shows which port is being used with full access URLs
   - 🔧 **Manual Override**: You can also specify a custom port with environment variable `GRADIO_SERVER_PORT`
   - 💡 **Still Having Issues?**: Close other Gradio applications or restart your computer

3. **Permission errors on network drives**
   - Use the "Save to Source File Location" option with caution
   - The application will automatically fallback to default output directory

4. **Application won't start - All ports busy**
   - The application tries ports 7860-7869 automatically
   - Close applications using these ports (check with `netstat -an | findstr 786` on Windows)
   - Alternative: Set `GRADIO_SERVER_PORT=8080` environment variable for a different port
   - Restart your computer if needed to free up ports

3.  **Using the Interface:**
    *   **Upload Files:** Drag and drop your `.txt` files into the upload area.
    *   **Configure Options:**
        *   Select any text cleaning options you need.
        *   Choose between "Intelligent Detection" (recommended) or "Custom Regex" for chapter splitting.
        *   Optionally, add an author and a cover image.
        *   Specify an output folder if you don't want to use the default.
    *   **Convert:** Click the "Start Conversion" button to begin the process.
    *   **View Results:** The results table will show the status of each conversion, and the log will provide detailed information.

## Version

*   Current Version: 0.1.3

---

# TXT 转 EPUB 转换器

> **Language / 语言:** [English](#txt-to-epub-converter) | [中文说明](#txt-转-epub-转换器)
> 
> **Project Repository / 项目地址:** [https://github.com/cs2764/txt-to-epub](https://github.com/cs2764/txt-to-epub)

这是一个功能强大且智能的工具，用于将纯文本（`.txt`）文件转换为 EPUB 格式。该应用程序基于 Gradio 构建，提供了一个用户友好的 Web 界面，支持批量处理、文本清理和先进的章节检测。

## 功能特性

*   **智能章节检测：** 通过先进的、基于启发式规则的引擎自动分析文本，以识别章节标题。该功能针对中英文文学惯例进行了特别优化。
## AI-Generated Project

This project was created entirely through AI-powered development using `gemini_cli` and `Cursor`. The combination of these two AI coding tools enabled rapid development through iterative feedback and refinement to build the application from scratch, including its core logic, user interface, and features. The project demonstrates the potential of AI-assisted software development in creating fully functional applications.

---
*   **批量处理：** 在单次操作中转换多个 `.txt` 文件为 EPUB。
*   **文本清理：**提供可选工具，用于合并多余空行和移除额外空白，以获得更整洁的输出。
*   **自定义章节规则：** 高级用户可以提供自定义的正则表达式来定义章节分割点。
*   **章节预览：** 在转换之前，您可以预览检测引擎找到的章节，以确保准确性。
*   **元数据支持：** 为您生成的 EPUB 文件添加作者信息和封面图片。
*   **灵活的输出位置：** 将转换后的文件保存到默认的 `epub_output` 文件夹、指定自定义目录，或直接保存到源文件位置（对网络驱动器和受保护目录自动降级处理）。
*   **Web 界面：** 易于使用的界面，可在本地运行，并可从您网络中的其他设备访问。

## 如何使用

### 快速开始（推荐）

使用为您的平台提供的自动化脚本：

**安装与启动：**
*   **Windows：** 双击 `run_windows.bat`
*   **macOS：** 在终端中运行 `./run_macos.sh`（针对Intel和Apple Silicon优化）
*   **Linux：** 在终端中运行 `./run_unix.sh`

**环境清理：**
*   **Windows：** 双击 `cleanup_windows.bat`
*   **macOS：** 在终端中运行 `./cleanup_macos.sh`
*   **Linux：** 在终端中运行 `./cleanup_unix.sh`

这些脚本将自动：
- **安装脚本：** 检查conda安装、创建虚拟环境、安装依赖、启动应用程序
- **清理脚本：** 在项目使用完成后安全删除虚拟环境

### 手动安装

1.  **环境要求：**
    *   安装 [Anaconda](https://www.anaconda.com/products/distribution) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
    *   将此代码仓库克隆到您的本地计算机

2.  **环境配置：**
    ```bash
    # 创建 conda 环境
    conda create -n txt-to-epub python=3.10 -y
    
    # 激活环境
    conda activate txt-to-epub
    
    # 安装依赖
    pip install -r requirements.txt
    ```

3.  **运行程序：**
    ```bash
    # 确保 conda 环境已激活
    conda activate txt-to-epub
    
    # 运行应用程序
    python webui.py
    ```
    *   程序将自动在您的默认网络浏览器中打开。

### 部署说明

*   应用程序默认运行在 `0.0.0.0:7860`，可从网络中的其他设备访问
*   生产环境部署建议使用反向代理（nginx）和进程管理器
*   conda 环境确保在不同系统间依赖的一致性

### 故障排除

**常见问题：**

1. **首次运行时"创建conda环境失败"**
   - 最新版本已修复此问题
   - 如果遇到此问题，请重新运行脚本
   - 环境创建和激活逻辑已改进

2. **端口7860已被占用**
   - 关闭其他Gradio应用程序或重启计算机
   - 应用程序会自动尝试其他端口

3. **网络驱动器权限错误**
   - 谨慎使用"保存到源文件位置"选项
   - 应用程序会自动降级到默认输出目录

3.  **使用界面：**
    *   **上传文件：** 将您的 `.txt` 文件拖放到上传区域。
    *   **配置选项：**
        *   选择您需要的文本清理选项。
        *   在“智能检测”（推荐）或“自定义正则表达式”之间选择章节分割模式。
        *   （可选）添加作者和封面图片。
        *   如果您不想使用默认文件夹，请指定一个输出文件夹。
    *   **转换：** 点击“开始转换”按钮以启动该过程。
    *   **查看结果：** 结果表将显示每次转换的状态，日志将提供详细信息。

## 自动化脚本说明

本项目提供了完整的自动化脚本套件，包含安装和清理功能：

### 安装脚本

#### `run_windows.bat` (Windows)
- **使用方法：** 双击文件即可运行
- **功能：** 自动检测conda、创建环境、安装依赖
- **特点：** 包含详细的错误处理和用户提示

#### `run_macos.sh` (macOS)
- **使用方法：** `chmod +x run_macos.sh && ./run_macos.sh`
- **功能：** 针对macOS优化，支持Intel和Apple Silicon
- **特点：** 
  - 自动检测处理器架构
  - 检查Xcode Command Line Tools
  - 端口冲突检测
  - 彩色输出和详细提示

#### `run_unix.sh` (Linux/Unix)
- **使用方法：** `chmod +x run_unix.sh && ./run_unix.sh`
- **功能：** 通用Unix系统支持
- **特点：** 兼容性好，适用于各种Linux发行版

### 清理脚本

#### `cleanup_windows.bat` (Windows)
- **使用方法：** 双击文件即可运行
- **功能：** 安全删除conda虚拟环境
- **特点：** 
  - 检查环境是否存在
  - 用户确认提示
  - 详细的清理状态反馈

#### `cleanup_macos.sh` (macOS)
- **使用方法：** `chmod +x cleanup_macos.sh && ./cleanup_macos.sh`
- **功能：** macOS优化的环境清理
- **特点：** 
  - 显示环境磁盘占用
  - 自动处理活跃环境
  - 可选清理缓存文件
  - 架构检测和优化建议

#### `cleanup_unix.sh` (Linux/Unix)
- **使用方法：** `chmod +x cleanup_unix.sh && ./cleanup_unix.sh`
- **功能：** 通用Unix系统环境清理
- **特点：** 彩色输出、确认提示、错误处理

## 版本

*   当前版本：0.1.2
