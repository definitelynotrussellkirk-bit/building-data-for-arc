from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from reviewer_support import find_root, load_selected_generator
from reproduce_underidentified_lesson import find_underidentified_lesson


def test_labels_are_correct_but_cross_query_lesson_is_underdetermined():
    root = find_root(__file__)
    generator, _source, _digest = load_selected_generator("4d5bb3c0250b", root=root)
    lesson = find_underidentified_lesson(generator, max_attempts=512)

    assert len(lesson["train"]) == 3
    assert len(lesson["test"]) == 1
    all_inputs = [pair["input"] for pair in lesson["train"] + lesson["test"]]
    assert len({repr(grid) for grid in all_inputs}) == 4

    for pair in lesson["train"] + lesson["test"]:
        assert generator.rule_mirror(pair["input"]) == pair["output"]

    reasons = generator.lesson_identifiable(
        lesson["train"], {"input": lesson["test"][0]["input"]}
    )
    assert reasons == [
        "demonstrations remain consistent with shortcut: crop_top_left_block"
    ]
    query = lesson["test"][0]
    assert generator._crop_top_left_block(query["input"]) != query["output"]
