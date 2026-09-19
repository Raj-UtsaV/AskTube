import streamlit as st

from src.config import load_settings
from src.services.rag import (
    answer_question,
    build_vector_store,
    summarize_video,
)
from src.services.youtube import extract_video_id, get_transcript

SESSION_DEFAULTS = {
    "messages": [],
    "video_id": None,
    "transcript": None,
    "vector_store": None,
    "chunk_count": 0,
    "summary": None,
}

LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
}

APP_STYLES = """
<style>
    .stAppHeader { background: rgba(9, 11, 13, 0.9); }
    [data-testid="stSidebar"] { border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border: 1px solid #30363d;
        border-radius: 4px;
    }
    .block-container { max-width: 1180px; padding-top: 2rem; }
    h1, h2, h3 { letter-spacing: 0; }
    .asktube-kicker {
        color: #28c7d9;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
    }
    .asktube-title { margin: 0; }
    .asktube-subtitle { color: #a9b1ba; margin: 0.35rem 0 1.5rem; }
    .asktube-empty {
        border-left: 3px solid #ff3b30;
        margin-top: 1rem;
        padding: 0.25rem 0 0.25rem 1rem;
    }
    .asktube-empty p { color: #a9b1ba; margin-bottom: 0; }
    [data-testid="stMetric"] {
        background: #11151a;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 0.65rem 0.8rem;
    }
    [data-testid="stChatMessage"] { border-radius: 4px; }
    [data-testid="stChatInput"] {
        position: sticky;
        bottom: 1rem;
        z-index: 10;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 1.25rem; }
    .stTabs [data-baseweb="tab"] { padding-left: 0; padding-right: 0; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 0;
    }
    [data-testid="stVideo"] iframe { max-width: 100%; }
    @media (max-width: 1200px) {
        [data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            width: 100%;
            flex: 1 1 auto;
        }
    }
    @media (max-width: 640px) {
        .block-container { padding: 1rem 1rem 5rem; }
        .asktube-subtitle { margin-bottom: 1rem; }
    }
</style>
"""


def initialize_session() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, list) else value


def reset_session() -> None:
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value.copy() if isinstance(value, list) else value


def render_sidebar(settings):
    with st.sidebar:
        st.image("assets/asktube-banner.png", width="stretch")
        st.subheader("Video setup")
        video_input = st.text_input(
            "YouTube URL or video ID",
            placeholder="https://youtube.com/watch?v=...",
        )
        language = st.selectbox(
            "Transcript language",
            options=list(LANGUAGES),
            format_func=LANGUAGES.get,
        )
        retrieved_chunks = st.slider(
            "Answer context",
            2,
            8,
            4,
            help="Number of transcript sections used for each answer.",
        )
        process = st.button(
            ":material/play_arrow: Process video",
            type="primary",
            width="stretch",
        )
        clear = st.button(
            ":material/delete: Clear workspace",
            width="stretch",
            disabled=st.session_state.video_id is None,
        )
        st.link_button(
            ":material/code: View on GitHub",
            "https://github.com/Raj-UtsaV/AskTube",
            width="stretch",
        )

        if st.session_state.video_id:
            st.divider()
            st.caption("CURRENT VIDEO")
            st.code(st.session_state.video_id, language=None)
            st.caption(f"{st.session_state.chunk_count} transcript sections indexed")

    return (
        settings.groq_api_key,
        settings.groq_model,
        settings.embedding_model,
        settings.huggingface_api_token,
        video_input,
        language,
        retrieved_chunks,
        process,
        clear,
    )


def process_video(video_input, language, embedding_model, huggingface_api_token) -> None:
    video_id = extract_video_id(video_input)
    transcript = get_transcript(video_id, [language.strip() or "en"])
    vector_store, chunk_count = build_vector_store(
        transcript,
        embedding_model,
        huggingface_api_token,
    )

    st.session_state.update(
        video_id=video_id,
        transcript=transcript,
        vector_store=vector_store,
        chunk_count=chunk_count,
        messages=[],
        summary=None,
    )


def render_chat(api_key, chat_model, retrieved_chunks) -> None:
    history = st.container()
    question = st.chat_input("Ask something about this video...")

    with history:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("sources"):
                    with st.expander("Transcript sources"):
                        for index, source in enumerate(message["sources"], start=1):
                            st.markdown(f"**Source {index}**")
                            st.write(source)

        if not question:
            return

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Searching transcript and asking Groq..."):
                    answer, docs = answer_question(
                        question,
                        st.session_state.vector_store,
                        api_key,
                        chat_model,
                        retrieved_chunks,
                    )
                st.markdown(answer)
                sources = [doc.page_content for doc in docs]
                with st.expander("Transcript sources"):
                    for index, doc in enumerate(docs, start=1):
                        st.markdown(f"**Source {index}**")
                        st.write(doc.page_content)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
            except Exception as exc:
                st.error(f"Could not answer the question: {exc}")


def run() -> None:
    initialize_session()
    settings = load_settings()
    st.markdown(APP_STYLES, unsafe_allow_html=True)

    (
        api_key,
        chat_model,
        embedding_model,
        huggingface_api_token,
        video_input,
        language,
        retrieved_chunks,
        process,
        clear,
    ) = render_sidebar(settings)

    st.markdown(
        '<p class="asktube-kicker">YouTube knowledge workspace</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<h1 class="asktube-title">AskTube</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="asktube-subtitle">Ask grounded questions, build a summary, '
        'and inspect the transcript behind every answer.</p>',
        unsafe_allow_html=True,
    )

    if clear:
        reset_session()
        st.rerun()

    if process:
        if not api_key:
            st.error("The language model service is not configured.")
        elif not huggingface_api_token:
            st.error("The embedding service is not configured.")
        elif not video_input.strip():
            st.error("Enter a YouTube URL or video ID.")
        else:
            try:
                with st.spinner("Fetching transcript and preparing the video..."):
                    process_video(
                        video_input,
                        language,
                        embedding_model,
                        huggingface_api_token,
                    )
                st.success(
                    f"Video ready. Indexed {st.session_state.chunk_count} "
                    "transcript sections."
                )
            except Exception as exc:
                st.error(f"Could not process the video: {exc}")

    if st.session_state.vector_store is None:
        st.image("assets/asktube-banner.png", width="stretch")
        st.markdown(
            """
            <div class="asktube-empty">
                <strong>Start with a YouTube video</strong>
                <p>Paste a URL or video ID in the sidebar, choose the transcript
                language, and process it to open the workspace.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    player_column, details_column = st.columns([1.7, 1], gap="large")
    with player_column:
        st.video(f"https://www.youtube.com/watch?v={st.session_state.video_id}")
    with details_column:
        st.caption("VIDEO STATUS")
        st.subheader("Ready to explore")
        metric_left, metric_right = st.columns(2)
        metric_left.metric("Sections", st.session_state.chunk_count)
        metric_right.metric("Language", LANGUAGES[language])
        st.caption("Answers use only the indexed transcript context.")

    chat_tab, summary_tab, transcript_tab = st.tabs(
        ["Chat", "Summary", "Transcript"]
    )
    with chat_tab:
        render_chat(api_key, chat_model, retrieved_chunks)

    with summary_tab:
        st.subheader("Video summary")
        if st.button(
            ":material/notes: Generate summary",
            type="primary",
            disabled=st.session_state.summary is not None,
        ):
            if not api_key:
                st.error("The language model service is not configured.")
            else:
                try:
                    with st.spinner("Building the summary..."):
                        st.session_state.summary = summarize_video(
                            st.session_state.transcript, api_key, chat_model
                        )
                except Exception as exc:
                    st.error(f"Could not summarize the video: {exc}")
        if st.session_state.summary:
            st.markdown(st.session_state.summary)
        else:
            st.caption(
                "Generate a concise overview and key points from the transcript."
            )

    with transcript_tab:
        st.subheader("Full transcript")
        st.download_button(
            ":material/download: Download transcript",
            st.session_state.transcript,
            file_name=f"{st.session_state.video_id}-transcript.txt",
            mime="text/plain",
        )
        with st.container(height=420):
            st.write(st.session_state.transcript)
