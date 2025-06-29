#!/bin/bash

echo "========================================"
echo "TXT to EPUB Converter - Environment cleanup (macOS)"
echo "========================================"
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
    print_warning "This script is optimized for macOS. Use cleanup_unix.sh for other Unix systems."
fi

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed or not in PATH!"
    echo "Cannot proceed with cleanup."
    echo
    print_info "If you installed conda but it's not in PATH, try:"
    echo "source ~/miniconda3/etc/profile.d/conda.sh"
    echo "or"
    echo "source ~/anaconda3/etc/profile.d/conda.sh"
    echo
    exit 1
fi

print_success "[1/3] Checking conda installation... OK"

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
if ! conda env list | grep -q "txt-to-epub"; then
    echo "[2/3] Environment 'txt-to-epub' not found."
    echo "Nothing to clean up."
    echo
    exit 0
fi

print_success "[2/3] Found environment 'txt-to-epub'"
echo

# Show environment info and disk usage
echo "Environment details:"
conda env list | grep "txt-to-epub"

# Try to show disk usage (macOS specific)
env_path=$(conda env list | grep "txt-to-epub" | awk '{print $2}')
if [[ -d "$env_path" ]]; then
    disk_usage=$(du -sh "$env_path" 2>/dev/null | cut -f1)
    if [[ -n "$disk_usage" ]]; then
        print_info "Environment size: $disk_usage"
    fi
fi
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

# Check if environment is currently active
if [[ "$CONDA_DEFAULT_ENV" == "txt-to-epub" ]]; then
    print_warning "Environment is currently active. Deactivating first..."
    conda deactivate
fi

# Remove the environment
conda env remove -n txt-to-epub -y
if [ $? -ne 0 ]; then
    print_error "Failed to remove conda environment!"
    echo
    print_info "Common solutions:"
    print_info "1. Make sure the environment is not active in any terminal"
    print_info "2. Try: conda deactivate && conda env remove -n txt-to-epub -y"
    print_info "3. Check if any applications are using the environment"
    echo
    exit 1
fi

echo
print_success "SUCCESS: Environment 'txt-to-epub' has been completely removed!"
echo
echo "Cleanup completed successfully."
print_info "You can now safely delete this project folder if you no longer need it."
echo

# macOS specific: Check if there are any related cache files
cache_dirs=(
    "$HOME/.cache/pip"
    "$HOME/Library/Caches/pip"
    "$HOME/.gradio"
)

echo "Optional: Clean up related cache files?"
echo "This will remove pip and gradio cache files (safe to do)."
read -p "Clean cache files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            print_info "Cleaning $cache_dir..."
            rm -rf "$cache_dir"
        fi
    done
    print_success "Cache files cleaned!"
fi

echo
print_success "All cleanup operations completed!" 