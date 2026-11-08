"""Bounded semantic-rival audit for the repeated-shape parametric lesson."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SOURCE = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_fb7_audit_proto_" + hashlib.sha256(_SOURCE.read_bytes()).hexdigest(), _SOURCE
)
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)


def _pick(grid, mode):
    classes = [(shape, items) for shape, items in P._shape_classes(grid).items() if len(items) >= 2]
    if mode == "largest_area":
        return min(classes, key=lambda item: (-len(item[0]), P._class_anchor(item[1])))
    if mode == "smallest_area":
        return min(classes, key=lambda item: (len(item[0]), P._class_anchor(item[1])))
    if mode == "largest_mass":
        return min(classes, key=lambda item: (-len(item[0]) * len(item[1]), P._class_anchor(item[1])))
    if mode == "smallest_mass":
        return min(classes, key=lambda item: (len(item[0]) * len(item[1]), P._class_anchor(item[1])))
    if mode == "top_left":
        return min(classes, key=lambda item: P._class_anchor(item[1]))
    raise ValueError(mode)


def _rivals(settings):
    truth = settings["class_policy"]
    other = "least_repeated" if truth == "most_frequent" else "most_frequent"

    def native(policy):
        return lambda grid: P.render_shape(*(
            lambda selected: (selected[0], len(selected[1]))
        )(P.select_class(grid, policy)))

    rivals = {"other_native_policy": native(other)}
    for mode in ("largest_area", "smallest_area", "largest_mass", "smallest_mass", "top_left"):
        rivals[mode] = lambda grid, mode=mode: P.render_shape(
            _pick(grid, mode)[0], len(_pick(grid, mode)[1])
        )
    for fixed in (2, 3, 4, 5):
        rivals[f"selected_fixed_scale_{fixed}"] = lambda grid, fixed=fixed: P.render_shape(
            P.select_class(grid, truth)[0], fixed
        )
    rivals["selected_unscaled"] = lambda grid: P.render_shape(P.select_class(grid, truth)[0], 1)
    rivals["selected_total_objects_scale"] = lambda grid: P.render_shape(
        P.select_class(grid, truth)[0], len(P._components(grid))
    )
    return rivals


def audit_episode(seed, settings, demos=2, queries=4):
    episode = P.generate(seed, settings, demos=demos, queries=queries)
    rivals = _rivals(settings)
    survivors = []
    harmful = []
    query_disagreements = {}
    for name, rival in rivals.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
            disagreements = [
                index
                for index, pair in enumerate(episode["test"])
                if rival(pair["input"]) != pair["output"]
            ]
        except Exception as error:  # a rival error is evidence against that rival, not a pass
            fits = False
            disagreements = [f"error:{type(error).__name__}:{error}"]
        if fits:
            survivors.append(name)
            query_disagreements[name] = disagreements
            if disagreements:
                harmful.append(name)
    constant = episode["train"][0]["output"]
    return {
        "seed": seed,
        "settings": settings,
        "demos": demos,
        "queries": queries,
        "rival_count": len(rivals),
        "survivors": survivors,
        "harmful_survivors": harmful,
        "query_disagreements": query_disagreements,
        "constant_query_failures": sum(pair["output"] != constant for pair in episode["test"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 4096:
        raise SystemExit("--seeds must be in 1..4096")
    reports = [
        audit_episode(seed, settings)
        for seed in range(args.seeds)
        for settings in P.SETTINGS
    ]
    payload = {
        "schema": "arcpuzzles-bounded-rival-audit-v1",
        "task_id": P.TASK_ID,
        "episodes": len(reports),
        "pairs": sum(report["demos"] + report["queries"] for report in reports),
        "harmful_survivors": sum(len(report["harmful_survivors"]) for report in reports),
        "reports": reports,
        "limitations": "Finite named rivals and sampled seeds; not a proof of universal identifiability.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ("task_id", "episodes", "pairs", "harmful_survivors")}, sort_keys=True))
    if payload["harmful_survivors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
