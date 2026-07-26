#!/bin/bash
set -e

EXTENSION_UUID="bars@vaibhav-sri.github.com"
ZIP_NAME="${EXTENSION_UUID}.zip"
INSTALL_DIR="${HOME}/.local/share/gnome-shell/extensions/${EXTENSION_UUID}"

echo "Packaging extension..."
zip -q "${ZIP_NAME}" bars.py extension.js metadata.json stylesheet.css README.md

echo "Removing any existing installation or symlinks to prevent conflicts..."
rm -rf "${INSTALL_DIR}"

echo "Installing extension locally..."
gnome-extensions install "${ZIP_NAME}"

echo "Cleaning up..."
rm "${ZIP_NAME}"

echo ""
echo "Extension installed successfully!"
echo "Please log out and log back in to reload GNOME Shell (required for Wayland)."
echo "After logging back in, enable the extension by running:"
echo "  gnome-extensions enable ${EXTENSION_UUID}"
