import json
import os
from typing import Any

from dotenv import load_dotenv
from ollama import Client

MAX_ARTICLE_CHARACTERS = 30_000

RESEARCH_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "research_question": {
            "type": "string",
        },
        "method": {
            "type": "string",
        },
        "main_finding": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "limitations": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "research_question",
        "method",
        "main_finding",
        "limitations"
    ],
    "additionalProperties": False,
}


def get_ollama_client() -> Client:
    """Create a client for the locally running Ollama server"""
    load_dotenv()

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    return Client(host=host)


def summarize_article(title: str, text: str, language: str) -> dict[str, Any]:
    """Ask a local research-reader agent for a structured summary"""
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
        format=RESEARCH_SUMMARY_SCHEMA,
        options={
            "temperature": 0,
        },
    )

    try:
        return json.loads(response.message.content)
    except json.JSONDecodeError as err:
        raise RuntimeError(
            "The local model did not return valid JSON"
        ) from err
