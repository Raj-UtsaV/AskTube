# AskTube Project Documentation

## 1. Project Overview

AskTube is a Retrieval-Augmented Generation (RAG) application that allows users
to ask questions about YouTube videos and generate concise video summaries. The
application extracts the available transcript, converts it into searchable text
representations, retrieves the most relevant sections for a question, and uses a
large language model to produce an answer grounded in the video content.

The project provides a simple Streamlit interface and supports standard YouTube
URLs, Shorts URLs, embed URLs, and raw video IDs.

## 2. Problem Statement

Long videos often contain useful information that is difficult to locate without
watching the complete recording. Manual searching is slow, and general-purpose
language models may answer using outside knowledge instead of the video's actual
content.

AskTube addresses this problem by turning a YouTube transcript into a searchable
knowledge source. It retrieves relevant transcript sections before generating a
response, helping users find information quickly while keeping answers connected
to the selected video.

## 3. Objectives

- Extract transcripts from supported YouTube videos.
- Convert transcript chunks into semantic embeddings.
- Retrieve the most relevant chunks for each user question.
- Generate answers using only the retrieved transcript context.
- Summarize both short and long video transcripts.
- Provide an accessible and interactive web interface.
- Support local execution and Streamlit Community Cloud deployment.

## 4. Key Features

- Question answering based on YouTube transcript content
- Concise video summary generation
- Support for eight transcript languages
- Semantic retrieval using Hugging Face embeddings and FAISS
- Display of the transcript chunks used to generate each answer
- Session-based conversation history
- Support for multiple common YouTube URL formats
- Environment-based configuration for secure API key management

## 5. Technology Stack

| Technology | Purpose |
| --- | --- |
| Python | Core application development |
| Streamlit | Interactive web interface |
| LangChain | Prompt, retrieval, and generation pipeline |
| Groq | Large language model inference |
| Hugging Face | Cloud-based text embeddings |
| FAISS | Local vector storage and similarity search |
| YouTube Transcript API | Transcript extraction |
| GitHub Actions | Automated unit testing |

## 6. System Architecture

```text
YouTube URL or Video ID
          |
          v
  Transcript Extraction
          |
          v
     Text Chunking
          |
          v
Hugging Face Embeddings
          |
          v
    FAISS Vector Store
          |
          v
     User Question
          |
          v
   Similarity Retrieval
          |
          v
    Relevant Context
          |
          v
      Groq LLM
          |
          v
   Grounded Response
```

## 7. Application Workflow

### 7.1 Video processing

1. The user enters a YouTube URL or an 11-character video ID.
2. The application validates the input and extracts the video ID.
3. The YouTube Transcript API retrieves the transcript in the selected language.
4. LangChain splits the transcript into overlapping text chunks.
5. Hugging Face generates an embedding for each chunk.
6. FAISS indexes the embeddings for similarity-based retrieval.

### 7.2 Question answering

1. The user submits a question through the chat interface.
2. The question is compared with the indexed transcript chunks.
3. FAISS returns the most semantically relevant sections.
4. LangChain inserts the retrieved text into a structured prompt.
5. Groq generates a concise answer using only the supplied context.
6. The answer and supporting transcript chunks are shown to the user.

### 7.3 Video summarization

For shorter transcripts, AskTube sends the transcript directly through the
summary pipeline. Longer transcripts are divided into larger sections and
summarized individually. The partial summaries are then combined into a final
overview with key points.

## 8. Project Structure

```text
AskTube/
|-- .github/workflows/tests.yml
|-- .streamlit/config.toml
|-- assets/asktube-banner.png
|-- tests/
|   |-- test_rag.py
|   `-- test_youtube.py
|-- src/
|   |-- services/
|   |   |-- rag.py
|   |   `-- youtube.py
|   |-- config.py
|   `-- ui.py
|-- .env.example
|-- .gitignore
|-- app.py
|-- README.md
`-- requirements.txt
```

## 9. Installation and Setup

### Prerequisites

- Python 3.12 or later
- A Groq API key
- A Hugging Face API token
- A YouTube video with an available transcript

### Installation

```bash
git clone https://github.com/Raj-UtsaV/AskTube.git
cd AskTube
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

### Configuration

Create a local environment file from the provided template:

```bash
cp .env.example .env
```

Add the required credentials:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACEHUB_API_TOKEN=your_hugging_face_token
```

The `.env` file is ignored by Git and must not be committed.

### Running the application

```bash
streamlit run app.py
```

Open the local URL displayed by Streamlit, enter a YouTube video, and select
**Process video**. Once indexing is complete, questions and summaries can be
generated from the transcript.

## 10. Testing

Run the unit tests with:

```bash
python -m unittest discover -s tests -v
```

The current tests verify transcript text splitting and supported YouTube URL and
video ID formats. GitHub Actions runs the same test suite after pushes and pull
requests.

## 11. Security and Privacy

- API credentials are loaded from environment variables or Streamlit secrets.
- Local `.env` and Streamlit secrets files are excluded through `.gitignore`.
- The vector store remains in the active application session and is not saved to
  a permanent database.
- Users should avoid processing private or sensitive video transcripts through
  third-party inference services without reviewing the providers' data policies.

## 12. Limitations

- A video must have an accessible transcript.
- YouTube may restrict transcript requests from some cloud-hosted environments.
- Answer quality depends on transcript quality and retrieval relevance.
- Automatic speech recognition errors may affect generated responses.
- Very long videos require multiple model calls during summarization.
- The application does not currently preserve conversations between sessions.

## 13. Future Scope

- Add support for uploaded audio, video, and transcript files.
- Include timestamps and links to relevant moments in the video.
- Cache processed videos to reduce repeated embedding requests.
- Add multilingual questions independent of transcript language.
- Support persistent chat history and saved video collections.
- Add retrieval and response quality evaluation metrics.

## 14. Conclusion

AskTube demonstrates how RAG can make long-form video content easier to explore.
By combining transcript extraction, semantic search, and grounded language model
generation, the application gives users a practical way to understand videos
without manually searching through the entire recording.

## 15. Repository

[GitHub - AskTube](https://github.com/Raj-UtsaV/AskTube)
