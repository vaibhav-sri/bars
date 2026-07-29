#!/bin/bash
set -e

EXTENSION_UUID="bars@vaibhav-sri.github.com"
ZIP_NAME="${EXTENSION_UUID}.zip"
INSTALL_DIR="${HOME}/.local/share/gnome-shell/extensions/${EXTENSION_UUID}"

echo "Packaging extension..."
zip -q "${ZIP_NAME}" bars.py extension.js metadata.json stylesheet.css README.md

echo "Removing any existing installation or symlinks to prevent conflicts..."
rm -rf "${INSTALL_DIR}"

echo "Checking dependencies..."
if ! python3 -c "import dbus" &> /dev/null; then
    echo "================================================================="
    echo "WARNING: Missing dependency 'python3-dbus'!"
    echo "The extension requires it to communicate with media players."
    echo "Please run: sudo apt install python3-dbus (Ubuntu/Debian)"
    echo "         or sudo dnf install python3-dbus (Fedora)"
    echo "================================================================="
fi

echo "Installing extension locally..."
gnome-extensions install "${ZIP_NAME}"

echo "Cleaning up..."
rm "${ZIP_NAME}"

echo "Enabling extension automatically..."
gnome-extensions enable "${EXTENSION_UUID}"

echo ""
echo "Extension installed and enabled successfully!"
echo "Please log out and log back in to reload GNOME Shell and see the extension on your top bar."
