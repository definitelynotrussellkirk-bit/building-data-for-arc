"""Keep actual Racket-labeled teaching failures available in the portable task."""
import importlib.util
import json

import pytest
from reviewer_support import find_root


ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / "c7070676c606"
SPEC = importlib.util.spec_from_file_location("retained_teaching_generator", TASK_HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
FIXTURES = json.loads((TASK_HOME / "counterexamples" / "teaching_failures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["cases"], ids=lambda case: case["id"])
def test_actual_before_lessons_remain_recognized_as_ambiguous(case):
    """The repair changes future sampling, while the old failures stay detectable."""
    assert FIXTURES["rule_source_sha256"].startswith(GEN.RULE_HASH)
    demos, query = case["demos"], case["query"]
    assert len(demos) == 3
    assert all(GEN.self_check(pair["input"]) == [] for pair in demos + [query])
    reasons = GEN.lesson_identifiable(demos, query)
    for name in case["rivals"]:
        rival = GEN.LESSON_COMPETITORS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in demos)
        assert rival(query["input"]) != query["output"]
        assert any(name in reason for reason in reasons)
