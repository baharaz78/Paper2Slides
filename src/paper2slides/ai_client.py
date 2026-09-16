import os

from dotenv import load_dotenv
from ollama import Client

MAX_ARTICLE_CHARACTERS = 30_000


def get_ollama_client() -> Client:
    """Create a client for the locally running Ollama server"""
    load_dotenv()

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    return Client(host=host)


def summarize_article(title: str, text: str, language: str) -> str:
    """Ask the research-reader agent to summarize an article"""
    client = get_ollama_client()
    model = os.getenv("OLLAMA_MODEL", "qwen3:4b")

    article_text = text[:MAX_ARTICLE_CHARACTERS]

    response = client.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a research reader. "
                    "Summarize the supplied academic paper accurately. "
                    "Include the research question, method, main findings, "
                    "and limitations. Do not invent facts or numbers. "
                    f"Write the answer in {language}."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Article title: {title}\n\n"
                    f"Article text:\n{article_text}"
                ),
            },
        ],
    )

    return response.message.content
