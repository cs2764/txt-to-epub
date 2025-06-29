#!/bin/bash

echo "================================"
echo "TXT to EPUB Converter - Unix"
echo "================================"
echo

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed or not in PATH!"
    echo "Please install Anaconda or Miniconda first:"
    echo "https://www.anaconda.com/products/distribution"
    echo "https://docs.conda.io/en/latest/miniconda.html"
    echo
    echo "For quick installation on Linux/macOS:"
    echo "wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "bash Miniconda3-latest-Linux-x86_64.sh"
    exit 1
fi

print_success "[1/4] Checking conda installation... OK"
echo

# Initialize conda for this shell session
eval "$(conda shell.bash hook)"

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

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies!"
    exit 1
fi
print_success "Dependencies installed successfully!"
echo

# Run the application
echo "[4/4] Starting TXT to EPUB Converter..."
echo
print_warning "The application will open in your default web browser."
echo "Local access: http://localhost:7860"
echo "Network access: http://0.0.0.0:7860"
print_warning "Press Ctrl+C to stop the application."
echo

python webui.py

# Check if application started successfully
if [ $? -ne 0 ]; then
    print_error "Application failed to start!"
    exit 1
fi 