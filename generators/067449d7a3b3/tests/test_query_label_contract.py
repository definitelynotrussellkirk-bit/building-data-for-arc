"""The labeled-query hook must reject a corrupt private answer."""
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


def test_lesson_hook_rejects_corrupted_query_label():
    gen, _, _ = load_selected_generator(
        "067449d7a3b3", root=find_root(Path(__file__))
    )
    grids = [gen.generate(91, index) for index in range(4)]
    pairs = [{"input": grid, "output": gen._mirror(grid)} for grid in grids]
    demos, query = pairs[:3], pairs[3]
    assert gen.lesson_identifiable(demos, query) == []
    assert gen.lesson_identifiable(demos, {"input": query["input"]}) == []

    corrupted = [row[:] for row in query["output"]]
    corrupted[0][0] = (corrupted[0][0] + 1) % 10
    findings = gen.lesson_identifiable(demos, {**query, "output": corrupted})
    assert any("query output disagrees" in reason for reason in findings), findings
