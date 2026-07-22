import unittest
from unittest.mock import patch
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
        self.assertEqual(daemon.tick(), "🎵 No player")

    @patch('bars.get_mpris_players')
    @patch('bars.get_metadata')
    def test_daemon_nothing_playing(self, mock_get_metadata, mock_get_players):
        mock_get_players.return_value = ["org.mpris.MediaPlayer2.firefox"]
        mock_get_metadata.return_value = ({}, 0, "Stopped")
        daemon = bars.BarsDaemon()
        self.assertEqual(daemon.tick(), "🎵 Nothing playing")

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
        self.assertEqual(daemon.tick(), "First line")

        # Advance position to 13 seconds
        mock_get_metadata.return_value = (
            {'xesam:artist': ['Test Artist'], 'xesam:title': 'Test Song'},
            13000000,
            "Playing"
        )
        self.assertEqual(daemon.tick(), "Second line")

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
        self.assertEqual(daemon.tick(), "🎵 Nothing playing")

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


if __name__ == '__main__':
    unittest.main()
