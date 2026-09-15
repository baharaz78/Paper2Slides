# Paper2Slides

Paper2Slides is a multi-agent system that transforms research papers into concise, editable PowerPoint presentations.

Upload a PDF paper, choose a target slide count, and receive a presentation that summarizes the research while keeping figures, charts, and explanatory text connected.

## Features

- Extracts text, figures, and captions from research-paper PDFs
- Generates presentations with 4 to 10 slides
- Uses multiple specialized agents for:
  - Reading and summarizing the paper
  - Planning the presentation narrative
  - Writing slide content
  - Matching figures with relevant slide text
  - Reviewing factual accuracy
- Adds source-page and figure-caption information to speaker notes
- Produces editable PowerPoint files
- Supports both a command-line interface and a local API

## Project Flow

```text
PDF Paper
  ↓
Text, Figure, and Caption Extraction
  ↓
Research Reader Agent
  ↓
Narrative Planner and Slide Writer
  ↓
Visual Grounding Agent
  ↓
Factual Reviewer
  ↓
Editable PowerPoint Presentation
```

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key
- Node.js with the PowerPoint rendering runtime

## Installation

```bash
git clone git@github.com:baharaz78/Paper2Slides.git
cd Paper2Slides

uv sync
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
```

## Usage

Generate a six-slide presentation from a paper:

```bash
uv run paper2slides article.pdf --slides 6 --language en --output outputs/presentation.pptx
```

Generate a Persian presentation:

```bash
uv run paper2slides article.pdf --slides 6 --language fa --output outputs/presentation-fa.pptx
```

## Local API

Start the local server:

```bash
uv run uvicorn paper2slides.api:app --reload
```

Create a job by uploading a PDF to:

```text
POST /jobs?slide_count=6&language=en
```

Check progress:

```text
GET /jobs/{job_id}
```

Download the completed presentation:

```text
GET /jobs/{job_id}/download
```

## Project Structure

```text
Paper2Slides/
├── src/
│   └── paper2slides/
│       ├── api.py
│       ├── cli.py
│       ├── ingest.py
│       ├── llm.py
│       ├── models.py
│       ├── orchestrator.py
│       └── renderer/
├── tests/
├── pyproject.toml
├── README.md
└── .env.example
```

## Notes

- The system only uses information found in the uploaded paper.
- A figure is added to a slide only when its caption and surrounding context support the slide’s main message.
