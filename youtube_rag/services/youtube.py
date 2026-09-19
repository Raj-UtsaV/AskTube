import re


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
VIDEO_URL_PATTERNS = (
    re.compile(r"(?:v=)([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/embed/([A-Za-z0-9_-]{11})"),
)


def extract_video_id(value: str) -> str:
    """Return the video ID from a YouTube URL or raw ID."""
    value = value.strip()

    for pattern in VIDEO_URL_PATTERNS:
        if match := pattern.search(value):
            return match.group(1)

    if VIDEO_ID_PATTERN.fullmatch(value):
        return value

    raise ValueError("Enter a valid YouTube URL or 11-character video ID.")


def get_transcript(video_id: str, languages: list[str] | None = None) -> str:
    """Fetch and flatten a YouTube transcript."""
    from youtube_transcript_api import YouTubeTranscriptApi

    fetched = YouTubeTranscriptApi().fetch(
        video_id,
        languages=languages or ["en"],
    )
    transcript = " ".join(snippet.text for snippet in fetched).strip()

    if not transcript:
        raise ValueError("The transcript is empty.")

    return transcript
