"""Finite demonstration-only rival audit for the cursor-route family."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_cursor_audit_adapter_" + str(BASE).encode().hex(), BASE / "adapter.py")
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)
model = adapter.model

RIVALS = (
    "header",
    "reverse",
    "identity_body",
    "first_command_only",
    "last_command_only",
    "straight_up_only",
    "horizontal_output_mirror",
    "vertical_output_mirror",
    "erase_targets",
    "paint_route_bbox",
)


def _paint_routes(grid, indices):
    data = model.analyze(grid, "header")
    out = [row[:] for row in data["body"]]
    n = data["cursor"]["size"]
    for index in indices:
        for r, c in data["route_summary"][index]["positions"]:
            for rr in range(r, r + n):
                for cc in range(c, c + n):
                    out[rr][cc] = 8
    return out


def predict(grid, rival, setting):
    mode = adapter.checked(setting)
    if rival in adapter.VALUES:
        return model.solve(grid, rival)
    data = model.analyze(grid, mode)
    if rival == "identity_body":
        return [row[:] for row in data["body"]]
    if rival == "first_command_only":
        return _paint_routes(grid, [0])
    if rival == "last_command_only":
        return _paint_routes(grid, [3])
    if rival == "straight_up_only":
        out = [row[:] for row in data["body"]]
        r, c, n = data["cursor"]["r"], data["cursor"]["c"], data["cursor"]["size"]
        while r >= 0:
            for rr in range(r, min(r + n, len(out))):
                for cc in range(c, min(c + n, len(out[0]))):
                    out[rr][cc] = 8
            r -= 1
        return out
    intended = model.solve(grid, mode)
    if rival == "horizontal_output_mirror":
        return [row[::-1] for row in intended]
    if rival == "vertical_output_mirror":
        return intended[::-1]
    if rival == "erase_targets":
        out = copy.deepcopy(intended)
        bg = data["background"]
        for obj in data["objects"]:
            for r, c in obj["cells"]:
                if out[r][c] != 8:
                    out[r][c] = bg
        return out
    if rival == "paint_route_bbox":
        out = [row[:] for row in data["body"]]
        points = [p for route in data["route_summary"] for p in route["positions"]]
        n = data["cursor"]["size"]
        r0 = min(r for r, _ in points); c0 = min(c for _, c in points)
        r1 = max(r + n - 1 for r, _ in points); c1 = max(c + n - 1 for _, c in points)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = 8
        return out
    raise ValueError("unknown rival")


def audit(seeds, demo_counts):
    result = {
        "schema": "cursor-route-finite-rival-audit-v1",
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "rivals": list(RIVALS),
        "episodes": 0,
        "pairs": 0,
        "failures": [],
        "survivors": [],
        "limits": "Finite declared Python rivals; protected Racket parity and causal evidence are separate checks.",
    }
    for seed in result["seeds"]:
        for demos in result["demo_counts"]:
            for setting in adapter.SETTINGS:
                episode = adapter.generate(seed, copy.deepcopy(setting), demos, 4)
                survivors = []
                for rival in RIVALS:
                    if all(predict(pair["input"], rival, setting) == pair["output"] for pair in episode["train"]):
                        survivors.append(rival)
                        for index, pair in enumerate(episode["test"]):
                            if predict(pair["input"], rival, setting) != pair["output"]:
                                result["failures"].append(
                                    {"seed": seed, "demos": demos, "settings": setting, "rival": rival, "query": index}
                                )
                result["survivors"].append(
                    {"seed": seed, "demos": demos, "settings": setting, "rules": survivors}
                )
                result["episodes"] += 1
                result["pairs"] += demos + 4
    result["status"] = "failed" if result["failures"] else "passed"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(range(args.seeds), (2, 3, 6))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "episodes", "pairs", "failures")}))
    raise SystemExit(report["status"] != "passed")
