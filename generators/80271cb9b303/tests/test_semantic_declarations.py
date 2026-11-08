from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "generators" / "80271cb9b303" / "generator.py"
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"

if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "generator_80271cb9b303_semantic_declarations_test", GENERATOR_PATH
)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_canonical_shortcuts_are_exactly_the_rivals_that_fit_every_canonical_pair():
    pairs = canonical_pairs(
        gen.TASK_ID,
        root=find_root(__file__),
        labeled_only=True,
    )
    expected = {
        name
        for name, rival in gen.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    }

    assert expected == set()
    assert set(gen.CANONICAL_SHORTCUTS) == expected


def test_lesson_competitors_still_include_every_declared_semantic_rival():
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)
