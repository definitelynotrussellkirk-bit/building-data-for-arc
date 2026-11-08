"""Bounded replay audit for the 539d4ac45311 native parametric family.

This intentionally uses only public adapter behavior plus the small pure-Python
solver.  It is useful to later reviewers because it checks the minimum teaching
budget and the cascade's non-commuting A→B dependency across fixed seeds.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"connection_mode": "horizontal"},
    {"connection_mode": "vertical"},
    {"connection_mode": "cascade"},
)


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("audit_539d4ac45311_adapter", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_audit(destination: Path | str | None = None, *, seeds=(0, 17, 29, 63)) -> dict:
    adapter = _load_adapter()
    checked_settings = 0
    unique_survivors = 0
    cascade_pairs = 0
    differs_skip_a = 0
    differs_skip_b = 0
    differs_reversed = 0

    for seed in seeds:
        inputs_by_setting = []
        for chosen in SETTINGS:
            episode = adapter.generate(seed, chosen, 2, 4)
            inputs_by_setting.append([
                pair["input"] for split in ("train", "test") for pair in episode[split]
            ])
            survivors = []
            expected = [pair["output"] for pair in episode["train"]]
            for candidate in SETTINGS:
                observed = [
                    adapter.solve(pair["input"], candidate["connection_mode"])
                    for pair in episode["train"]
                ]
                if observed == expected:
                    survivors.append(candidate)
            checked_settings += 1
            if survivors == [chosen]:
                unique_survivors += 1
        if not all(inputs == inputs_by_setting[0] for inputs in inputs_by_setting[1:]):
            raise AssertionError(f"settings changed the input bank for seed {seed}")

        cascade = adapter.generate(seed, SETTINGS[2], 6, 4)
        for pair in cascade["train"]:
            source = pair["input"]
            expected = pair["output"]
            skip_a = adapter.solve(source, "vertical")
            skip_b = adapter.solve(source, "horizontal")
            reversed_order = adapter.solve(adapter.solve(source, "vertical"), "horizontal")
            cascade_pairs += 1
            differs_skip_a += expected != skip_a
            differs_skip_b += expected != skip_b
            differs_reversed += expected != reversed_order

    report = {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": "539d4ac45311",
        "status": "pass" if (
            unique_survivors == checked_settings
            and differs_skip_a == cascade_pairs
            and differs_skip_b == cascade_pairs
            and differs_reversed == cascade_pairs
        ) else "fail",
        "seeds": list(seeds),
        "settings_checked": checked_settings,
        "minimum_demo_survivors": unique_survivors,
        "cascade_pairs_checked": cascade_pairs,
        "cascade_differs_from_skip_a": differs_skip_a,
        "cascade_differs_from_skip_b": differs_skip_b,
        "cascade_differs_from_reversed_order": differs_reversed,
    }
    if destination is not None:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_audit(args.out)
    print(json.dumps(report, sort_keys=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
