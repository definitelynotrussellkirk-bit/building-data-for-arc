"""Bounded adversarial self-audit for the template parametric family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_template_verify_prototype", HOME / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
p = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = p
SPEC.loader.exec_module(p)


def audit() -> dict:
    failures = []
    checks = 0
    values = set()
    for seed in range(32):
        for demos in (2, 3, 6):
            episodes = {
                mode: p.generate_pairs(seed, demos, 4, mode)
                for mode in p.MODES
            }
            left = episodes["canonical"]
            right = episodes["match_count_relay"]
            if [x["input"] for x in left] != [x["input"] for x in right]:
                failures.append({"seed": seed, "demos": demos, "finding": "settings changed inputs"})
            if (len(left[-1]["input"]), len(left[-1]["input"][0])) != (30, 30):
                failures.append({"seed": seed, "demos": demos, "finding": "missing 30x30 fourth query"})
            if len({json.dumps(x["input"]) for x in left}) != len(left):
                failures.append({"seed": seed, "demos": demos, "finding": "duplicate inputs"})
            values.update(p.match_count(x["input"]) for x in left)
            rivals = {
                "canonical": p.canonical_output,
                "relay": p.relay_output,
                "literal_zero": p.literal_zero_relay_output,
                "component_count": p.component_count_relay_output,
                "fixed_1": lambda g: p.fixed_relay_output(g, 1),
                "fixed_2": lambda g: p.fixed_relay_output(g, 2),
                "fixed_3": lambda g: p.fixed_relay_output(g, 3),
            }
            for mode, pairs in episodes.items():
                demos_pairs, query_pairs = pairs[:demos], pairs[demos:]
                correct_name = "canonical" if mode == "canonical" else "relay"
                for name, rival in rivals.items():
                    if name == correct_name:
                        continue
                    checks += 1
                    survives = all(rival(x["input"]) == x["output"] for x in demos_pairs)
                    changes_query = any(rival(x["input"]) != x["output"] for x in query_pairs)
                    if survives and changes_query:
                        failures.append({
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "rival": name,
                            "finding": "rival fits every demo and changes a query",
                        })
    return {
        "schema": "0eb83be0298d-parametric-self-audit-v1",
        "seeds": 32,
        "demo_counts": [2, 3, 6],
        "query_count": 4,
        "episodes": 32 * 3 * 2,
        "rival_checks": checks,
        "match_counts": sorted(values),
        "failures": failures,
        "status": "passed" if not failures and values == {1, 2, 3} else "failed",
        "limits": "Finite named-rival audit; not a proof against every possible rule.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
