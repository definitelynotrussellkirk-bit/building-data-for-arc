from __future__ import annotations

from pathlib import Path
import sys


try:
    from reviewer_support import find_root, load_selected_generator
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import find_root, load_selected_generator


TASK_ID = "8d2ecf358469"
gen, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))


def test_every_six_pair_lesson_survives_query_rotation():
    """Any one of the six materialized pairs may become the held-out query."""
    assert gen.VERSION == "2.1.0"
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            pairs = []
            for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(2801 + start, index, difficulty=difficulty)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    query_index,
                    [
                        gen.observe_overrides(pair["input"])["area_profile"]
                        for pair in pairs
                    ],
                )
