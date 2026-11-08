from pathlib import Path
import importlib.util
import pytest
from reviewer_support import canonical_pairs, find_root
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("audited_" + Path(__file__).parents[1].name, Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

def test_production_and_rotated_lessons_refute_single_color():
    rival = GEN.LESSON_COMPETITORS["complete_only_one_color"]
    for band in ("easy", "medium", "hard"):
        pairs = [{"input": GEN.generate(0,i,difficulty=band)} for i in range(65)]
        for p in pairs:
            p["output"] = GEN.rule_mirror(p["input"])
        for start in range(62):
            window = pairs[start:start+4]
            for q in range(4):
                demos = window[:q]+window[q+1:]
                assert GEN.lesson_identifiable(demos, window[q]) == []
                assert any(rival(p["input"]) != p["output"] for p in demos)
