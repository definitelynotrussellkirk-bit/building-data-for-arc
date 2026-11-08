"""Bounded replay audit for the e438ce3e02ce native metric family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"distance_metric": "manhattan"},
    {"distance_metric": "chebyshev"},
)


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("audit_e438ce3e02ce_adapter", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_colors(grid):
    return [value for row in grid for value in row if value]


def run_audit(destination: Path | str | None = None, *, seeds=(0, 17, 29, 63)) -> dict:
    adapter = _load_adapter()
    settings_checked = 0
    minimum_demo_survivors = 0
    metric_pairs_checked = 0
    metric_outputs_differ = 0
    region_checks = 0
    stress_cases_checked = 0

    for seed in seeds:
        inputs_by_setting = []
        for chosen in SETTINGS:
            episode = adapter.generate(seed, chosen, 2, 4)
            inputs_by_setting.append([
                pair["input"] for split in ("train", "test") for pair in episode[split]
            ])
            expected = [pair["output"] for pair in episode["train"]]
            survivors = []
            for candidate in SETTINGS:
                observed = [adapter.solve(pair["input"], candidate["distance_metric"])
                            for pair in episode["train"]]
                if observed == expected:
                    survivors.append(candidate)
            settings_checked += 1
            if survivors == [chosen]:
                minimum_demo_survivors += 1
        if inputs_by_setting[0] != inputs_by_setting[1]:
            raise AssertionError(f"settings changed the input bank for seed {seed}")

        episode = adapter.generate(seed, SETTINGS[0], 6, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                source = pair["input"]
                manhattan = adapter.solve(source, "manhattan")
                chebyshev = adapter.solve(source, "chebyshev")
                metric_pairs_checked += 1
                metric_outputs_differ += manhattan != chebyshev
                colors = _seed_colors(source)
                for output in (manhattan, chebyshev):
                    if (any(value == 8 for row in output for value in row)
                            and all(sum(value == color for row in output for value in row) > 1
                                    for color in colors)):
                        region_checks += 1
                if len(source) == len(source[0]) == 30:
                    occupied = [(r, c) for r, row in enumerate(source)
                                for c, value in enumerate(row) if value]
                    if (len(occupied) == 5
                            and any(r == 0 for r, _ in occupied)
                            and any(r == 29 for r, _ in occupied)
                            and any(c == 0 for _, c in occupied)
                            and any(c == 29 for _, c in occupied)
                            and sum(a != b for ar, br in zip(manhattan, chebyshev)
                                    for a, b in zip(ar, br)) >= 150):
                        stress_cases_checked += 1

    report = {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": "e438ce3e02ce",
        "status": "pass" if (
            minimum_demo_survivors == settings_checked
            and metric_outputs_differ == metric_pairs_checked
            and region_checks == 2 * metric_pairs_checked
            and stress_cases_checked == len(seeds)
        ) else "fail",
        "seeds": list(seeds),
        "settings_checked": settings_checked,
        "minimum_demo_survivors": minimum_demo_survivors,
        "metric_pairs_checked": metric_pairs_checked,
        "metric_outputs_differ": metric_outputs_differ,
        "region_checks": region_checks,
        "stress_cases_checked": stress_cases_checked,
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
