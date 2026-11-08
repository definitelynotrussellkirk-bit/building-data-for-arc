"""Bounded demonstration-only self-audit for the L-completion family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent


def _family():
    path = HERE / "family.py"
    spec = importlib.util.spec_from_file_location("_arc_68e9f92d8e4b_family_audit", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*, seeds: Iterable[int] = range(20)):
    family = _family()
    surviving = []
    episodes = 0
    has_30 = False
    rival_rejections = {name: 0 for name in family.RIVALS}
    for seed in seeds:
        for mode in family.MODES:
            episode = family.generate(seed, {"fill_mode": mode}, 2, 4)
            episodes += 1
            has_30 = has_30 or any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in episode["test"])
            named = {
                "object_color": lambda grid: family.label(grid, "object_color"),
                "orientation_legend": lambda grid: family.label(grid, "orientation_legend"),
                **family.RIVALS,
            }
            for name, transform in named.items():
                if name == mode:
                    continue
                fits = all(transform(pair["input"]) == pair["output"] for pair in episode["train"])
                if fits:
                    surviving.append({"seed": seed, "selected_mode": mode, "rival": name})
                elif name in rival_rejections:
                    rival_rejections[name] += 1
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "status": "passed" if not surviving else "failed",
        "episodes_checked": episodes,
        "surviving_rivals": surviving,
        "rival_rejections": rival_rejections,
        "has_30x30": has_30,
        "limits": "finite declared rivals over the supplied seeds; not universal uniqueness",
    }


if __name__ == "__main__":
    report = run()
    destination = HERE / "evidence/current/self_audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["status"] == "passed" else 1)
