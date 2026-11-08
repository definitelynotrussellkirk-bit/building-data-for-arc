"""Finite teaching-rival audit for the thick-cursor route family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_cursor_route_audit_adapter", HERE / "adapter.py")
A = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(A)


def _paint(field, background, cells):
    out = [row[:] for row in field]
    for r, c in cells:
        if field[r][c] in (background, 8):
            out[r][c] = 8
    return out


def _patched_bounce(value, mode, replacement):
    original = A._bounce_extend
    A._bounce_extend = replacement
    try:
        return A.solve(value, mode)
    finally:
        A._bounce_extend = original


def _stop_at_first_blocker(field, background, start, side, vector):
    return A._extend(field, background, start, side, vector), []


def _no_turned_leg(field, background, start, side, vector):
    return set(A._block(start, side)), []


def _all_up(value):
    field, _specs, background, cursor = A._field(value)
    cells = A._extend(field, background, (cursor[0], cursor[1]), cursor[2], A.DIRECTIONS["up"])
    return _paint(field, background, cells)


def predictions(value):
    return {
        "header": A.solve(value, "header"),
        "opposite": A.solve(value, "opposite"),
        "stop_header": _patched_bounce(value, "header", _stop_at_first_blocker),
        "stop_opposite": _patched_bounce(value, "opposite", _stop_at_first_blocker),
        "target_only_header": _patched_bounce(value, "header", _no_turned_leg),
        "target_only_opposite": _patched_bounce(value, "opposite", _no_turned_leg),
        "all_up": _all_up(value),
        "identity_field": [row[:] for row in value[6:]],
    }


def audit(seeds=range(16), demo_counts=(2, 3, 6)):
    seeds = list(seeds)
    demo_counts = tuple(demo_counts)
    harmful = []
    equivalent = []
    episodes = 0
    labeled_pairs = 0
    stress = 0
    rivals = []
    for seed in seeds:
        bank = A.generate(seed, {"turn_rule": "header"}, 6, 4)
        train = [predictions(pair["input"]) for pair in bank["train"]]
        test = [predictions(pair["input"]) for pair in bank["test"]]
        rivals = list(train[0])
        for demos in demo_counts:
            for chosen in A.MODES:
                episodes += 1
                labeled_pairs += demos + 4
                if len(bank["test"][-1]["input"]) == 30:
                    stress += 1
                for rival in rivals:
                    if rival == chosen:
                        continue
                    if not all(row[rival] == row[chosen] for row in train[:demos]):
                        continue
                    record = {"seed": seed, "demos": demos, "setting": chosen, "rival": rival}
                    if any(row[rival] != row[chosen] for row in test):
                        harmful.append(record)
                    else:
                        equivalent.append(record)
    return {
        "schema": "arcpuzzles-finite-teaching-audit-v1",
        "status": "passed" if not harmful else "failed",
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "seeds": seeds,
        "demo_counts": list(demo_counts),
        "rivals": rivals,
        "harmful_survivors": harmful,
        "finite_equivalent_survivors": equivalent,
        "substantive_30x24_episodes": stress,
        "label_backend": "Python claims; protected Racket preflight and causal replay are separate.",
        "limits": "Finite declared rivals and seeds, not universal uniqueness or owner acceptance.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "episodes", "labeled_pairs", "harmful_survivors")}))
    raise SystemExit(report["status"] != "passed")


if __name__ == "__main__":
    main()
