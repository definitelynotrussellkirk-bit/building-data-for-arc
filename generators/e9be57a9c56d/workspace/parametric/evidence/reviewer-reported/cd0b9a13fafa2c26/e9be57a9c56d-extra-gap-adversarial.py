from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import time

from reviewer_support import public_challenge_id

HERE = Path(__file__).resolve()
REPO = HERE.parents[1] / "repo"
PROTOTYPE = REPO / "generators/e9be57a9c56d/workspace/parametric/prototype.py"
REPORT = HERE.with_suffix(".json")

spec = importlib.util.spec_from_file_location("e9be_extra_gap_probe", PROTOTYPE)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)
generator, _, _ = module.selected_generator()


def independent_mirror(grid: list[list[int]], extra_copy_gap: int) -> list[list[int]]:
    scene = generator._analyze(grid)
    n = scene["n_markers"]
    anchor = scene["anchor_pos"]
    axis_size = scene["template_w"] if scene["orientation"] == "horizontal" else scene["template_h"]
    offsets = [0] * n
    for index in range(anchor + 1, n):
        offsets[index] = (
            offsets[index - 1]
            + axis_size
            - 1
            + scene["gaps"][index - 1]
            + extra_copy_gap
        )
    for index in range(anchor - 1, -1, -1):
        offsets[index] = (
            offsets[index + 1]
            - axis_size
            + 1
            - scene["gaps"][index]
            - extra_copy_gap
        )

    template_cells = scene["template"]["cells"]
    row0 = min(row for row, _ in template_cells)
    col0 = min(col for _, col in template_cells)
    positions = (
        [(row0, col0 + offset) for offset in offsets]
        if scene["orientation"] == "horizontal"
        else [(row0 + offset, col0) for offset in offsets]
    )
    output = deepcopy(scene["grid"])
    for index, marker in enumerate(scene["markers"]):
        if index == anchor:
            continue
        copy_row, copy_col = positions[index]
        for dr, dc in scene["pattern"]:
            row, col = copy_row + dr, copy_col + dc
            if not (0 <= row < scene["height"] and 0 <= col < scene["width"]):
                raise AssertionError(("out_of_bounds", extra_copy_gap, scene, index, row, col))
            output[row][col] = marker["color"]
    return output


started = time.monotonic()
settings = Counter()
orientations = Counter()
markers = Counter()
template_sizes = Counter()
anchors = Counter()
dimensions = Counter()
public_ids: set[str] = set()
parity_checks = 0
episode_count = 0
input_count = 0
max_height = 0
max_width = 0

with module.RuleOracle(timeout=20.0) as oracle:
    # Exercise complete sampler phase/configuration cycles beyond one episode.
    for sample_index in range(64):
        source, metadata = module._sample_input(20261023, sample_index)
        max_height = max(max_height, len(source))
        max_width = max(max_width, len(source[0]))
        assert len(source) <= 30 and len(source[0]) <= 30
        assert generator.self_check(source) == []
        orientations[metadata["orientation"]] += 1
        markers[metadata["n_markers"]] += 1
        template_sizes[metadata["template_size"]] += 1
        anchors[metadata["anchor_pos"]] += 1
        dimensions[f"{len(source)}x{len(source[0])}"] += 1
        for gap in (0, 1):
            actual = oracle.apply(module.materialize_rule(gap), source)
            expected = independent_mirror(source, gap)
            assert actual == expected, (sample_index, gap, metadata)
            parity_checks += 1

    # Exercise episode selection and teaching contracts across both settings.
    for seed in range(8):
        for gap in (0, 1):
            episode = module.build_episode(
                seed=seed,
                extra_copy_gap=gap,
                demo_count=3,
                query_count=4,
                oracle=oracle,
            )
            episode_count += 1
            settings[gap] += 1
            public = episode["public"]
            identifier = public_challenge_id(public)
            assert identifier not in public_ids
            public_ids.add(identifier)
            inputs = [pair["input"] for pair in public["train"] + public["test"]]
            assert len(inputs) == 7
            assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 7
            input_count += len(inputs)
            private = episode["private"]
            assert private["rival_fit"]["surviving_rivals"] == []
            assert all(row["identified_from_demonstrations"] for row in private["per_query_checks"])
            assert all(row["opposite_changes_query"] for row in private["per_query_checks"])

result = {
    "schema": "e9be57a9c56d-extra-gap-adversarial-v1",
    "prototype_sha256": module.hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest(),
    "elapsed_seconds": round(time.monotonic() - started, 3),
    "sampler_inputs": 64,
    "episode_count": episode_count,
    "episode_inputs": input_count,
    "unique_public_ids": len(public_ids),
    "racket_python_parity_checks": parity_checks,
    "max_height": max_height,
    "max_width": max_width,
    "settings": dict(sorted(settings.items())),
    "orientations": dict(sorted(orientations.items())),
    "marker_counts": dict(sorted(markers.items())),
    "template_sizes": dict(sorted(template_sizes.items())),
    "anchor_positions": dict(sorted(anchors.items())),
    "dimension_profiles": dict(sorted(dimensions.items())),
    "failures": [],
    "limits": (
        "Bounded deterministic probe: 64 sampler indices and 16 episodes; "
        "independent geometry shares the production parser but not the Racket edit sites."
    ),
}
REPORT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
