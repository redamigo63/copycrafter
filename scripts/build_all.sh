#!/bin/bash

# Exit on error
set -e

# Make sure we're in the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
cd "$PROJECT_ROOT"
echo "Working directory: $(pwd)"

# Get version from pubspec.yaml
VERSION=$(grep 'version:' pubspec.yaml | sed 's/version: //' | tr -d '\r')
echo "Building CopyCrafter version $VERSION"

# Create releases directory if it doesn't exist
mkdir -p releases

# Function to build for a specific platform
build_for_platform() {
  PLATFORM=$1
  BUILD_TYPE=$2
  OUTPUT_NAME=$3
  
  echo "Building for $PLATFORM..."
  flutter build $PLATFORM --release

  if [ "$PLATFORM" = "macos" ]; then
    echo "Creating DMG for macOS..."
    # You'll need create-dmg installed: brew install create-dmg
    if command -v create-dmg &> /dev/null; then
      create-dmg \
        --volname "CopyCrafter" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "CopyCrafter.app" 200 190 \
        --hide-extension "CopyCrafter.app" \
        --app-drop-link 600 185 \
        "releases/CopyCrafter-$VERSION-macOS.dmg" \
        "build/macos/Build/Products/Release/CopyCrafter.app"
    else
      echo "create-dmg not installed. Skipping DMG creation."
      echo "To install create-dmg, run: brew install create-dmg"
      # Just copy the app bundle
      mkdir -p "releases"
      if [ -d "build/macos/Build/Products/Release/CopyCrafter.app" ]; then
        cp -r "build/macos/Build/Products/Release/CopyCrafter.app" "releases/CopyCrafter-$VERSION-macOS.app"
        echo "App bundle copied to releases/CopyCrafter-$VERSION-macOS.app"
      else
        echo "ERROR: Could not find the built macOS app at build/macos/Build/Products/Release/CopyCrafter.app"
        echo "Build may have failed or the app may be located elsewhere."
        ls -la build/macos/Build/Products/Release/ || echo "Directory does not exist"
      fi
    fi
  elif [ "$PLATFORM" = "windows" ]; then
    echo "Packaging Windows executable..."
    # Zip the Windows build
    if [ -d "build/$BUILD_TYPE" ]; then
      cd "build/$BUILD_TYPE"
      zip -r "../../../releases/$OUTPUT_NAME-$VERSION-windows.zip" .
      cd ../../..
      echo "Windows package created at releases/$OUTPUT_NAME-$VERSION-windows.zip"
    else
      echo "ERROR: Could not find Windows build at build/$BUILD_TYPE"
      echo "Build may have failed or files may be located elsewhere."
    fi
  fi
  
  echo "Build for $PLATFORM completed!"
}

# Build for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  build_for_platform "macos" "macos/Runner/Release" "CopyCrafter"
else
  echo "Skipping macOS build (not on macOS)"
fi

# Build for Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  build_for_platform "windows" "windows/runner/Release" "CopyCrafter"
else
  echo "Skipping Windows build (not on Windows)"
fi

echo "All builds completed!"
echo "Check the 'releases' directory for the built packages." 