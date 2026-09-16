import json
import os
from copy import deepcopy
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

PRESENTATION_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "presentation_title": {
            "type": "string",
        },
        "slides": {
            "type": "array",
            "minItems": 4,
            "maxItems": 10,
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                    },
                    "key_message": {
                        "type": "string",
                    },
                    "bullets": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 4,
                        "items": {
                            "type": "string",
                        },
                    },
                    "image_path": {
                        "type": ["string", "null"],
                    },
                    "image_explanation": {
                        "type": "string",
                    },
                },
                "required": [
                    "title",
                    "key_message",
                    "bullets",
                    "image_path",
                    "image_explanation",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "presentation_title",
        "slides",
    ],
    "additionalProperties": False,
}


def get_language_instruction(language: str) -> str:
    """Return a clear natural language instruction for output language"""
    language_instruction = {
        "fa": (
            "Persian (Farsi), written entirely in Persian script. "
            "Do not write English except for unavoidable proper nouns."
        ),
        "en": "English",
    }

    return language_instruction.get(language, language)


def get_ollama_client() -> Client:
    """Create a client for the locally running Ollama server"""
    load_dotenv()

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    return Client(host=host)


def summarize_article(title: str, text: str, language: str) -> dict[str, Any]:
    """Ask a local research-reader agent for a structured summary"""
    client = get_ollama_client()
    model = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    language_instruction = get_language_instruction(language)

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
                    f"Write all JSON values in {language_instruction}."
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


def plan_presentation(
        summary: dict[str, Any], images: list[dict[str, Any]], slide_count: int, language: str,
) -> dict[str, Any]:
    """Ask the planner agent to create a structured slide plan"""
    client = get_ollama_client()
    model = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    language_instruction = get_language_instruction(language)

    planning_input = json.dumps(
        {
            "research_summary": summary,
            "candidate_images": images,
            "requested_slide_count": slide_count,
        },
        ensure_ascii=False,
        indent=2,
    )

    presentation_schema = deepcopy(PRESENTATION_PLAN_SCHEMA)
    slides_schema = presentation_schema["properties"]["slides"]
    slides_schema["minItems"] = slide_count
    slides_schema["maxItems"] = slide_count

    response = client.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a presentation planner. "
                    "Create an academic presentation plan from the supplied "
                    "research summary and candidate images. "
                    "Use exactly the requested number of slides. "
                    "Use only the supplied image paths. "
                    "Choose an image only when its caption supports the "
                    "slide's key message. "
                    "If no image is relevant, use null for image_path. "
                    "Do not invent facts or numbers. "
                    "Return only valid JSON, with no markdown or extra text. "
                    f"Write all JSON values in {language_instruction}."
                ),
            },
            {
                "role": "user",
                "content": planning_input,
            },
        ],
        format=presentation_schema,
        options={
            "temperature": 0,
        },
    )

    try:
        presentation_plan = json.loads(response.message.content)
    except json.JSONDecodeError as err:
        raise RuntimeError(
            "The local model did not return a valid presentation plan."
        ) from err

    if len(presentation_plan["slides"]) != slide_count:
        raise RuntimeError(
            f"Expected {slide_count} slides, but received {len(presentation_plan["slides"])}"
        )

    return presentation_plan


def review_presentation_plan(
        presentation_plan: dict[str, Any], images: list[dict[str, Any]], language: str
) -> dict[str, Any]:
    """Review image choices and their relationship to each slide"""
    client = get_ollama_client()
    model = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    language_instruction = get_language_instruction(language)

    slide_count = len(presentation_plan["slides"])

    review_input = json.dumps(
        {
            "presentation_plan": presentation_plan,
            "candidate_images": images,
        },
        ensure_ascii=False,
        indent=2,
    )

    presentation_schema = deepcopy(PRESENTATION_PLAN_SCHEMA)

    slides_schema = presentation_schema["properties"]["slides"]
    slides_schema["minItems"] = slide_count
    slides_schema["maxItems"] = slide_count

    response = client.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a visual reviewer for academic presentations. "
                    "Review every slide in the supplied presentation plan. "
                    "Keep an image only when its caption clearly supports "
                    "the slide's key message. "
                    "If an image is not relevant, set image_path to null. "
                    "When an image is used, image_explanation must clearly "
                    "explain the relationship between the image and the "
                    "slide text. "
                    "Use only the supplied image paths. "
                    "Do not invent facts or numbers. "
                    "Keep the same number of slides. "
                    "Return only valid JSON, with no markdown or extra text. "
                    f"Write all JSON values in {language_instruction}."
                ),
            },
            {
                "role": "user",
                "content": review_input,
            },
        ],
        format=presentation_schema,
        options={
            "temperature": 0,
        },
    )

    try:
        reviewed_plan = json.loads(response.message.content)
    except json.JSONDecodeError as err:
        raise RuntimeError(
            "The visual reviewer did not return valid JSON"
        ) from err

    if len(reviewed_plan["slides"]) != slide_count:
        raise RuntimeError(
            "The visual reviewer changed the number of slides"
        )

    valid_paths = {
        image["path"]
        for image in images
    }

    for slide in reviewed_plan["slides"]:
        image_path = slide["image_path"]

        if image_path is not None and image_path not in valid_paths:
            slide["image_path"] = None
            slide["image_explanation"] = (
                "No verified related image was selected"
            )

    return reviewed_plan
