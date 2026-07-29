EXTENSION_UUID = bars@vaibhav-sri.github.com
ZIP_NAME = $(EXTENSION_UUID).zip
INSTALL_DIR = $(HOME)/.local/share/gnome-shell/extensions/$(EXTENSION_UUID)

# Files to include in the extension zip
FILES = \
	bars.py \
	extension.js \
	metadata.json \
	stylesheet.css \
	README.md

.PHONY: all pack install clean

all: pack

pack: $(ZIP_NAME)

$(ZIP_NAME): $(FILES)
	@echo "Packaging extension into $(ZIP_NAME)..."
	@zip -q $(ZIP_NAME) $(FILES)
	@echo "Done! You can install it using:"
	@echo "gnome-extensions install $(ZIP_NAME)"

install: pack
	@echo "Checking dependencies..."
	@if ! python3 -c "import dbus" > /dev/null 2>&1; then \
		echo "================================================================="; \
		echo "WARNING: Missing dependency 'python3-dbus'!"; \
		echo "The extension requires it to communicate with media players."; \
		echo "Please run: sudo apt install python3-dbus (Ubuntu/Debian)"; \
		echo "         or sudo dnf install python3-dbus (Fedora)"; \
		echo "================================================================="; \
	fi
	@echo "Removing any existing installation or symlinks to prevent conflicts..."
	@rm -rf $(INSTALL_DIR)
	@echo "Installing extension locally..."
	@gnome-extensions install $(ZIP_NAME)
	@echo "Enabling extension automatically..."
	@gnome-extensions enable $(EXTENSION_UUID)
	@echo "Extension installed and enabled! Please log out and log back in to reload GNOME Shell."

clean:
	@rm -f $(ZIP_NAME)
	@echo "Cleaned."
