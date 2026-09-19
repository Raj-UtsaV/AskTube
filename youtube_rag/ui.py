import streamlit as st

from youtube_rag.config import load_settings
from youtube_rag.services.rag import (
    answer_question,
    build_vector_store,
    summarize_video,
)
from youtube_rag.services.youtube import extract_video_id, get_transcript

SESSION_DEFAULTS = {
    "messages": [],
    "video_id": None,
    "transcript": None,
    "vector_store": None,
    "chunk_count": 0,
}


def initialize_session() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, list) else value


def reset_session() -> None:
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value.copy() if isinstance(value, list) else value


def render_options(settings):
    language_column, chunks_column = st.columns(2)
    language = language_column.selectbox(
        "Transcript language",
        options=["en", "hi", "es", "fr", "de", "pt", "ja", "ko"],
        format_func={
            "en": "English",
            "hi": "Hindi",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "pt": "Portuguese",
            "ja": "Japanese",
            "ko": "Korean",
        }.get,
    )
    retrieved_chunks = chunks_column.slider("Retrieved chunks", 2, 8, 4)

    return (
        settings.groq_api_key,
        settings.groq_model,
        settings.embedding_model,
        settings.huggingface_api_token,
        language,
        retrieved_chunks,
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
    )


def render_chat(api_key, chat_model, retrieved_chunks) -> None:
    st.markdown("### Chat with the video")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not (question := st.chat_input("Ask something about this video...")):
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
            with st.expander("Retrieved transcript chunks"):
                for index, doc in enumerate(docs, start=1):
                    st.markdown(f"**Chunk {index}**")
                    st.write(doc.page_content)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
        except Exception as exc:
            st.error(f"Could not answer the question: {exc}")


def run() -> None:
    initialize_session()
    settings = load_settings()

    st.title("🎥 AskTube")
    st.caption("Ask questions and generate summaries from YouTube transcripts.")
    video_input = st.text_input(
        "YouTube URL or video ID",
        placeholder="https://www.youtube.com/watch?v=...",
    )
    (
        api_key,
        chat_model,
        embedding_model,
        huggingface_api_token,
        language,
        retrieved_chunks,
    ) = render_options(settings)
    process_column, clear_column = st.columns(2)
    process = process_column.button(
        "Process video", type="primary", use_container_width=True
    )
    clear = clear_column.button("Clear", use_container_width=True)

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
                    "transcript chunks."
                )
            except Exception as exc:
                st.error(f"Could not process the video: {exc}")

    if st.session_state.vector_store is None:
        st.write("Process a video first, then ask questions about its transcript.")
        return

    st.info(
        f"Ready: `{st.session_state.video_id}` · "
        f"{st.session_state.chunk_count} chunks indexed"
    )
    if st.button("Summarize video"):
        if not api_key:
            st.error("The language model service is not configured.")
        else:
            try:
                with st.spinner("Summarizing with Groq..."):
                    summary = summarize_video(
                        st.session_state.transcript, api_key, chat_model
                    )
                st.markdown("### Summary")
                st.write(summary)
            except Exception as exc:
                st.error(f"Could not summarize the video: {exc}")

    render_chat(api_key, chat_model, retrieved_chunks)
