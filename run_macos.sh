#!/bin/bash

echo "================================"
echo "TXT to EPUB Converter - macOS"
echo "================================"
echo

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_warning "This script is optimized for macOS. Use run_unix.sh for other Unix systems."
fi

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed or not in PATH!"
    echo
    print_info "To install Miniconda on macOS:"
    echo "1. Intel Macs:"
    echo "   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
    echo "   bash Miniconda3-latest-MacOSX-x86_64.sh"
    echo
    echo "2. Apple Silicon Macs (M1/M2):"
    echo "   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    echo "   bash Miniconda3-latest-MacOSX-arm64.sh"
    echo
    echo "3. Or install via Homebrew:"
    echo "   brew install miniconda"
    echo
    echo "After installation, restart your terminal and run this script again."
    exit 1
fi

print_success "[1/4] Checking conda installation... OK"

# Check for Apple Silicon and print info
if [[ $(uname -m) == 'arm64' ]]; then
    print_info "Detected Apple Silicon Mac (M1/M2)"
else
    print_info "Detected Intel Mac"
fi
echo

# Initialize conda for this shell session
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    eval "$(conda shell.bash hook)"
fi

# Check if environment exists
if conda env list | grep -q "txt-to-epub"; then
    print_success "[2/4] Conda environment already exists... OK"
    echo "Activating existing environment..."
    conda activate txt-to-epub
    if [ $? -ne 0 ]; then
        print_error "Failed to activate existing environment!"
        exit 1
    fi
else
    echo "[2/4] Creating conda environment..."
    conda create -n txt-to-epub python=3.10 -y
    if [ $? -ne 0 ]; then
        print_error "Failed to create conda environment!"
        exit 1
    fi
    print_success "Environment created successfully!"
    echo "Activating new environment..."
    conda activate txt-to-epub
    if [ $? -ne 0 ]; then
        print_error "Failed to activate newly created environment!"
        exit 1
    fi
fi
echo

# Install dependencies
echo "[3/4] Installing dependencies..."

# macOS specific: Check for Xcode Command Line Tools for some packages
if ! xcode-select -p &> /dev/null; then
    print_warning "Xcode Command Line Tools not found. Some packages might need them."
    print_info "Install with: xcode-select --install"
fi

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies!"
    print_info "If you encounter issues on Apple Silicon, try:"
    print_info "export ARCHFLAGS='-arch arm64' && pip install -r requirements.txt"
    exit 1
fi
print_success "Dependencies installed successfully!"
echo

# Run the application
echo "[4/4] Starting TXT to EPUB Converter..."
echo
print_warning "The application will open in your default web browser."
print_warning "Press Ctrl+C to stop the application."
echo

# macOS specific: Check if port 7860 is available
if lsof -i :7860 &> /dev/null; then
    print_warning "Port 7860 is already in use. The application will try to use another port."
fi

python webui.py

# Check if application started successfully
if [ $? -ne 0 ]; then
    print_error "Application failed to start!"
    print_info "Common solutions:"
    print_info "1. Make sure no other Gradio apps are running"
    print_info "2. Check if all dependencies installed correctly"
    print_info "3. Try running: conda activate txt-to-epub && python webui.py"
    exit 1
fi 