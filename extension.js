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
        this._scriptPath = this.dir.get_child('lyrics.py').get_path();
        
        this._startDaemon();
    }

    _startDaemon() {
        try {
            this._proc = new Gio.Subprocess({
                argv: ['python3', '-u', this._scriptPath], // -u for unbuffered stdout
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });
            this._proc.init(null);
            
            let stdoutPipe = this._proc.get_stdout_pipe();
            this._dataStream = new Gio.DataInputStream({
                base_stream: stdoutPipe,
                close_base_stream: true
            });
            
            this._readNextLine();
        } catch (e) {
            console.error(`${this.uuid}: Failed to spawn script`, e);
        }
    }

    _readNextLine() {
        if (!this._dataStream) return;
        
        this._dataStream.read_line_async(GLib.PRIORITY_DEFAULT, null, (stream, res) => {
            try {
                let [line, length] = stream.read_line_finish_utf8(res);
                if (line !== null) {
                    this._label.set_text(line.trim());
                    // Read next line recursively
                    this._readNextLine();
                } else {
                    // EOF reached, meaning process died.
                    console.log(`${this.uuid}: Python daemon exited`);
                    this._proc = null;
                }
            } catch (e) {
                console.error(`${this.uuid}: Error reading stdout`, e);
            }
        });
    }

    disable() {
        if (this._proc) {
            this._proc.force_exit();
            this._proc = null;
        }

        if (this._dataStream) {
            this._dataStream.close(null);
            this._dataStream = null;
        }

        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
        this._label = null;
    }
}
