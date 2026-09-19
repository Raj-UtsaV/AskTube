import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.services.youtube import extract_video_id, get_transcript


class ExtractVideoIdTests(unittest.TestCase):
    def test_accepts_supported_formats(self):
        video_id = "dQw4w9WgXcQ"
        values = (
            video_id,
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://youtu.be/{video_id}",
            f"https://youtube.com/shorts/{video_id}",
            f"https://youtube.com/embed/{video_id}",
        )

        for value in values:
            with self.subTest(value=value):
                self.assertEqual(extract_video_id(value), video_id)

    def test_rejects_invalid_input(self):
        with self.assertRaises(ValueError):
            extract_video_id("invalid")


class GetTranscriptTests(unittest.TestCase):
    def test_retries_transient_connection_reset(self):
        api = FlakyTranscriptApi(failures=1)

        with patch("youtube_transcript_api.YouTubeTranscriptApi", return_value=api):
            with patch("src.services.youtube.time.sleep") as sleep:
                transcript = get_transcript("dQw4w9WgXcQ")

        self.assertEqual(transcript, "hello world")
        self.assertEqual(api.calls, 2)
        sleep.assert_called_once()

    def test_raises_clear_error_after_repeated_connection_resets(self):
        api = FlakyTranscriptApi(failures=3)

        with patch("youtube_transcript_api.YouTubeTranscriptApi", return_value=api):
            with patch("src.services.youtube.time.sleep"):
                with self.assertRaisesRegex(ValueError, "Could not reach YouTube"):
                    get_transcript("dQw4w9WgXcQ")


class FlakyTranscriptApi:
    def __init__(self, failures):
        self.calls = 0
        self.failures = failures

    def fetch(self, video_id, languages):
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectionResetError(104, "Connection reset by peer")
        return [SimpleNamespace(text="hello"), SimpleNamespace(text="world")]


if __name__ == "__main__":
    unittest.main()
