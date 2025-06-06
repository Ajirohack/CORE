#!/bin/bash

# Archivist Package Setup Script
# This script prepares the Archivist Package for use in SpaceNew

set -e

echo "Setting up Archivist Package for SpaceNew..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# SpaceNew root directory
SPACENEW_DIR=$(dirname $(dirname $(dirname "$SCRIPT_DIR")))

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p "$SPACENEW_DIR/data/archivist/personas"
mkdir -p "$SPACENEW_DIR/data/archivist/scenarios"
mkdir -p "$SPACENEW_DIR/data/archivist/stages"
mkdir -p "$SPACENEW_DIR/data/archivist/knowledge"
mkdir -p "$SPACENEW_DIR/data/financial/templates"
mkdir -p "$SPACENEW_DIR/logs/archivist"

# Copy MirrorCore files from human-simulator
if [ -d "/Users/macbook/Desktop/y2.5 - ReDefination/proposal/human-simulator/archived_new_data" ]; then
    echo "Copying MirrorCore files from human-simulator..."
    mkdir -p "$SCRIPT_DIR/components/mirrorcore"
    cp -r "/Users/macbook/Desktop/y2.5 - ReDefination/proposal/human-simulator/archived_new_data/"*.py "$SCRIPT_DIR/components/mirrorcore/"
    cp -r "/Users/macbook/Desktop/y2.5 - ReDefination/proposal/human-simulator/archived_new_data/"*.json "$SPACENEW_DIR/data/archivist/stages/"
else
    echo "Warning: human-simulator files not found, skipping..."
fi

# Copy financial-business-app files
if [ -d "/Volumes/Project Disk/financial-business-app/src" ]; then
    echo "Copying financial-business-app files..."
    mkdir -p "$SCRIPT_DIR/components/financial"
    cp -r "/Volumes/Project Disk/financial-business-app/src/components" "$SCRIPT_DIR/components/financial/"
else
    echo "Warning: financial-business-app files not found, skipping..."
fi

# Copy Archivist Mode files
if [ -d "/Users/macbook/Downloads/whyte_houx_final/build/Archivist Mode" ]; then
    echo "Copying Archivist Mode files..."
    mkdir -p "$SPACENEW_DIR/data/archivist/knowledge/archivist_mode"
    cp "/Users/macbook/Downloads/whyte_houx_final/build/Archivist Mode/"*.md "$SPACENEW_DIR/data/archivist/knowledge/archivist_mode/"
else
    echo "Warning: Archivist Mode files not found, skipping..."
fi

# Create necessary __init__.py files
touch "$SCRIPT_DIR/components/__init__.py"
touch "$SCRIPT_DIR/components/mirrorcore/__init__.py"
touch "$SCRIPT_DIR/components/financial/__init__.py"

# Create symlinks to plugin_system if needed
if [ ! -L "$SCRIPT_DIR/plugin_system" ] && [ -d "/Users/macbook/Downloads/whyte_houx_final/build/developers/scalfolding-apps/SpaceNew/core/packages/plugin_system" ]; then
    echo "Creating symlink to plugin_system..."
    ln -s "/Users/macbook/Downloads/whyte_houx_final/build/developers/scalfolding-apps/SpaceNew/core/packages/plugin_system" "$SCRIPT_DIR/plugin_system"
fi

# Install Python requirements
echo "Creating requirements.txt..."
cat > "$SCRIPT_DIR/requirements.txt" << EOF
pydantic>=2.0.0
fastapi>=0.95.0
playwright>=1.40.0
selenium>=4.10.0
pinecone-client>=2.2.2
langchain>=0.0.267
sentence-transformers>=2.2.2
unstructured>=0.10.0
tiktoken>=0.5.0
pandas>=2.0.0
PyPDF2>=3.0.0
python-docx>=0.8.11
EOF

echo "Installing Python requirements..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Install browser automation dependencies if required
if command -v playwright &> /dev/null; then
    echo "Installing Playwright browsers..."
    playwright install
elif command -v selenium &> /dev/null; then
    echo "Installing ChromeDriver..."
    # This is platform specific and might need adjustment
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install --cask chromedriver
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        apt-get install -y chromium-chromedriver
    fi
fi

echo "Archivist Package setup complete!"
echo "To use the package, ensure it's enabled in your SpaceNew configuration."
