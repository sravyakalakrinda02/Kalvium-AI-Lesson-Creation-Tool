# LessonCraft AI — Kalvium AI Research Intern Task

A local Streamlit prototype that researches a lesson topic, generates a 45-minute lesson, runs two separate quality-control audits, and lets an instructor edit, save and export the result.

## Features
- Lesson title and learning-objective inputs.
- Research leads from DuckDuckGo Instant Answer, Open Library book catalogue and YouTube search.
- AI-generated structured 45-minute lesson with explanations, examples, activities, knowledge check and references.
- Independent QC Layer 1: research/factual accuracy, source reliability and evidence gaps.
- Independent QC Layer 2: instructional quality and objective alignment.
- Instructor editing, local JSON save, Markdown preview and ZIP export containing lesson, references and both QC reports.
- Input validation and retry-friendly error handling; the app does not overwrite an existing saved lesson during a failed generation attempt.

## Requirements
- Python 3.10+
- Internet access for research endpoints
- Google Gemini API key for lesson generation and both QC audits (API usage may incur charges)

## Setup (Windows / macOS / Linux)

```bash
python -m venv .venv
```

Activate the environment:

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install packages:
```bash
pip install -r requirements.txt
```

Create a `.env` file by copying `.env.example`, then add your own API key:
```env
GEMINI_API_KEY=your_key_here
OPENAI_MODEL=gemini-3.5-flash-lite
```

Run:
```bash
streamlit run app.py
```

## Required test cases
1. **HTTP Requests and Responses** — Explain GET and POST methods and distinguish between 2xx, 4xx and 5xx response status categories.
2. **Python Functions** — Define functions, explain parameters and return values, and write a reusable function to solve a simple problem.

For each test, generate a lesson, inspect references, review both QC reports, edit at least one field, save, and export the ZIP package. Capture these steps in the demo video.

## Research and accuracy limitations
The app gathers public research leads. Open Library is a catalogue, not the full text of a book. The YouTube integration provides a targeted YouTube search page rather than asserting that a specific video has been reviewed. DuckDuckGo's instant-answer endpoint may return sparse results; the app includes a search link fallback. The QC model is instructed to distinguish supplied leads from verified evidence. An instructor must open and verify important sources and claims before treating the lesson as publication-ready.

## Architecture
- `app.py`: Streamlit UI, state, editing, save and export workflow.
- `research.py`: web, book-catalogue and YouTube research helpers.
- `lesson_engine.py`: lesson generation and two independent QC prompts.
- `exports.py`: Markdown rendering and complete ZIP package.

## Responsible use
Keep API keys private. Do not commit `.env` to GitHub. Cite and acknowledge all external resources. AI-generated material and QC reports require human review.


## Gemini free-tier setup
1. Create a key in Google AI Studio: https://aistudio.google.com/apikey
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Run `streamlit run app.py`.
4. Paste the key into the Google Gemini API key field. The default model is `gemini-3.5-flash-lite`; free-tier availability and quotas are controlled by Google and can change. Do not commit your API key or share it.
