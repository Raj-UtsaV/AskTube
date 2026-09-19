from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from langchain_groq import ChatGroq

SUMMARY_CHUNK_SIZE = 12_000


def _is_vector(value) -> bool:
    return isinstance(value, list) and all(
        isinstance(number, (int, float)) for number in value
    )


def _normalize(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(number * number for number in vector))
    return [number / length for number in vector] if length else vector


def _mean_pool(token_vectors: list[list[float]]) -> list[float]:
    if not token_vectors:
        return []

    return [
        sum(token_vector[index] for token_vector in token_vectors) / len(token_vectors)
        for index in range(len(token_vectors[0]))
    ]


def _as_vectors(result) -> list[list[float]]:
    data = result.tolist() if hasattr(result, "tolist") else result
    if not data:
        return []

    if _is_vector(data):
        return [_normalize(data)]

    vectors = []
    for item in data:
        vector = item if _is_vector(item) else _mean_pool(item)
        vectors.append(_normalize(vector))
    return vectors


def build_vector_store(
    transcript: str,
    embedding_model: str,
    huggingface_api_token: str = "",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> tuple[FAISS, int]:
    """Split a transcript, create embeddings, and build FAISS."""
    from huggingface_hub import InferenceClient
    from langchain_community.vectorstores import FAISS
    from langchain_core.embeddings import Embeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    class HuggingFaceCloudEmbeddings(Embeddings):
        def __init__(self, model_name: str, api_token: str) -> None:
            self.client = InferenceClient(model=model_name, token=api_token)

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return _as_vectors(self.client.feature_extraction(texts))

        def embed_query(self, text: str) -> list[float]:
            return self.embed_documents([text])[0]

    documents = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    ).create_documents([transcript])
    embeddings = HuggingFaceCloudEmbeddings(
        embedding_model,
        huggingface_api_token,
    )

    return FAISS.from_documents(documents, embeddings), len(documents)


def get_llm(api_key: str, chat_model: str) -> ChatGroq:
    from langchain_groq import ChatGroq

    return ChatGroq(api_key=api_key, model=chat_model, temperature=0.2)


def answer_question(
    question: str,
    vector_store: FAISS,
    api_key: str,
    chat_model: str,
    k: int = 4,
) -> tuple[str, list[Document]]:
    """Retrieve relevant transcript chunks and answer with Groq."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    docs = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    ).invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer the question using only the supplied YouTube transcript "
                "context. If the answer is not supported by the context, say: "
                "'I don't know from this video.' Keep the answer clear and concise.",
            ),
            ("human", "Transcript context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | get_llm(api_key, chat_model) | StrOutputParser()

    return chain.invoke({"context": context, "question": question}), docs


def _split_text(text: str, chunk_size: int = SUMMARY_CHUNK_SIZE) -> list[str]:
    return [
        text[index : index + chunk_size]
        for index in range(0, len(text), chunk_size)
        if text[index : index + chunk_size].strip()
    ]


def _summarize_text(text: str, api_key: str, chat_model: str, prompt_text: str) -> str:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_text),
            ("human", "Transcript:\n{text}"),
        ]
    )
    chain = prompt | get_llm(api_key, chat_model) | StrOutputParser()

    return chain.invoke({"text": text})


def summarize_video(transcript: str, api_key: str, chat_model: str) -> str:
    """Generate a concise summary with Groq."""
    chunks = _split_text(transcript)
    if len(chunks) == 1:
        return _summarize_text(
            chunks[0],
            api_key,
            chat_model,
            "Summarize the supplied YouTube transcript using only its content. "
            "Give a short overview followed by 5-8 key points.",
        )

    partial_summaries = [
        _summarize_text(
            chunk,
            api_key,
            chat_model,
            "Summarize this section of a YouTube transcript using only its content. "
            "Keep it concise and preserve important details.",
        )
        for chunk in chunks
    ]
    return _summarize_text(
        "\n\n".join(partial_summaries),
        api_key,
        chat_model,
        "Combine these section summaries into one video summary. Give a short "
        "overview followed by 5-8 key points. Do not add outside information.",
    )
