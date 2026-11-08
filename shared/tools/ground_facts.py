#!/usr/bin/env python3
"""Deterministic FACT-SCRATCHPAD — jump-start the DSL model with grounded perception.

Runs the existing `auto_scan`/`suggest` engine on the demos and renders its confidence-ranked
findings as closed-vocab tokens: each PROPERTY token followed by a 2-digit RATING (0-99). These are
FED into the prompt (read, not generated) on the normal task rows so the model writes programs on top
of verified facts (it can't hallucinate the grid size / recolor map if they're sitting in front of
it). A separate ~10% <pred_facts> task asks the model to PREDICT the ratings from the demos alone —
a small perception signal so it isn't fully dependent on the fed facts.

Everything here is deterministic + demo-derived (no test-output leakage, no teacher LLM). Robust by
construction: ANY failure returns empty facts rather than breaking the streamer.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# feature-name (auto_scan) -> claimed property token
FEATURE_TOK = {
    "consistent_mapping": "<p_consistent_map>", "color_roles": "<p_color_roles>",
    "frames": "<p_frames>", "lines": "<p_lines>", "regularity": "<p_regularity>",
    "motion": "<p_motion>", "scattered": "<p_scattered>", "shape_change": "<p_shape_change>",
    "diff": "<p_diff>", "change_type": "<p_change_type>", "object_count_change": "<p_objcount>",
    "enclosure_input": "<p_enclosure>", "lattice_input": "<p_lattice>",
    "symmetry_input": "<p_symmetry>", "periodicity_input": "<p_periodicity>",
}


def _suggest_tok(expr: str):
    """suggest() template expr -> property token (the actionable 'try this rule' hint)."""
    if "recolor_map" in expr:
        return "<p_recolor_map>"
    if "fill_enclosed" in expr:
        return "<p_fill_enclosed>"
    if "complete_symmetry" in expr:
        return "<p_complete_sym>"
    if "upscale" in expr:
        return "<p_upscale>"
    if "recolor" in expr:
        return "<p_recolor_single>"
    return None


def _rating(score: float):
    v = max(0, min(99, round(float(score) * 99)))   # 0-1 confidence -> 2 decimal digits
    return [str(v // 10), str(v % 10)]


def fact_tokens(train_pairs, top_k: int = 10):
    """Property+rating token list (NO delimiters): [<p_x> d d <p_y> d d ...]. [] on any failure."""
    from arc_repl.auto_scan import auto_scan, suggest
    task = {"train": [{"input": p["input"], "output": p["output"]}
                      for p in (train_pairs or []) if p.get("output") is not None]}
    if not task["train"]:
        return []
    props: dict = {}
    try:
        scored, results = auto_scan(task)
        for fname, score, _ in scored:
            tok = FEATURE_TOK.get(fname)
            if tok and score > 0:
                props[tok] = max(props.get(tok, 0.0), score)
        for expr, conf, _ in suggest(task, results):
            tok = _suggest_tok(expr)
            if tok and conf > 0:
                props[tok] = max(props.get(tok, 0.0), conf)
    except Exception:
        return []                       # robust: never break the streamer
    out = []
    for tok, score in sorted(props.items(), key=lambda kv: -kv[1])[:top_k]:
        out.append(tok); out += _rating(score)
    return out


def fed_facts(train_pairs, top_k: int = 10):
    """Delimited FED preamble the model reads before answering: <facts> ... </facts>."""
    return ["<facts>"] + fact_tokens(train_pairs, top_k) + ["</facts>"]
