# ScholarGuard 🧠

Separating Human Insight from Machine Output

## Overview

ScholarGuard is a mini web app and Chrome Extension that labels Google Scholar results as Human / Mixed / AI and provides a chatbot-like UI to fetch human-authored papers by topic (using a local mock dataset for hackathon demo).

## Project Structure

- `backend/` Flask API with mock datasets
  - `app.py` – endpoints `/health`, `/detect`, `/papers`
  - `data/labels.json` – curated labels for some titles
  - `data/papers.json` – list of papers with metadata
- `frontend/` Simple web UI for the chatbot
- `extension/` Chrome MV3 extension (badges + internal chat page)

## Prereqs
- Python 3.10+
- Chrome (or Chromium-based browser)

## Run Backend API

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/app.py
```

API runs at `http://127.0.0.1:5000`.

Endpoints:
- `GET /health` – health check
- `POST /detect` – body `{ "title": "..." }` => `{ label, confidence, explanation }`
- `GET /papers?topic=ai%20ethics&includeMixed=false&limit=5` – ranked filtered results

## Run Frontend (Static)
Open `frontend/index.html` in a browser (API must be running). The page calls `http://127.0.0.1:5000` by default.

## Install Extension
1. Visit `chrome://extensions`
2. Enable Developer mode
3. Load unpacked → choose the `extension/` folder
4. Open Google Scholar (`https://scholar.google.com`) – badges appear near titles
5. Click the extension icon → Open Chatbot (opens extension's `chat.html`)

Note: The extension content script calls `http://127.0.0.1:5000/detect`. Ensure the API is running. If CORS/network restrictions arise, keep the backend on localhost and reload.

## Demo Flow
- Browse Google Scholar and see 🟢 Human, 🟠 Mixed, 🔴 AI badges
- Open the chatbot and ask: "Show me human-written papers on AI ethics"
- Receive labeled papers with summaries and links

## Notes
- Detection uses a curated `labels.json` where available, falling back to a lightweight heuristic.
- Replace with a real detector later (e.g., GPTZero or custom model) without changing the UI.