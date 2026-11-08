#!/usr/bin/env python3
"""Bounded adversarial self-review for 7d970a1ea99b reflection scope."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
TASK_ID = "7d970a1ea99b"


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_7d970a1ea99b", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expect_error(fn, label: str) -> str:
    try:
        fn()
    except (TypeError, ValueError) as exc:
        return f"{label}: {type(exc).__name__}: {exc}"
    raise AssertionError(f"{label} unexpectedly succeeded")


def _fixed_color(proto, color):
    return lambda grid: proto._reflect_fixed(grid, color)


def _fixed_diagonal_slot(proto, slot):
    def rival(grid):
        color = grid[slot][slot]
        return proto._reflect_fixed(grid, color) if color else [row[:] for row in grid]
    return rival


def _all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    proto = _load()
    started = time.monotonic()

    settings = list(proto.SETTINGS)
    count_corners = ((2, 1), (2, 4), (6, 1), (6, 4))
    episodes_checked = 0
    matched_checks = 0
    fixed_color_checks = 0
    fixed_slot_checks = 0
    cross_checks = []
    stress_checks = []

    for seed in range(12):
        for demos, queries in count_corners:
            episodes = [proto.generate(seed, setting, demos, queries) for setting in settings]
            assert _all_inputs(episodes[0]) == _all_inputs(episodes[1])
            matched_checks += 1
            for setting, episode in zip(settings, episodes, strict=True):
                assert episode["certificate"]["survivors"] == [setting]
                assert all(v == "refuted" for v in episode["certificate"]["rivals"].values())
                assert len({proto.digest(grid) for grid in _all_inputs(episode)}) == demos + queries
                for color in range(1, 10):
                    rival = _fixed_color(proto, color)
                    assert not all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                    fixed_color_checks += 1
                for slot in (0, 1, 2, 3, 4):
                    rival = _fixed_diagonal_slot(proto, slot)
                    assert not all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                    fixed_slot_checks += 1
                episodes_checked += 1
            if queries == 4:
                stress = episodes[0]["test"][3]["input"]
                p = proto.profile(stress)
                assert p["shape"] == "30x30" and p["boundary_sources"] >= 2
                assert sum(cell != 0 for row in stress for cell in row) >= 40
                stress_checks.append({"seed": seed, **p})

    # Demo and query streams are prefix-stable and independent.
    minimum = proto.generate(77, settings[0], 2, 1)
    maximum = proto.generate(77, settings[0], 6, 4)
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"][:1]

    # Crossed control 1: hold dimensions and all source positions fixed, change
    # only the diagonal cue to a decoy color.  The selected reflected group must change.
    base = proto.generate(101, {"reflection_scope": "diagonal_cued"}, 2, 4)["test"][1]["input"]
    changed_cue = copy.deepcopy(base)
    n = len(base)
    cue_index = next(i for i in range(n) if base[i][i])
    old_cue = base[cue_index][cue_index]
    decoy = next(value for row in base for value in row if value not in (0, old_cue))
    changed_cue[cue_index][cue_index] = decoy
    assert proto.diagonal_cue_color(changed_cue) == decoy
    assert proto.transform(base, {"reflection_scope": "diagonal_cued"}) != proto.transform(
        changed_cue, {"reflection_scope": "diagonal_cued"}
    )
    cross_checks.append({
        "kind": "fixed_geometry_changed_intermediate",
        "shape": [n, n],
        "old_cue": old_cue,
        "new_cue": decoy,
        "input_sha256": proto.digest(base),
        "changed_sha256": proto.digest(changed_cue),
    })

    # Crossed control 2: hold the cue color fixed while transposing all source
    # geometry.  The intermediate remains equal but the final selected cells move.
    transposed = [list(row) for row in zip(*base)]
    assert proto.diagonal_cue_color(transposed) == old_cue
    assert proto.profile(transposed)["cue_frequency_rank"] == proto.profile(base)["cue_frequency_rank"]
    assert proto.transform(base, {"reflection_scope": "diagonal_cued"}) != proto.transform(
        transposed, {"reflection_scope": "diagonal_cued"}
    )
    cross_checks.append({
        "kind": "fixed_intermediate_changed_geometry",
        "cue": old_cue,
        "input_sha256": proto.digest(base),
        "transposed_sha256": proto.digest(transposed),
    })

    # Authored-certificate and API attacks.
    corrupted = copy.deepcopy(maximum)
    corrupted["train"][0]["output"] = [[9]]
    duplicate = copy.deepcopy(maximum)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    malformed = copy.deepcopy(maximum["test"][0]["input"])
    malformed[0][0] = True
    two_cues = copy.deepcopy(maximum["test"][0]["input"])
    empty_diag = next(i for i in range(len(two_cues)) if two_cues[i][i] == 0)
    two_cues[empty_diag][empty_diag] = next(v for row in two_cues for v in row if v)
    rejections = [
        _expect_error(lambda: proto.generate(0, settings[0], True, 4), "boolean demos"),
        _expect_error(lambda: proto.generate(0, settings[0], 2, 5), "too many queries"),
        _expect_error(lambda: proto.program({"reflection_scope": "all", "extra": 0}), "extra setting"),
        _expect_error(lambda: proto.certify(corrupted), "forged label"),
        _expect_error(lambda: proto.certify(duplicate), "duplicate input"),
        _expect_error(lambda: proto.transform(malformed, settings[0]), "boolean cell"),
        _expect_error(lambda: proto.transform(two_cues, settings[1]), "two diagonal cues"),
    ]

    # Protected-Racket replay across both settings, two fresh seeds, minimum
    # lessons and the 30x30 query.  certify also replays demo-only survivors.
    racket_rows = []
    with proto.RacketRunner() as run:
        for seed in (37, 89):
            for setting in settings:
                episode = proto.generate(seed, setting, 2, 4)
                certificate = proto.certify(episode, execute=run)
                for pair_index in (0, 1, 5):
                    pair = (episode["train"] + episode["test"])[pair_index]
                    assert run(proto.program(setting), pair["input"]) == pair["output"]
                racket_rows.append({
                    "seed": seed,
                    "settings": setting,
                    "survivors": certificate["survivors"],
                    "program_sha256": hashlib.sha256(proto.program(setting).encode()).hexdigest(),
                })
        runtime = proto.RacketRunner  # source identity below, runtime already protected by wrapper

    result = {
        "schema": "arcpuzzles-parametric-adversarial-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "attempted_surfaces": [
            "both settings over 12 seeds and all 2/6-demo x 1/4-query corners",
            "all fixed-color 1..9 and fixed-diagonal-slot 0..4 shortcut rules at the two-demo minimum",
            "crossed controls changing cue at fixed geometry and geometry at fixed cue",
            "prefix stability, duplicate inputs, forged labels, malformed cells/settings/counts and two-cue rejection",
            "protected-Racket replay for both settings, two fresh seeds and each 30x30 query",
        ],
        "episodes_checked": episodes_checked,
        "matched_input_checks": matched_checks,
        "fixed_color_shortcut_checks": fixed_color_checks,
        "fixed_slot_shortcut_checks": fixed_slot_checks,
        "crossed_controls": cross_checks,
        "stress_30x30_checks": len(stress_checks),
        "stress_examples": stress_checks[:4],
        "rejections": rejections,
        "racket": {"backend": "racket", "protected": True, "rows": racket_rows,
                   "evaluations_at_least": len(racket_rows) * 7},
        "limits": (
            "Finite named-rival and sampler probes do not prove unrestricted uniqueness; "
            "owner source review and native acceptance remain separate."
        ),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("prototype.py", "adapter.py", "promotion.json")
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "episodes_checked": episodes_checked,
        "matched_input_checks": matched_checks,
        "fixed_color_shortcut_checks": fixed_color_checks,
        "fixed_slot_shortcut_checks": fixed_slot_checks,
        "stress_30x30_checks": len(stress_checks),
        "elapsed_seconds": result["elapsed_seconds"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
