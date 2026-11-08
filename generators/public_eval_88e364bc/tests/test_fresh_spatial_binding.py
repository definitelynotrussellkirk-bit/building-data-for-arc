"""The minimum lesson must distinguish color binding from spatial shortcuts."""
from pathlib import Path
import importlib.util

import pytest

HOME = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sources():
    return (load(HOME / "generator.py", "fresh_binding_base"),
            load(HOME / "workspace/parametric/adapter.py", "fresh_binding_adapter"))


def positional_prediction(base, grid, mode, policy):
    """Share only scene parsing; deliberately replace wall-keyed association."""
    parsed = base.parse(grid)
    result = [row[:] for row in grid]
    for r, c in parsed["tokens"]:
        result[r][c] = 0
    for region in parsed["regions"]:
        cells = {tuple(p) for p in region["cells"]}
        center = tuple(sum(p[axis] for p in cells) / len(cells) for axis in (0, 1))

        def distance(legend):
            r0, c0, r1, c1 = legend["bounds"]
            return (center[0] - (r0 + r1) / 2) ** 2 + (center[1] - (c0 + c1) / 2) ** 2

        chooser = min if policy == "nearest" else max
        legend = chooser(parsed["legends"], key=distance)
        dr, dc = legend["direction"]
        if mode == "toward_tail":
            dr, dc = -dr, -dc
        for r, c in region["tokens"]:
            while ((r + dr, c + dc) in cells and
                   (not dr or not dc or ((r + dr, c) in cells and (r, c + dc) in cells))):
                r, c = r + dr, c + dc
            result[r][c] = 4
    return result


@pytest.mark.parametrize("seed", [0, 9223372036854775807])
@pytest.mark.parametrize("mode", ["toward_head", "toward_tail"])
@pytest.mark.parametrize("policy", ["nearest", "farthest"])
def test_two_demos_reject_positional_binding(sources, seed, mode, policy):
    base, adapter = sources
    lesson = adapter.generate(seed, {"motion": mode}, demos=2, queries=4)
    rejected = [i for i, pair in enumerate(lesson["train"])
                if positional_prediction(base, pair["input"], mode, policy) != pair["output"]]
    assert rejected, (seed, mode, policy)
