import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';
import Clutter from 'gi://Clutter';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

export default class LyricsBarExtension extends Extension {
    enable() {
        this._indicator = new PanelMenu.Button(0.0, 'Lyrics Bar', false);
        
        // Add a label
        this._label = new St.Label({
            text: '🎵 Loading...',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'lyrics-bar-label'
        });
        
        this._indicator.add_child(this._label);
        
        // Add to the top bar (left)
        Main.panel.addToStatusArea(this.uuid, this._indicator, 1, 'left');

        // Prepare the command to run our python helper script
        // We will bundle lyrics.py in our extension folder
        this._scriptPath = this.dir.get_child('lyrics.py').get_path();

        // Start a timer to update
        this._timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1000, () => {
            this._updateLyrics();
            return GLib.SOURCE_CONTINUE;
        });
        
        this._updateLyrics();
    }

    _updateLyrics() {
        try {
            let proc = new Gio.Subprocess({
                argv: ['python3', this._scriptPath],
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });
            proc.init(null);
            
            proc.communicate_utf8_async(null, null, (proc, res) => {
                try {
                    let [ok, stdout, stderr] = proc.communicate_utf8_finish(res);
                    if (ok && stdout) {
                        this._label.set_text(stdout.trim());
                    }
                } catch (e) {
                    console.error(`${this.uuid}: Error reading stdout`, e);
                }
            });
        } catch (e) {
            console.error(`${this.uuid}: Failed to spawn script`, e);
        }
    }

    disable() {
        if (this._timeout) {
            GLib.Source.remove(this._timeout);
            this._timeout = null;
        }

        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
        this._label = null;
    }
}
