import re
import time


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
VIDEO_URL_PATTERNS = (
    re.compile(r"(?:v=)([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([A-Za-z0-9_-]{11})"),
    re.compile(r"youtube\.com/embed/([A-Za-z0-9_-]{11})"),
)
TRANSCRIPT_FETCH_ATTEMPTS = 3
TRANSCRIPT_RETRY_DELAY_SECONDS = 0.5


def extract_video_id(value: str) -> str:
    """Return the video ID from a YouTube URL or raw ID."""
    value = value.strip()

    for pattern in VIDEO_URL_PATTERNS:
        if match := pattern.search(value):
            return match.group(1)

    if VIDEO_ID_PATTERN.fullmatch(value):
        return value

    raise ValueError("Enter a valid YouTube URL or 11-character video ID.")


def _network_errors() -> tuple[type[BaseException], ...]:
    errors: tuple[type[BaseException], ...] = (ConnectionError, TimeoutError, OSError)
    try:
        from requests import exceptions as requests_exceptions

        return errors + (
            requests_exceptions.ConnectionError,
            requests_exceptions.Timeout,
        )
    except ImportError:
        return errors


def get_transcript(video_id: str, languages: list[str] | None = None) -> str:
    """Fetch and flatten a YouTube transcript."""
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    transcript_languages = languages or ["en"]
    for attempt in range(TRANSCRIPT_FETCH_ATTEMPTS):
        try:
            fetched = api.fetch(video_id, languages=transcript_languages)
            break
        except _network_errors() as exc:
            if attempt == TRANSCRIPT_FETCH_ATTEMPTS - 1:
                raise ValueError(
                    "Could not reach YouTube for the transcript. Try again in a "
                    "moment; if it keeps failing, YouTube may be blocking this "
                    "network."
                ) from exc
            time.sleep(TRANSCRIPT_RETRY_DELAY_SECONDS * (attempt + 1))

    transcript = " ".join(snippet.text for snippet in fetched).strip()

    if not transcript:
        raise ValueError("The transcript is empty.")

    return transcript
