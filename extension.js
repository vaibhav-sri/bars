import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';
import Clutter from 'gi://Clutter';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';

export default class BarsExtension extends Extension {
    enable() {
        this._indicator = new PanelMenu.Button(0.0, 'Bars', false);
        
        // Add a label
        this._label = new St.Label({
            text: 'Loading...',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'bars-label'
        });
        
        this._indicator.add_child(this._label);
        
        // Add to the top bar (left) 
        Main.panel.addToStatusArea(this.uuid, this._indicator, -1, 'left');

        // GNOME loads extensions in an unpredictable order. 
        // We connect to 'child-added' on the leftBox to guarantee Bars 
        // stays permanently at the far right of the left panel!
        this._actorAddedId = Main.panel._leftBox.connect('child-added', () => {
            if (this._indicator) {
                GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => {
                    let leftBox = Main.panel._leftBox;
                    let children = leftBox.get_children();
                    let indicatorActor = this._indicator.container || this._indicator;
                    if (children.length > 0 && children[children.length - 1] !== indicatorActor) {
                        leftBox.set_child_at_index(indicatorActor, leftBox.get_n_children() - 1);
                    }
                    return GLib.SOURCE_REMOVE;
                });
            }
        });

        // Listen for screen lock/unlock to hide/show lyrics
        this._sessionUpdatedId = Main.sessionMode.connect('updated', () => {
            this._updateLabel();
        });

        // Prepare the command to run our python helper script
        this._scriptPath = this.dir.get_child('bars.py').get_path();
        
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

    _updateLabel() {
        if (!this._lastData) return;
        let data = this._lastData;
        if (Main.sessionMode.currentMode === 'unlock-dialog') {
            if (data.title) {
                this._label.set_text(`${data.title}`);
            } else {
                this._label.set_text('');
            }
        } else {
            this._label.set_text(data.text);
        }
    }

    _readNextLine() {
        if (!this._dataStream) return;
        
        this._dataStream.read_line_async(GLib.PRIORITY_DEFAULT, null, (stream, res) => {
            try {
                let [line, length] = stream.read_line_finish_utf8(res);
                if (line !== null) {
                    try {
                        let data = JSON.parse(line.trim());
                        this._lastData = data;
                        this._updateLabel();
                    } catch (e) {
                        this._label.set_text(line.trim());
                    }
                    // Read next line recursively
                    this._readNextLine();
                } else {
                    // EOF reached, meaning process died.
                    console.log(`${this.uuid}: Python daemon exited`);
                    this._proc = null;
                    
                    // Restart daemon automatically after 5 seconds to recover from suspend/crashes
                    this._timeout = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 5, () => {
                        if (!this._proc) {
                            this._startDaemon();
                        }
                        this._timeout = null;
                        return GLib.SOURCE_REMOVE;
                    });
                }
            } catch (e) {
                console.error(`${this.uuid}: Error reading stdout`, e);
            }
        });
    }

    disable() {
        if (this._actorAddedId) {
            Main.panel._leftBox.disconnect(this._actorAddedId);
            this._actorAddedId = null;
        }

        if (this._sessionUpdatedId) {
            Main.sessionMode.disconnect(this._sessionUpdatedId);
            this._sessionUpdatedId = null;
        }

        if (this._timeout) {
            GLib.Source.remove(this._timeout);
            this._timeout = null;
        }

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
