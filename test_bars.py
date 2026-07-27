import unittest
from unittest.mock import patch
import json
import bars


class TestBarsDaemon(unittest.TestCase):
    def test_parse_synced_lyrics(self):
        lrc = "[00:10.50] Hello world\n[00:12.00] \n[00:15.25] Next line"
        parsed = bars.parse_synced_lyrics(lrc)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], (10.5, "Hello world"))
        self.assertEqual(parsed[1], (12.0, ""))
        self.assertEqual(parsed[2], (15.25, "Next line"))

    @patch('bars.get_mpris_players')
    def test_daemon_no_players(self, mock_get_players):
        mock_get_players.return_value = []
        daemon = bars.BarsDaemon()
        self.assertEqual(json.loads(daemon.tick())['text'], "No player")

    @patch('bars.get_mpris_players')
    @patch('bars.get_metadata')
    def test_daemon_nothing_playing(self, mock_get_metadata, mock_get_players):
        mock_get_players.return_value = ["org.mpris.MediaPlayer2.firefox"]
        mock_get_metadata.return_value = ({}, 0, "Stopped")
        daemon = bars.BarsDaemon()
        self.assertEqual(json.loads(daemon.tick())['text'], "Nothing playing")

    @patch('bars.get_mpris_players')
    @patch('bars.get_metadata')
    @patch('bars.get_cached_lyrics')
    def test_daemon_playing_synced(
            self,
            mock_get_cached,
            mock_get_metadata,
            mock_get_players):
        mock_get_players.return_value = ["org.mpris.MediaPlayer2.firefox"]
        # Position is in microseconds (11.0 seconds)
        mock_get_metadata.return_value = (
            {'xesam:artist': ['Test Artist'], 'xesam:title': 'Test Song'},
            11000000,
            "Playing"
        )
        mock_get_cached.return_value = "[00:10.50] First line\n[00:12.00] Second line"

        daemon = bars.BarsDaemon()
        self.assertEqual(json.loads(daemon.tick())['text'], "First line")

        # Advance position to 13 seconds
        mock_get_metadata.return_value = (
            {'xesam:artist': ['Test Artist'], 'xesam:title': 'Test Song'},
            13000000,
            "Playing"
        )
        self.assertEqual(json.loads(daemon.tick())['text'], "Second line")

    def test_parse_synced_lyrics_malformed(self):
        lrc = "[00:10.50] Good\n[invalid] Bad\n[99:99.99] Also good\nJust text\n[00:11] Missing decimal\n[00:12:00] Three colons"
        parsed = bars.parse_synced_lyrics(lrc)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], (10.5, "Good"))
        self.assertEqual(parsed[1], (99 * 60 + 99.99, "Also good"))
        self.assertEqual(parsed[2], (11.0, "Missing decimal"))

    @patch('bars.get_mpris_players')
    @patch('bars.get_metadata')
    def test_daemon_empty_metadata_fields(
            self, mock_get_metadata, mock_get_players):
        mock_get_players.return_value = ["org.mpris.MediaPlayer2.firefox"]
        mock_get_metadata.return_value = (
            {'xesam:artist': [], 'xesam:title': ''}, 0, "Playing")
        daemon = bars.BarsDaemon()
        self.assertEqual(json.loads(daemon.tick())['text'], "Nothing playing")

    @patch('os.path.exists')
    @patch('builtins.open',
           new_callable=unittest.mock.mock_open,
           read_data='invalid json')
    @patch('bars.fetch_lyrics')
    def test_get_cached_lyrics_corrupted_cache(
            self, mock_fetch, mock_file, mock_exists):
        mock_exists.return_value = True
        mock_fetch.return_value = "[00:10.00] Fetched"
        # Since JSON is invalid, it should gracefully fall back to fetching
        lrc = bars.get_cached_lyrics("Artist", "Title")
        self.assertEqual(lrc, "[00:10.00] Fetched")
        mock_fetch.assert_called_once_with("Artist", "Title")

    @patch('bars.get_mpris_players')
    def test_daemon_exit_on_consecutive_errors(self, mock_get_players):
        mock_get_players.side_effect = Exception("DBus broken")
        daemon = bars.BarsDaemon()

        # Simulate 50 consecutive errors
        for _ in range(50):
            self.assertIsNone(daemon.tick())

        # The 51st error should trigger sys.exit(1)
        with self.assertRaises(SystemExit) as cm:
            daemon.tick()
        self.assertEqual(cm.exception.code, 1)

    @patch('bars.get_mpris_players')
    @patch('bars.get_metadata')
    def test_json_rendering_schema(self, mock_get_metadata, mock_get_players):
        # This test ensures that the daemon output perfectly adheres to the expected
        # JSON schema required by extension.js for rendering, eliminating UI crashes.
        mock_get_players.return_value = ["org.mpris.MediaPlayer2.firefox"]
        mock_get_metadata.return_value = (
            {'xesam:artist': ['Test Artist'], 'xesam:title': 'Test Song'},
            11000000,
            "Playing"
        )
        
        daemon = bars.BarsDaemon()
        output = daemon.tick()
        
        # Must be valid JSON string
        self.assertIsInstance(output, str)
        data = json.loads(output)
        
        # Must contain all required keys for extension.js
        self.assertIn('title', data)
        self.assertIn('artist', data)
        self.assertIn('text', data)
        self.assertIn('status', data)
        
        # Verify data types
        self.assertIsInstance(data['title'], str)
        self.assertIsInstance(data['artist'], str)
        self.assertIsInstance(data['text'], str)
        self.assertIsInstance(data['status'], str)

    @patch('bars.get_mpris_players')
    @patch('bars.get_metadata')
    def test_firefox_string_artist_metadata(self, mock_get_metadata, mock_get_players):
        # Firefox MPRIS sometimes returns xesam:artist as a single string instead of a list.
        # This test ensures we don't accidentally extract just the first character.
        mock_get_players.return_value = ["org.mpris.MediaPlayer2.firefox"]
        mock_get_metadata.return_value = (
            {'xesam:artist': 'Jim Croce', 'xesam:title': 'Time in a Bottle'},
            0,
            "Playing"
        )
        
        daemon = bars.BarsDaemon()
        daemon.tick()
        
        self.assertEqual(daemon.last_artist, 'Jim Croce')
        self.assertEqual(daemon.last_title, 'Time in a Bottle')

    @patch('bars.get_mpris_players')
    @patch('bars.get_metadata')
    @patch('bars.get_cached_lyrics')
    def test_daemon_instrumental_gap(
            self,
            mock_get_cached,
            mock_get_metadata,
            mock_get_players):
        # This test ensures that the daemon shows the song title before lyrics start,
        # and "..." during long instrumental gaps.
        mock_get_players.return_value = ["org.mpris.MediaPlayer2.firefox"]
        mock_get_cached.return_value = "[00:10.00] First lyric\n[00:20.00] \n[00:30.00] Second lyric"
        
        # Position 0: Before first lyric (should show song title)
        mock_get_metadata.return_value = (
            {'xesam:artist': ['Artist'], 'xesam:title': 'Song'},
            0,
            "Playing"
        )
        daemon = bars.BarsDaemon()
        self.assertEqual(json.loads(daemon.tick())['text'], "Song - Artist")

        # Position 11 seconds: During first lyric
        mock_get_metadata.return_value = (
            {'xesam:artist': ['Artist'], 'xesam:title': 'Song'},
            11000000,
            "Playing"
        )
        self.assertEqual(json.loads(daemon.tick())['text'], "First lyric")

        # Position 22 seconds: During instrumental gap
        mock_get_metadata.return_value = (
            {'xesam:artist': ['Artist'], 'xesam:title': 'Song'},
            22000000,
            "Playing"
        )
        self.assertEqual(json.loads(daemon.tick())['text'], "...")


if __name__ == '__main__':
    unittest.main()
