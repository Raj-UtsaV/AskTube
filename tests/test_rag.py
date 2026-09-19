import unittest

from src.services.rag import _split_text


class SplitTextTests(unittest.TestCase):
    def test_splits_large_text(self):
        chunks = _split_text("a" * 25_000, chunk_size=12_000)

        self.assertEqual([len(chunk) for chunk in chunks], [12_000, 12_000, 1_000])

    def test_skips_empty_chunks(self):
        self.assertEqual(_split_text("   ", chunk_size=2), [])


if __name__ == "__main__":
    unittest.main()
