import unittest

from youtube_rag.services.youtube import extract_video_id


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


if __name__ == "__main__":
    unittest.main()
