"""Bounded adversarial audit for the e87109e9 native family."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("audit_e871_engine", HOME / "engine.py")
engine = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = engine
_spec.loader.exec_module(engine)


def _paint(state, cells):
    out = [row[:] for row in state["body"]]
    for r, c in cells:
        if out[r][c] in (state["background"], 8):
            out[r][c] = 8
    return out


def no_bounce(grid):
    state = engine.parse(grid)
    h, w = len(state["body"]), len(state["body"][0])
    pos = (state["source_bbox"][0], state["source_bbox"][1])
    cells = set(state["source_cells"])
    for color, hand in state["instructions"]:
        candidates = []
        for direction in engine.DIRECTIONS:
            leg = engine._seek(pos, direction, state["source_size"], h, w, state["obstacles"])
            if leg[2] is not None and leg[2].color == color:
                candidates.append((direction, leg))
        if not candidates:
            cells.update(engine._seek(pos, (-1, 0), state["source_size"], h, w, state["obstacles"])[0])
            continue
        direction, leg = candidates[0]
        cells.update(leg[0])
        direction = engine._turn(direction, hand)
        tail = engine._seek(leg[1], direction, state["source_size"], h, w, state["obstacles"])
        cells.update(tail[0])
    return _paint(state, cells)


def opposite_hand(grid):
    changed = [row[:] for row in grid]
    for start in range(0, len(changed[0]), 6):
        left = any(changed[r][start + 1] != 0 for r in range(1, 5))
        src, dst = (start + 1, start + 4) if left else (start + 4, start + 1)
        for r in range(1, 5):
            changed[r][dst] = changed[r][src]
            changed[r][src] = 0
    return engine.solve(changed, "trace_only")


def cardinal_cross(grid):
    state = engine.parse(grid)
    h, w = len(state["body"]), len(state["body"][0])
    pos = (state["source_bbox"][0], state["source_bbox"][1])
    cells = set(state["source_cells"])
    for direction in engine.DIRECTIONS:
        cells.update(engine._seek(pos, direction, state["source_size"], h, w, state["obstacles"])[0])
    return _paint(state, cells)


def first_instruction_only(grid):
    state = engine.trace(grid)
    return _paint(state, state["source_cells"] | state["routes"][0].cells)


def highlight_first_route(grid):
    return engine.solve_wrong_first_route(grid)


def highlight_largest_object(grid):
    state = engine.trace(grid)
    out = engine.solve(grid, "trace_only")
    selected = max(state["obstacles"], key=lambda obstacle: (len(obstacle.cells), obstacle.color))
    for r, c in selected.cells:
        out[r][c] = 9
    return out


def highlight_most_collisions(grid):
    state = engine.trace(grid)
    out = engine.solve(grid, "trace_only")
    selected = max(state["routes"], key=lambda route: (bool(route.hits), len(route.hits), route.color))
    if selected.hits:
        for r, c in selected.hits[0].cells:
            out[r][c] = 9
    return out


RIVALS = {
    "no_bounce": no_bounce,
    "opposite_hand": opposite_hand,
    "cardinal_cross": cardinal_cross,
    "first_instruction_only": first_instruction_only,
    "highlight_first_route": highlight_first_route,
    "highlight_largest_object": highlight_largest_object,
    "highlight_most_collisions": highlight_most_collisions,
}
MEANINGS = {
    "no_bounce": "stop the post-turn run at its first later rectangle",
    "opposite_hand": "swap every header left/right turn",
    "cardinal_cross": "ignore the header and emit only four straight source rays",
    "first_instruction_only": "execute only the first header instruction",
    "highlight_first_route": "highlight the first header route instead of the derived shortest route",
    "highlight_largest_object": "highlight the largest raw rectangle",
    "highlight_most_collisions": "use maximum collision count instead of minimum routed footprint size",
}


def binding(path):
    return {"path": path.relative_to(HOME.parents[2]).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def run(out: Path, seeds=(0, 17, 43, 97), demos=2):
    failures = []
    episodes = 0
    exact_30 = 0
    for seed in seeds:
        demo_inputs, query_inputs = engine.input_bank(seed)
        exact_30 += sum(len(grid) == len(grid[0]) == 30 for grid in demo_inputs + query_inputs)
        for finish in engine.PARAMETERS["finish"]:
            episodes += 1
            expected = [engine.solve(grid, finish) for grid in demo_inputs[:demos]]
            relevant = ("no_bounce", "opposite_hand", "cardinal_cross", "first_instruction_only") if finish == "trace_only" else (
                "highlight_first_route", "highlight_largest_object", "highlight_most_collisions")
            for name in relevant:
                claims = [RIVALS[name](grid) for grid in demo_inputs[:demos]]
                if claims == expected:
                    failures.append({"seed": seed, "finish": finish, "rival": name})
    report = {
        "schema": "arcpuzzles-bounded-authoring-audit-v1",
        "task_id": engine.TASK_ID,
        "status": "passed" if not failures else "failed",
        "seeds": list(seeds),
        "demos": demos,
        "episodes": episodes,
        "exact_30x30_inputs": exact_30,
        "rivals": MEANINGS,
        "survivors": failures,
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
