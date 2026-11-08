"""Racket-labelled lesson that a spatial key shortcut used to escape."""
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("b4ecb537757c", root=ROOT)

def test_retained_spatial_key_shortcut_is_reported():
    fixture = json.loads((ROOT / "generators/b4ecb537757c/workspace/cyclic_key_lesson.json").read_text())
    pairs, query_index = fixture["pairs"], fixture["query_index"]
    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
    errors = GEN.lesson_identifiable(demos, pairs[query_index])
    assert any(fixture["rival"] in error for error in errors), errors
