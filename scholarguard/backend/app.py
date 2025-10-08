import json
import os
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LABELS_PATH = os.path.join(DATA_DIR, "labels.json")
PAPERS_PATH = os.path.join(DATA_DIR, "papers.json")


def normalize_title(text: str) -> str:
    return (text or "").strip().lower()


def build_labels_index(labels_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for entry in labels_list:
        title = normalize_title(entry.get("title", ""))
        if title:
            index[title] = entry
    return index


labels_list: List[Dict[str, Any]] = []
papers_list: List[Dict[str, Any]] = []
labels_index: Dict[str, Dict[str, Any]] = {}


def load_datasets() -> None:
    global labels_list, papers_list, labels_index
    labels_list = _load_json(LABELS_PATH)
    papers_list = _load_json(PAPERS_PATH)
    labels_index = build_labels_index(labels_list)


def match_label_for_text(text: str) -> Optional[Dict[str, Any]]:
    """Try exact title match then substring heuristic against known labels."""
    if not text:
        return None
    needle = normalize_title(text)
    if needle in labels_index:
        return labels_index[needle]
    # Substring heuristic
    best: Optional[Tuple[int, Dict[str, Any]]] = None
    for title_key, entry in labels_index.items():
        if title_key in needle or needle in title_key:
            # Prefer longer matching titles
            match_score = max(len(title_key), len(needle))
            if best is None or match_score > best[0]:
                best = (match_score, entry)
    return best[1] if best else None


def heuristic_label(text: str) -> Dict[str, Any]:
    lower = (text or "").lower()
    ai_cues = ["gpt", "chatgpt", "llm", "ai-written", "prompt-engineering", "hallucination"]
    mixed_cues = ["assisted", "ai-assisted", "co-authored with ai"]
    if any(cue in lower for cue in ai_cues):
        return {
            "label": "ai",
            "confidence": 0.65,
            "explanation": "Detected AI-related phrasing and cues typical of machine-generated text.",
        }
    if any(cue in lower for cue in mixed_cues):
        return {
            "label": "mixed",
            "confidence": 0.6,
            "explanation": "Signals indicate collaboration between human authors and AI tools.",
        }
    return {
        "label": "human",
        "confidence": 0.6,
        "explanation": "Defaulting to human based on writing style and lack of AI cues.",
    }


def score_paper_against_topic(paper: Dict[str, Any], topic: str) -> int:
    if not topic:
        return 0
    topic_l = topic.lower()
    score = 0
    for field in (paper.get("title", ""), paper.get("summary", "")):
        text = (field or "").lower()
        for token in topic_l.split():
            if token and token in text:
                score += 1
    for kw in paper.get("keywords", []) or []:
        if kw and kw.lower() in topic_l:
            score += 1
    return score


@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok"})


@app.route("/detect", methods=["POST"])
def detect() -> Any:
    payload = request.get_json(silent=True) or {}
    text = payload.get("title") or payload.get("abstract") or payload.get("text")
    if not text:
        return jsonify({
            "error": "Missing 'title' or 'abstract' in request body.",
        }), 400

    mapped = match_label_for_text(text)
    if mapped:
        return jsonify({
            "label": mapped.get("label", "mixed"),
            "confidence": mapped.get("confidence", 0.75),
            "explanation": mapped.get("explanation", "Label derived from curated dataset."),
        })

    result = heuristic_label(text)
    return jsonify(result)


@app.route("/papers", methods=["GET"])
def papers() -> Any:
    topic = (request.args.get("topic") or "").strip()
    try:
        limit = int(request.args.get("limit", "5"))
    except ValueError:
        limit = 5
    include_mixed = (request.args.get("includeMixed", "false").lower() == "true")

    # Label each paper using dataset or heuristic, then filter and rank
    annotated: List[Dict[str, Any]] = []
    for p in papers_list:
        paper = dict(p)
        title = paper.get("title", "")
        mapped = match_label_for_text(title)
        if mapped:
            paper["label"] = mapped.get("label", paper.get("label", "mixed"))
            paper["explanation"] = mapped.get("explanation", paper.get("explanation"))
        else:
            heuristic = heuristic_label(title)
            paper["label"] = heuristic["label"]
            paper["explanation"] = heuristic["explanation"]
        annotated.append(paper)

    filtered = [p for p in annotated if p.get("label") == "human" or (include_mixed and p.get("label") == "mixed")]
    if topic:
        filtered.sort(key=lambda p: score_paper_against_topic(p, topic), reverse=True)
    else:
        # Prefer newer papers first if no topic
        filtered.sort(key=lambda p: p.get("year", 0), reverse=True)

    return jsonify({
        "topic": topic,
        "count": min(limit, len(filtered)),
        "results": filtered[:limit],
    })


def create_app() -> Flask:
    load_datasets()
    return app


if __name__ == "__main__":
    load_datasets()
    app.run(host="127.0.0.1", port=5000, debug=True)

