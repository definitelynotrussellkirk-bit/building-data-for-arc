"""Replay the bounded audit from WORK; run with PYTHONPATH=repo/shared/runtime."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs


parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=Path, default=Path("repo"))
args = parser.parse_args()
source = args.repo / "generators/53849ea2e4ac/generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", source)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def aggregate_color_rival(grid):
    counts = Counter(c for row in grid for c in row if c)
    return [[c for c in sorted(counts, key=lambda c: (counts[c], c))]]


pairs = canonical_pairs(generator.TASK_ID, root=args.repo)
assert len(pairs) == 5
assert all(aggregate_color_rival(p["input"]) == p["output"] for p in pairs)
base = generator.generate(11, 0, difficulty="medium")
assert len({c for row in base for c in row if c}) == 5
for override in (
    {"palette_size": 1}, {"n_distinct_colors": 1},
    {"palette_kind": "warm"}, {"texture": "cool"}, {"unknown_axis": 9},
):
    assert generator.generate(11, 0, difficulty="medium", **override) == base

for override in ({"grid_h": 7}, {"grid_w": 16}, {"n_blobs": 2}, {"n_blobs": 6}):
    try:
        generator.generate(11, 0, difficulty="medium", **override)
    except ValueError:
        pass
    else:
        raise AssertionError(f"Expected observed declared-range rejection: {override}")

repeated_color = [[1, 0, 0, 2, 2], [0, 0, 0, 0, 0], [1, 1, 1, 0, 0]]
assert generator.self_check(repeated_color) == []
assert aggregate_color_rival(repeated_color) == [[2, 1]]
assert generator.self_check([[True, 10], [-1, 0]]) == []

receipt = json.loads((Path(__file__).resolve().parent / "racket.json").read_text())
assert receipt["generator_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
assert all(not item["error"] for item in receipt["results"])
assert all(receipt["results"][i]["output"] == p["output"] for i, p in enumerate(pairs))
assert receipt["results"][5]["input"] == repeated_color
assert receipt["results"][5]["output"] == [[1, 2, 1]]
print("Audit reproduced: 5 canonical rival fits; inert/rejected controls; repeated-color Racket witness; weak validator.")
