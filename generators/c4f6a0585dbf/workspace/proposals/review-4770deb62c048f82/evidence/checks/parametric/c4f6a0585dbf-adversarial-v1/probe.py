from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "c4f6a0585dbf"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
spec = importlib.util.spec_from_file_location("c4f6_adversarial", PROTOTYPE_PATH)
assert spec is not None and spec.loader is not None
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)
generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)

started = time.monotonic()
input_seeds = [*range(32), 2**31 - 1, 2**63 - 1]
input_checks = 0
observed_shapes = set()
observed_markers = set()
for input_seed in input_seeds:
    grids = prototype.generate_inputs(input_seed)
    assert len(grids) == 7
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) == 7
    for grid in grids:
        assert generator.self_check(grid) == []
        observed = generator.observe_overrides(grid)
        assert observed["n_ports"] == 3
        assert 20 <= len(grid) <= 24
        assert 20 <= len(grid[0]) <= 24
        assert all(type(cell) is int and not isinstance(cell, bool) for row in grid for cell in row)
        assert {cell for row in grid for cell in row} <= {0, 1, 4}
        marker_count = sum(cell == 4 for row in grid for cell in row)
        assert 20 <= marker_count <= 23
        observed_shapes.add((len(grid), len(grid[0])))
        observed_markers.add(marker_count)
        input_checks += 1

paired_input_seeds = [31]
label_checks = 0
rival_checks = 0
public_checks = 0
pair_summaries = []
with RacketBridge() as bridge:
    for input_seed in paired_input_seeds:
        episodes = []
        for offset, setting in enumerate(prototype.MIN_VISIBLE_PORTS):
            episode = prototype.generate_episode(
                bridge,
                2 * input_seed + offset,
                min_visible_ports=setting,
            )
            program = prototype.program_for_min_visible_ports(setting, root=ROOT)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.evaluate(bridge, program, pair["input"])
                label_checks += 1
            analysis = prototype.analyze_episode(bridge, episode)
            assert analysis["demonstration_refutations"] == [0, 1, 2]
            assert all(row["query_differs"] and row["status"] == "no_ambiguity_found" for row in analysis["queries"])
            rival_checks += 7
            episodes.append(episode)
            public = prototype.public_challenge(episode)
            payload = public_challenge_bytes(public)
            identifier = public_challenge_id(public)
            assert identifier == hashlib.sha256(payload).hexdigest()
            assert json.loads(payload) == public
            assert all(set(pair) == {"input"} for pair in public["test"])
            public_checks += 1
        assert [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]] == [
            pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]
        ]
        assert all(
            left["output"] != right["output"]
            for left, right in zip(
                episodes[0]["train"] + episodes[0]["test"],
                episodes[1]["train"] + episodes[1]["test"],
                strict=True,
            )
        )
        records = prototype.prepare_public_records(episodes)
        assert [row["public_id"] for row in records] == sorted(row["public_id"] for row in records)
        pair_summaries.append(
            {
                "input_seed": input_seed,
                "public_ids": [row["public_id"] for row in records],
                "all_seven_outputs_differ": True,
            }
        )

try:
    prototype.prepare_public_records([episodes[0], episodes[0]])
except ValueError as exc:
    duplicate_rejection = str(exc)
else:
    raise AssertionError("duplicate visible challenge was not rejected")

result = {
    "schema": "c4f6a0585dbf-adversarial-probe-v1",
    "status": "bounded_no_finding",
    "surfaces": [
        "sampler boundaries and retry/placement success",
        "parameter/Racket parity plus public export and numeric types",
    ],
    "source": {
        "generator_path": str(generator_path.relative_to(ROOT)),
        "generator_sha256": generator_sha256,
        "prototype_path": str(PROTOTYPE_PATH.relative_to(ROOT)),
        "prototype_sha256": hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest(),
        "canonical_racket_sha256": hashlib.sha256(prototype.canonical_rule(root=ROOT).encode()).hexdigest(),
    },
    "sampler": {
        "input_seeds": input_seeds,
        "grids_checked": input_checks,
        "shapes_observed": sorted([list(shape) for shape in observed_shapes]),
        "marker_counts_observed": sorted(observed_markers),
        "finding": None,
    },
    "authority_and_export": {
        "paired_input_seeds": paired_input_seeds,
        "episodes_checked": 2 * len(paired_input_seeds),
        "labels_reexecuted_through_racket": label_checks,
        "rival_labels_checked": rival_checks,
        "public_payloads_checked": public_checks,
        "duplicate_rejection": duplicate_rejection,
        "bridge_policy": "one short-lived protected Racket child, bounded to 42 task evaluations",
        "pairs": pair_summaries,
        "finding": None,
    },
    "elapsed_seconds": round(time.monotonic() - started, 3),
    "limits": (
        "Bounded to 34 sampler seeds and one paired input seed; it does not prove "
        "exhaustive placement coverage or production suitability."
    ),
}
(Path(__file__).with_name("result.json")).write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, indent=2, sort_keys=True))
