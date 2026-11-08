"""DENSE_MOTION concept family: whole-OBJECT motion on a dense object field.

Each generator places a HANDFUL (6-14) of SUBSTANTIAL multi-cell objects on a
LARGE grid (input area ~250-500) and MOVES every object by one rule that all
pairs in the task share:

  gen1 — gravity to the floor: every object slides straight DOWN to the bottom
         wall (whole-object `move-to-wall`, shape preserved).
  gen2 — slide-to-wall in a per-task direction: every object slides to one of
         the four walls (direction fixed per task, varies across seeds).
  gen3 — magnetism to a central bar: a full-height wall line splits the grid;
         every object slides horizontally until it is flush against the wall
         (`slide-until-contact`).

CRITICAL semantics note: the prelude `gravity` head is PER-CELL column collapse
(it turns objects into streaks and scrambles the component count). These
generators deliberately use the WHOLE-OBJECT heads `move-to-wall` /
`slide-until-contact`, which shift every cell of an object by the SAME offset so
the shape — and hence the component count — is preserved. To keep parity trivial
and the component count fixed, objects are laid out in DISJOINT LANES along the
motion axis, so no two objects ever interact (no collisions, no overwrites).

`objects g` == `(find-objects g 0 4)`: 4-connected, SINGLE-COLOR components. The
Python `_components` finder below matches that exactly.

Shared parity + measurement helpers live here so the bridge wiring is defined
once. Each gen file's __main__ proves byte-exact Racket<->Python parity over >=25
seeds and prints the measured avg input area + component count.
"""
from __future__ import annotations


# --------------------------------------------------------------------------
# component finder — matches prelude `(find-objects g 0 4)` exactly:
# 4-connected, single-color components.
def components(g, bg=0):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    objs = []
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == bg or seen[r][c]:
                continue
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w
                            and not seen[nr][nc] and g[nr][nc] == v):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            objs.append((v, cells))
    return objs


# --------------------------------------------------------------------------
def _program_body(program: str) -> str:
    """Extract BODY from `(rule! (lambda (g) BODY))` by paren-matching."""
    marker = "(lambda (g)"
    i = program.index(marker) + len(marker)
    depth = 1
    j = i
    while j < len(program) and depth > 0:
        if program[j] == "(":
            depth += 1
        elif program[j] == ")":
            depth -= 1
        j += 1
    return program[i:j - 1].strip()


def parity_check(generate_task, *, n=25, version_label=""):
    """Run `generate_task` over n seeds, eval its program body in Racket, assert
    byte-exact equality with every stored output, AND measure avg input area +
    component count. Prints "PARITY: P/T exact" and the stats line."""
    from arc_repl.racket_bridge import RacketBridge

    b = RacketBridge()
    passed = total = 0
    first_fail = None
    areas = []
    comps = []
    changed = 0
    for seed in range(n):
        task = generate_task(seed)
        body = _program_body(task["program"])
        for split in ("train", "test"):
            for pair in task[split]:
                total += 1
                gin = pair["input"]
                areas.append(len(gin) * len(gin[0]))
                comps.append(len(components(gin)))
                if pair["output"] != gin:
                    changed += 1
                b.define_grid("g", gin)
                got = b.eval_text(body)
                if got == pair["output"]:
                    passed += 1
                elif first_fail is None:
                    first_fail = {
                        "seed": seed, "split": split,
                        "dims": (len(gin), len(gin[0])),
                        "py_out": pair["output"], "rkt_out": got,
                    }
    if first_fail is not None:
        print("FIRST MISMATCH:", first_fail)
    tag = f" [{version_label}]" if version_label else ""
    print(f"PARITY: {passed}/{total} exact{tag}")
    avg_area = sum(areas) / len(areas)
    avg_comp = sum(comps) / len(comps)
    print(f"STATS: avg_area={avg_area:.1f} (min {min(areas)}, max {max(areas)}) "
          f"| avg_comps={avg_comp:.2f} (min {min(comps)}, max {max(comps)}) "
          f"| output!=input {changed}/{total}")
    return passed, total
