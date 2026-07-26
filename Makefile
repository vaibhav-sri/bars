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
	@echo "Removing any existing installation or symlinks to prevent conflicts..."
	@rm -rf $(INSTALL_DIR)
	@echo "Installing extension locally..."
	@gnome-extensions install $(ZIP_NAME)
	@echo "Extension installed! Please log out and log back in (Wayland) or press Alt+F2, type 'r', and press Enter (X11)."
	@echo "Then enable it with: gnome-extensions enable $(EXTENSION_UUID)"

clean:
	@rm -f $(ZIP_NAME)
	@echo "Cleaned."
