"""Bounded adversarial audit for the 78332cb0 panel-chain family."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("audit_78332cb0_engine", HOME / "engine.py")
engine = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = engine
_spec.loader.exec_module(engine)


def source_order(grid):
    state = engine.analyze(grid)
    return engine._assemble(state["panels"], state["orientation"], None)


def reversed_chain(grid):
    state = engine.analyze(grid)
    return engine._assemble(list(reversed(state["ordered"])), state["orientation"], None)


def color_sorted(grid):
    state = engine.analyze(grid)
    return engine._assemble(sorted(state["panels"], key=lambda p: (p.color, p.source_index)), state["orientation"], None)


def wrong_source_center(grid):
    return engine.solve_wrong_source_center(grid)


def first_chain_panel(grid):
    state = engine.analyze(grid)
    return engine._assemble(state["ordered"], state["orientation"], state["ordered"][0].source_index)


def largest_ink_panel(grid):
    state = engine.analyze(grid)
    chosen = max(state["ordered"], key=lambda p: (sum(v != 7 for row in p.grid for v in row), p.source_index))
    return engine._assemble(state["ordered"], state["orientation"], chosen.source_index)


RIVALS = {
    "source_order": source_order,
    "reversed_chain": reversed_chain,
    "color_sorted": color_sorted,
    "wrong_source_center": wrong_source_center,
    "first_chain_panel": first_chain_panel,
    "largest_ink_panel": largest_ink_panel,
}
MEANINGS = {
    "source_order": "preserve occupied panels in source reading order",
    "reversed_chain": "follow the contact chain in the opposite direction",
    "color_sorted": "sort panels by foreground color instead of contacts",
    "wrong_source_center": "highlight the source-reading-order center panel",
    "first_chain_panel": "highlight the first panel instead of the chain center",
    "largest_ink_panel": "highlight the panel with most foreground cells",
}


def binding(path):
    return {"path": path.relative_to(HOME.parents[2]).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def run(out: Path, seeds=(0, 17, 43, 97), demos=2):
    survivors = []
    episodes = 0
    exact_30 = 0
    for seed in seeds:
        demo_inputs, query_inputs = engine.input_bank(seed)
        exact_30 += sum(len(g) == len(g[0]) == 30 for g in demo_inputs + query_inputs)
        for finish in engine.PARAMETERS["finish"]:
            episodes += 1
            expected = [engine.solve(grid, finish) for grid in demo_inputs[:demos]]
            names = ("source_order", "reversed_chain", "color_sorted") if finish == "chain_only" else (
                "wrong_source_center", "first_chain_panel", "largest_ink_panel")
            for name in names:
                if [RIVALS[name](grid) for grid in demo_inputs[:demos]] == expected:
                    survivors.append({"seed": seed, "finish": finish, "rival": name})
    report = {
        "schema": "arcpuzzles-bounded-authoring-audit-v1",
        "task_id": engine.TASK_ID,
        "status": "passed" if not survivors else "failed",
        "seeds": list(seeds),
        "demos": demos,
        "episodes": episodes,
        "exact_30x30_inputs": exact_30,
        "rivals": MEANINGS,
        "survivors": survivors,
        "limits": "Finite named rivals and seeds; no universal uniqueness claim.",
        "source_binding": [binding(HOME / "engine.py"), binding(Path(__file__)), binding(HOME / "canonical.rkt")],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({"status": result["status"], "episodes": result["episodes"], "survivors": result["survivors"]}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "passed" else 1)
