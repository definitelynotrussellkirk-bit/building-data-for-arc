"""Focused adversarial probe for the 941f7ac13580 border-size family."""
from __future__ import annotations

import argparse
import copy
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1]


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "_probe_941_" + hashlib.sha256(str(path).encode()).hexdigest(), path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expect_error(label: str, fn, errors: list[str]) -> None:
    try:
        fn()
    except (TypeError, ValueError):
        return
    except Exception as exc:  # the rejection should be deliberate, not a crash
        errors.append(f"{label}: wrong exception {type(exc).__name__}: {exc}")
        return
    errors.append(f"{label}: malformed value was accepted")


def run(seeds: int = 24, *, racket: bool = False) -> dict[str, Any]:
    p = _load()
    errors: list[str] = []
    episodes = 0
    pairs = 0
    rotations_at_fixed_profile: set[int] = set()
    border_sizes_at_fixed_profile: set[int] = set()
    grouped: dict[tuple[int, int], dict[str, set[Any]]] = defaultdict(
        lambda: {"shapes": set(), "ranks": set(), "colors": set(), "sides": set()}
    )
    shortcut_counts: dict[str, int] = defaultdict(int)
    max_demo_episodes = 0
    racket_pairs = 0

    runner = p.RacketRunner() if racket else None
    execute = runner.__enter__() if runner is not None else None
    try:
        for seed in range(seeds):
            for setting in p.SETTINGS:
                episode = p.generate(seed, setting, demos=2, queries=4)
                certificate = p.certify(episode, execute)
                episodes += 1
                pairs += 6
                if execute is not None:
                    racket_pairs += 6
                if certificate["survivors"] != [setting]:
                    errors.append(f"seed {seed} {setting}: survivor mismatch")
                shortcuts = certificate["shortcut_refutations"]
                for name, killed in shortcuts.items():
                    shortcut_counts[name] += int(killed)
                required = {k: v for k, v in shortcuts.items() if k != "fixed_first"}
                if not all(required.values()):
                    errors.append(f"seed {seed} {setting}: shortcut survived {required}")
                if setting["sequence_origin"] == "border_size" and not shortcuts["fixed_first"]:
                    errors.append(f"seed {seed}: canonical fixed-first rule survived alternate demos")

                all_pairs = episode["train"] + episode["test"]
                for pair_index, pair in enumerate(all_pairs):
                    facts = p.scene_facts(pair["input"])
                    key = (facts["object_count"], facts["rotation"])
                    colors = tuple(sorted(item["color"] for item in facts["components"]))
                    side = (
                        "top" if any(r == 0 for r, _ in facts["components"][facts["border_object_index"]]["cells"])
                        else "bottom" if any(r == facts["height"] - 1 for r, _ in facts["components"][facts["border_object_index"]]["cells"])
                        else "left" if any(c == 0 for _, c in facts["components"][facts["border_object_index"]]["cells"])
                        else "right"
                    )
                    grouped[key]["shapes"].add((facts["height"], facts["width"]))
                    grouped[key]["ranks"].add(facts["border_object_index"])
                    grouped[key]["colors"].add(colors)
                    grouped[key]["sides"].add(side)
                    if pair_index == 0:
                        rotations_at_fixed_profile.add(facts["rotation"])
                        border_sizes_at_fixed_profile.add(facts["border_object_size"])
                    if facts["border_object_count"] != 1 or facts["rotation"] in (None, 0):
                        errors.append(f"seed {seed} pair {pair_index}: invalid dependency facts")
                    if (facts["height"], facts["width"]) == (30, 30) and facts["nonzero_cells"] < 20:
                        errors.append(f"seed {seed}: 30x30 stress is only {facts['nonzero_cells']} cells")

                    # Color is nuisance: a bijective nonzero recoloring cannot change labels.
                    remap = {color: 10 - color for color in range(1, 10)}
                    recolored = [
                        [remap.get(cell, cell) for cell in row] for row in pair["input"]
                    ]
                    if p.transform(recolored, setting) != pair["output"]:
                        errors.append(f"seed {seed} pair {pair_index}: color shortcut leaked")

        # Maximum supported demo count, both branches, with independent four-query bank.
        for setting in p.SETTINGS:
            episode = p.generate(91, setting, demos=6, queries=4)
            p.certify(episode, execute)
            max_demo_episodes += 1
            if len(episode["train"]) != 6 or len(episode["test"]) != 4:
                errors.append(f"max-demo count mismatch for {setting}")

        if len(rotations_at_fixed_profile) < 2 or len(border_sizes_at_fixed_profile) < 2:
            errors.append(
                "crossed control failed: fixed 10x12/count/rank profile did not vary intermediate"
            )
        nuisance_groups = [
            (key, values)
            for key, values in grouped.items()
            if len(values["shapes"]) >= 2
            and len(values["ranks"]) >= 2
            and len(values["colors"]) >= 3
            and len(values["sides"]) >= 2
        ]
        if not nuisance_groups:
            errors.append(
                "crossed control failed: no fixed (count,rotation) group varied shape/rank/color/side"
            )

        # Authored certificate and count/grid rejection attacks.
        exemplar = p.generate(123, p.SETTINGS[1], demos=2, queries=4)
        duplicate = copy.deepcopy(exemplar)
        duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
        _expect_error("duplicate input", lambda: p.certify(duplicate), errors)
        wrong_label = copy.deepcopy(exemplar)
        wrong_label["test"][0]["output"] = [[9]]
        _expect_error("wrong label", lambda: p.certify(wrong_label), errors)
        wrong_program = copy.deepcopy(exemplar)
        wrong_program["program_solution"] = "(rule! g)"
        _expect_error("wrong program", lambda: p.certify(wrong_program), errors)
        forged = copy.deepcopy(exemplar)
        forged["certificate"] = {"survivors": [p.SETTINGS[0]], "racket_checked": True}
        if p.certify(forged)["survivors"] != [p.SETTINGS[1]]:
            errors.append("forged saved certificate bypassed recomputation")
        for label, fn in (
            ("bool seed", lambda: p.generate(True, p.DEFAULT, 2, 4)),
            ("too few demos", lambda: p.generate(1, p.DEFAULT, 1, 4)),
            ("too many demos", lambda: p.generate(1, p.DEFAULT, 7, 4)),
            ("wrong query count", lambda: p.generate(1, p.DEFAULT, 2, 3)),
            ("unknown setting", lambda: p.program({"sequence_origin": "largest"})),
            ("extra setting", lambda: p.program({"sequence_origin": "top_left", "x": 1})),
            ("bool grid cell", lambda: p.transform([[True]], p.DEFAULT)),
            ("ragged grid", lambda: p.transform([[0, 1], [0]], p.DEFAULT)),
            ("no border anchor", lambda: p.transform([[0] * 4 for _ in range(4)], p.DEFAULT)),
        ):
            _expect_error(label, fn, errors)
    finally:
        if runner is not None:
            runner.__exit__(None, None, None)

    status = "PASS" if not errors else "FAIL"
    return {
        "schema": "941f7ac13580-adversarial-probe-v1",
        "status": status,
        "finite_scope": {
            "seeds": seeds,
            "settings": len(p.SETTINGS),
            "minimum_demo_episodes": episodes,
            "maximum_demo_episodes": max_demo_episodes,
            "pairs_checked": pairs,
            "racket_pairs": racket_pairs,
        },
        "crossed_controls": {
            "fixed_profile_rotations": sorted(rotations_at_fixed_profile),
            "fixed_profile_border_sizes": sorted(border_sizes_at_fixed_profile),
            "nuisance_groups": [
                {
                    "object_count": key[0],
                    "rotation": key[1],
                    "shape_count": len(values["shapes"]),
                    "rank_count": len(values["ranks"]),
                    "palette_count": len(values["colors"]),
                    "side_count": len(values["sides"]),
                }
                for key, values in nuisance_groups
            ],
        },
        "shortcut_refutation_counts": dict(sorted(shortcut_counts.items())),
        "errors": errors,
        "limits": "Finite rival and malformed-input checks do not prove universal rule uniqueness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 128:
        raise SystemExit("--seeds must be in 1..128")
    result = run(args.seeds, racket=args.racket)
    body = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    print(body, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
