"""Behavioral regressions for witnesses missing from the original sampler."""
from __future__ import annotations

from reviewer_support import find_root, load_selected_generator


gen, _, _ = load_selected_generator("a55c1997c5e3", root=find_root(__file__))


def test_production_support_refutes_every_canonical_fit_shortcut():
    period = getattr(gen, "LESSON_SCHEDULE_PERIOD", len(gen.SCENE_PROFILES))
    grids = [gen.generate(17, i, difficulty="medium") for i in range(period)]
    pairs = [(grid, gen._official_python_mirror(grid)) for grid in grids]
    assert gen.CANONICAL_SHORTCUTS, "retain executable canonical-fit rivals"
    missing = [
        name for name, rival in gen.CANONICAL_SHORTCUTS.items()
        if all(rival(grid) == output for grid, output in pairs)
    ]
    assert not missing, f"ordinary generated support never refutes {missing}"


def test_every_declared_schedule_start_and_query_rotation_is_teachable():
    period = getattr(gen, "LESSON_SCHEDULE_PERIOD", len(gen.SCENE_PROFILES))
    demos = gen.EXAMPLES_NEEDED
    for band in ("easy", "medium", "hard"):
        # Independent fixed seeds; authoritative Racket coverage is retained by
        # the public lesson census, while this fast regression uses the mirror.
        for seed in (0, 17):
            pairs = []
            for i in range(period + demos):
                grid = gen.generate(seed, i, difficulty=band)
                pairs.append({"input": grid, "output": gen._official_python_mirror(grid)})
            for start in range(period):
                lesson = pairs[start:start + demos + 1]
                for query_index, query in enumerate(lesson):
                    train = lesson[:query_index] + lesson[query_index + 1:]
                    reasons = gen.lesson_identifiable(train, query)
                    assert not reasons, (band, seed, start, query_index, reasons)
