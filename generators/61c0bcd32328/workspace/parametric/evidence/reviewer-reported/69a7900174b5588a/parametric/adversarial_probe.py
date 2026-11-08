#!/usr/bin/env python3
"""Bounded adversarial probe for 61c0bcd32328 authored changes."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
PROTOTYPE = (
    ROOT
    / "generators"
    / "61c0bcd32328"
    / "workspace"
    / "parametric"
    / "prototype.py"
)

spec = importlib.util.spec_from_file_location("adversarial_direction_proto", PROTOTYPE)
if spec is None or spec.loader is None:
    raise RuntimeError(PROTOTYPE)
proto = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proto
spec.loader.exec_module(proto)
generator, generator_path, generator_sha256 = proto.selected_generator()

count_schedules = ((1, 1), (3, 4), (4, 1))
episode_failures = []
max_accepted_sample_index = -1
episode_count = 0
for seed in range(32):
    for direction in proto.SETTINGS:
        for n_train, n_test in count_schedules:
            episode_count += 1
            episode = proto.generate_episode(
                seed,
                direction=direction,
                n_train=n_train,
                n_test=n_test,
            )
            pairs = episode["train"] + episode["test"]
            indices = episode["meta"]["accepted_sample_indices"]
            max_accepted_sample_index = max(max_accepted_sample_index, *indices)
            signatures = [tuple(map(tuple, pair["input"])) for pair in pairs]
            checks = {
                "count": len(pairs) == n_train + n_test,
                "unique": len(set(signatures)) == len(signatures),
                "fixed_setting": episode["parameters"] == {"direction": direction},
                "lawful": all(generator.self_check(pair["input"]) == [] for pair in pairs),
                "labels": all(
                    pair["output"] == proto.solve(pair["input"], direction=direction)
                    for pair in pairs
                ),
                "rival_sensitive": all(
                    pair["output"]
                    != proto.solve(
                        pair["input"],
                        direction=(
                            "counterclockwise"
                            if direction == "clockwise"
                            else "clockwise"
                        ),
                    )
                    for pair in pairs
                ),
            }
            if not all(checks.values()):
                episode_failures.append(
                    {
                        "seed": seed,
                        "direction": direction,
                        "n_train": n_train,
                        "n_test": n_test,
                        "checks": checks,
                    }
                )

singleton_witnesses = {}
for difficulty in ("easy", "medium", "hard"):
    for profile, corner in (
        ("single_tl", "tl"),
        ("single_tr", "tr"),
        ("single_br", "br"),
        ("single_bl", "bl"),
    ):
        key = f"{difficulty}/{profile}"
        found = None
        for seed in range(128):
            grid = generator.generate(
                seed,
                seed * 19 + 5,
                difficulty=difficulty,
                scene_profile=profile,
            )
            info = generator._analysis(grid)
            singleton = any(
                observed_corner == corner and len(part["cells"]) == 1
                for observed_corner, part in info["corner_parts"]
            )
            if singleton:
                found = {
                    "seed": seed,
                    "sample_index": seed * 19 + 5,
                    "self_check": generator.self_check(grid),
                    "directions_differ": (
                        proto.solve(grid, direction="clockwise")
                        != proto.solve(grid, direction="counterclockwise")
                    ),
                    "input_sha256": hashlib.sha256(
                        json.dumps(grid, separators=(",", ":")).encode()
                    ).hexdigest(),
                }
                break
        singleton_witnesses[key] = found

public_failures = []
for seed in range(16):
    episode = proto.generate_episode(seed, n_train=3, n_test=4)
    public = proto.public_challenge(episode)
    changed = deepcopy(episode)
    changed["parameters"]["direction"] = (
        "counterclockwise"
        if episode["parameters"]["direction"] == "clockwise"
        else "clockwise"
    )
    changed["program"] = "private replacement"
    changed["meta"]["seed"] = 999999
    changed["test"][0]["output"] = [[9]]
    checks = {
        "mask": (
            set(public) == {"train", "test"}
            and all(set(pair) == {"input", "output"} for pair in public["train"])
            and all(set(pair) == {"input"} for pair in public["test"])
        ),
        "private_invariant_id": proto.public_id(changed) == proto.public_id(episode),
        "opaque_filename": (
            "clockwise" not in proto.public_filename(episode)
            and "counterclockwise" not in proto.public_filename(episode)
            and "seed" not in proto.public_filename(episode)
        ),
    }
    if not all(checks.values()):
        public_failures.append({"seed": seed, "checks": checks})

invalid_cases = []
for label, call in (
    ("bool_seed", lambda: proto.generate_episode(True)),
    ("negative_seed", lambda: proto.generate_episode(-1)),
    ("bool_train", lambda: proto.generate_episode(0, n_train=True)),
    ("zero_test", lambda: proto.generate_episode(0, n_test=0)),
    ("unknown_direction", lambda: proto.generate_episode(0, direction="sideways")),
):
    try:
        call()
    except ValueError:
        invalid_cases.append({"case": label, "rejected": True})
    else:
        invalid_cases.append({"case": label, "rejected": False})

report = {
    "schema": "61c0bcd32328-adversarial-authored-scope-v1",
    "task_id": proto.TASK_ID,
    "prototype_sha256": hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest(),
    "generator_path": str(generator_path),
    "generator_sha256": generator_sha256,
    "episode_probe": {
        "seeds": [0, 31],
        "settings": list(proto.SETTINGS),
        "count_schedules": [list(value) for value in count_schedules],
        "episodes_checked": episode_count,
        "max_accepted_sample_index": max_accepted_sample_index,
        "failures": episode_failures,
        "passed": not episode_failures,
    },
    "singleton_probe": {
        "seed_range": [0, 127],
        "witnesses": singleton_witnesses,
        "all_12_profile_band_cells_found": all(
            witness is not None
            and witness["self_check"] == []
            and witness["directions_differ"]
            for witness in singleton_witnesses.values()
        ),
    },
    "public_probe": {
        "seeds": [0, 15],
        "failures": public_failures,
        "passed": not public_failures,
    },
    "invalid_numeric_and_setting_probe": {
        "cases": invalid_cases,
        "passed": all(row["rejected"] for row in invalid_cases),
    },
    "limitations": [
        "Finite seeds and three count schedules only; this is not exhaustive.",
        "Singleton search is bounded to 128 seeds for each single-corner profile/band.",
        "Racket parity is covered by the separate exact verifier, not repeated here.",
    ],
    "command": [
        "python3",
        "../checks/parametric/adversarial_probe.py",
    ],
}
report["passed"] = all(
    (
        report["episode_probe"]["passed"],
        report["singleton_probe"]["all_12_profile_band_cells_found"],
        report["public_probe"]["passed"],
        report["invalid_numeric_and_setting_probe"]["passed"],
    )
)
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["passed"] else 1)
