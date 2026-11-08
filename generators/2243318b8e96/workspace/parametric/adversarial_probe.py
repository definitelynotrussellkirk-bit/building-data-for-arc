#!/usr/bin/env python3
"""Bounded adversarial self-review for 2243318b8e96 cue parity."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
TASK_ID = "2243318b8e96"


def _load(name: str):
    path = HERE / name
    spec = importlib.util.spec_from_file_location("_probe_" + name.replace(".", "_"), path)
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


def _all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _constant_color_mapping_possible(proto, episode) -> bool:
    mapping: dict[int, int] = {}
    for pair in episode["train"]:
        for obj in proto._components(pair["input"]):
            cells = list(obj["cells"])
            output_colors = {pair["output"][r][c] for r, c in cells}
            if len(output_colors) != 1:
                return False
            out = next(iter(output_colors))
            color = int(obj["color"])
            if color in mapping and mapping[color] != out:
                return False
            mapping[color] = out
    return True


def _position_alternating(proto, grid):
    objects = sorted(proto._components(grid), key=lambda obj: min(obj["cells"]))
    output = [[0] * len(grid[0]) for _ in grid]
    for index, obj in enumerate(objects):
        for r, c in obj["cells"]:
            output[r][c] = 3 if index % 2 == 0 else 8
    return output


def _size_rank_split(proto, grid):
    objects = sorted(proto._components(grid), key=lambda obj: (int(obj["size"]), min(obj["cells"])))
    output = [[0] * len(grid[0]) for _ in grid]
    for index, obj in enumerate(objects):
        for r, c in obj["cells"]:
            output[r][c] = 3 if index < len(objects) // 2 else 8
    return output


def _extend_component(proto, grid, wanted_color: int):
    result = copy.deepcopy(grid)
    h, w = len(result), len(result[0])
    components = proto._components(result)
    target = next(obj for obj in components if obj["color"] == wanted_color)
    other = set().union(*(obj["cells"] for obj in components if obj is not target))
    for r, c in sorted(target["cells"]):
        for dr, dc in proto._CARDINAL:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w) or result[rr][cc] != 0:
                continue
            if any((rr + ar, cc + ac) in other for ar, ac in proto._CARDINAL):
                continue
            result[rr][cc] = wanted_color
            if not proto._scene_errors(result):
                return result
            result[rr][cc] = 0
    raise AssertionError("could not construct lawful one-cell parity perturbation")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    proto = _load("prototype.py")
    adapter = _load("adapter.py")
    started = time.monotonic()

    settings = list(proto.SETTINGS)
    episodes_checked = 0
    matched_checks = 0
    wrong_setting_checks = 0
    named_shortcut_checks = 0
    extra_structural_checks = 0
    public_invariance_checks = 0
    public_positive_controls = 0
    stress_rows = []

    for seed in range(16):
        for demos in (2, 6):
            episodes = [proto.generate(seed, setting, demos, 4) for setting in settings]
            assert [_all_inputs(ep) for ep in episodes].count(_all_inputs(episodes[0])) == len(settings)
            matched_checks += 1
            for setting, episode in zip(settings, episodes, strict=True):
                certificate = proto.certify(episode)
                assert certificate["survivors"] == [setting]
                assert all(value == "refuted" for value in certificate["rivals"].values())
                named_shortcut_checks += len(certificate["rivals"])
                for wrong in settings:
                    if wrong == setting:
                        continue
                    assert not all(proto.transform(pair["input"], wrong) == pair["output"]
                                   for pair in episode["train"])
                    wrong_setting_checks += 1
                assert not _constant_color_mapping_possible(proto, episode)
                assert not all(_position_alternating(proto, pair["input"]) == pair["output"]
                               for pair in episode["train"])
                assert not all(_size_rank_split(proto, pair["input"]) == pair["output"]
                               for pair in episode["train"])
                extra_structural_checks += 3
                assert len({proto.digest(grid) for grid in _all_inputs(episode)}) == demos + 4

                visible = proto.public_turn(episode, 0)
                private_mutation = copy.deepcopy(episode)
                private_mutation["settings"] = settings[(settings.index(setting) + 1) % len(settings)]
                private_mutation["program_solution"] = "PRIVATE-MUTATION"
                private_mutation["certificate"] = {"forged": True}
                for pair in private_mutation["test"]:
                    pair["output"] = [[9]]
                for pair in private_mutation["test"][1:]:
                    pair["input"] = [[9]]
                assert proto.public_turn(private_mutation, 0) == visible
                public_invariance_checks += 1
                current_mutation = copy.deepcopy(episode)
                current_mutation["test"][0]["input"][0][0] = 9 if current_mutation["test"][0]["input"][0][0] == 0 else 0
                assert proto.public_turn(current_mutation, 0) != visible
                public_positive_controls += 1
                episodes_checked += 1

            stress = episodes[0]["test"][3]["input"]
            profile = proto.scene_profile(stress)
            assert profile["shape"] == [30, 30]
            assert profile["nonzero_cells"] >= 60
            assert profile["row_span"] >= 24 and profile["column_span"] >= 24
            assert profile["boundary_components"] >= 2
            assert profile["diagonal_same_color_contacts"] >= 1
            stress_rows.append({"seed": seed, **profile})

    # Prefix stability and count independence: increasing demonstrations cannot
    # perturb the complete four-query bank.
    minimum = proto.generate(77, settings[0], 2, 4)
    maximum = proto.generate(77, settings[0], 6, 4)
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"]

    # Adapter is thin and preserves exact source/labels.
    adapted = adapter.generate(81, settings[1], 2, 4)
    native = proto.generate(81, settings[1], 2, 4)
    assert adapted == {key: native[key] for key in ("train", "test", "program_solution")}
    assert adapter.program(settings[0]) == proto.CANONICAL_PROGRAM
    assert (HERE / "canonical.rkt").read_text().rstrip("\n") == proto.CANONICAL_PROGRAM

    # Causal crossed controls.  First flip only the cue's size parity; then hold
    # cue parity fixed while flipping a non-cue component's parity.
    base = proto.generate(101, settings[1], 2, 4)["test"][1]["input"]
    changed_cue = _extend_component(proto, base, 1)
    assert proto.cue_parity(changed_cue) != proto.cue_parity(base)
    assert proto.transform(base, settings[1]) != proto.transform(changed_cue, settings[1])
    noncue_color = next(int(obj["color"]) for obj in proto._components(base)
                        if obj["color"] not in (1, 2))
    changed_object = _extend_component(proto, base, noncue_color)
    assert proto.cue_parity(changed_object) == proto.cue_parity(base)
    assert proto.transform(base, settings[1]) != proto.transform(changed_object, settings[1])
    crossed_controls = [
        {
            "kind": "fixed_other_objects_changed_cue_intermediate",
            "before_cue_parity": proto.cue_parity(base),
            "after_cue_parity": proto.cue_parity(changed_cue),
            "before_sha256": proto.digest(base),
            "after_sha256": proto.digest(changed_cue),
        },
        {
            "kind": "fixed_intermediate_changed_noncue_parity",
            "cue_parity": proto.cue_parity(base),
            "before_sha256": proto.digest(base),
            "after_sha256": proto.digest(changed_object),
        },
    ]

    # Authored-certificate and strict API attacks.
    corrupted = copy.deepcopy(maximum)
    corrupted["train"][0]["output"] = [[9]]
    duplicate = copy.deepcopy(maximum)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    malformed = copy.deepcopy(maximum)
    malformed["test"][0]["input"][0][0] = True
    missing_cue = copy.deepcopy(maximum)
    for row in missing_cue["test"][0]["input"]:
        for index, value in enumerate(row):
            if value == 1:
                row[index] = 4
    rejections = [
        _expect_error(lambda: proto.generate(True, settings[0], 2, 4), "boolean seed"),
        _expect_error(lambda: proto.generate(0, settings[0], True, 4), "boolean demos"),
        _expect_error(lambda: proto.generate(0, settings[0], 1, 4), "too few demos"),
        _expect_error(lambda: proto.generate(0, settings[0], 2, 3), "non-four query count"),
        _expect_error(lambda: proto.program({"parity_reference": "absolute", "extra": 0}), "extra setting"),
        _expect_error(lambda: proto.certify(corrupted), "forged label"),
        _expect_error(lambda: proto.certify(duplicate), "duplicate input"),
        _expect_error(lambda: proto.certify(malformed), "boolean cell"),
        _expect_error(lambda: proto.certify(missing_cue), "missing cue"),
        _expect_error(lambda: proto.public_turn(maximum, True), "boolean turn"),
    ]

    # Protected-Racket replay at the supported minimum, including the 30x30
    # query, on fresh seeds not used by focused tests.
    racket_rows = []
    evaluations = 0
    with proto.RacketRunner() as run:
        for seed in (37, 89):
            for setting in settings:
                episode = proto.generate(seed, setting, 2, 4)
                certificate = proto.certify(episode, execute=run)
                assert certificate["survivors"] == [setting]
                for pair_index in (0, 1, 5):
                    pair = (episode["train"] + episode["test"])[pair_index]
                    assert run(proto.program(setting), pair["input"]) == pair["output"]
                    evaluations += 1
                racket_rows.append({
                    "seed": seed,
                    "settings": setting,
                    "survivors": certificate["survivors"],
                    "program_sha256": hashlib.sha256(proto.program(setting).encode()).hexdigest(),
                })

    result = {
        "schema": "arcpuzzles-parametric-adversarial-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "attempted_surfaces": [
            "three settings over 16 seeds at minimum/maximum demonstration counts with matched inputs",
            "all wrong declared settings plus fixed-output, swapped, threshold, bbox, 8-connectivity, color-total, foreground-total and partial-cue shortcuts",
            "constant input-color mapping, fixed object-position alternation and size-rank splitting",
            "crossed controls changing the cue parity at fixed other objects and a non-cue parity at fixed cue intermediate",
            "strict seed/count/settings/cell validation, forged labels, duplicate inputs and missing cue",
            "first-turn private/future-query invariance with current-query positive controls",
            "protected-Racket replay on both fresh seeds, all settings and each 30x30 query",
        ],
        "episodes_checked": episodes_checked,
        "matched_input_checks": matched_checks,
        "wrong_setting_checks": wrong_setting_checks,
        "named_shortcut_checks": named_shortcut_checks,
        "extra_structural_shortcut_checks": extra_structural_checks,
        "public_invariance_checks": public_invariance_checks,
        "public_positive_controls": public_positive_controls,
        "stress_30x30_checks": len(stress_rows),
        "stress_examples": stress_rows[:4],
        "crossed_controls": crossed_controls,
        "rejections": rejections,
        "racket": {
            "backend": "racket",
            "protected": True,
            "rows": racket_rows,
            "direct_label_evaluations": evaluations,
            "certificate_program_evaluations": len(racket_rows) * len(settings) * 2,
        },
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
        "wrong_setting_checks": wrong_setting_checks,
        "named_shortcut_checks": named_shortcut_checks,
        "stress_30x30_checks": len(stress_rows),
        "racket_rows": len(racket_rows),
        "elapsed_seconds": result["elapsed_seconds"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
