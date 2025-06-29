#!/bin/bash

echo "========================================"
echo "TXT to EPUB Converter - Environment cleanup"
echo "========================================"
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
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed or not in PATH!"
    echo "Cannot proceed with cleanup."
    echo
    exit 1
fi

print_success "[1/3] Checking conda installation... OK"
echo

# Initialize conda for this shell session
eval "$(conda shell.bash hook)"

# Check if environment exists
if ! conda env list | grep -q "txt-to-epub"; then
    echo "[2/3] Environment 'txt-to-epub' not found."
    echo "Nothing to clean up."
    echo
    exit 0
fi

print_success "[2/3] Found environment 'txt-to-epub'"
echo

# Show environment info
echo "Environment details:"
conda env list | grep "txt-to-epub"
echo

# Ask for confirmation
print_warning "This will permanently delete the 'txt-to-epub' conda environment!"
print_warning "This action cannot be undone."
echo

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled by user."
    echo
    exit 0
fi

echo
echo "[3/3] Removing conda environment..."

# Remove the environment
conda env remove -n txt-to-epub -y
if [ $? -ne 0 ]; then
    print_error "Failed to remove conda environment!"
    echo "You may need to deactivate the environment first if it's currently active."
    echo "Try running: conda deactivate"
    echo
    exit 1
fi

echo
print_success "SUCCESS: Environment 'txt-to-epub' has been completely removed!"
echo
echo "Cleanup completed successfully."
echo "You can now safely delete this project folder if you no longer need it."
echo 