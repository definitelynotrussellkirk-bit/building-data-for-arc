from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
OUT = ROOT / "checks" / "audit"
CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid, *, color=None, nonzero=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if (r, c) in seen:
                continue
            if color is not None and value != color:
                continue
            if nonzero and value == 0:
                continue
            if color is None and not nonzero:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in CARD:
                    p = rr + dr, cc + dc
                    if not (0 <= p[0] < h and 0 <= p[1] < w) or p in seen:
                        continue
                    nv = grid[p[0]][p[1]]
                    if color is not None and nv == color:
                        seen.add(p); stack.append(p)
                    elif nonzero and nv == value:
                        seen.add(p); stack.append(p)
            out.append((value, cells))
    return out


def bbox(cells):
    rs = [p[0] for p in cells]
    cs = [p[1] for p in cells]
    return min(rs), min(cs), max(rs), max(cs)


def normalized(cells):
    r0, c0, _, _ = bbox(cells)
    return sorted((r-r0, c-c0) for r, c in cells)


def e71_facts(grid):
    all_comps = components(grid, nonzero=True)
    protos = [(v, cells) for v, cells in all_comps if v != 5]
    frames = components(grid, color=5)
    if len(protos) != 1:
        raise ValueError(f"expected one prototype, got {len(protos)}")
    pcolor, pcells = protos[0]
    pr0, pc0, pr1, pc1 = bbox(pcells)
    pdims = (pr1-pr0+1, pc1-pc0+1)
    frame_facts = []
    for _, cells in frames:
        r0, c0, r1, c1 = bbox(cells)
        frame_facts.append({
            "bbox": [r0, c0, r1, c1],
            "interior_dims": [r1-r0-1, c1-c0-1],
        })
    return {
        "prototype_color": pcolor,
        "prototype_bbox": [pr0, pc0, pr1, pc1],
        "prototype_dims": list(pdims),
        "prototype_shape": [list(x) for x in normalized(pcells)],
        "frames": frame_facts,
    }


def modal_rival(grid):
    facts = e71_facts(grid)
    dims = [tuple(f["interior_dims"]) for f in facts["frames"]]
    counts = Counter(dims)
    max_count = max(counts.values())
    winners = sorted(k for k, v in counts.items() if v == max_count)
    if len(winners) != 1:
        return deepcopy(grid), winners
    chosen = winners[0]
    out = deepcopy(grid)
    for frame in facts["frames"]:
        if tuple(frame["interior_dims"]) != chosen:
            continue
        r0, c0, _, _ = frame["bbox"]
        for dr, dc in facts["prototype_shape"]:
            out[r0 + 1 + dr][c0 + 1 + dc] = facts["prototype_color"]
    return out, winners


# b31: advertised degenerate override accepted by its own validator.
b31, b31_path = load("b31e765ef780")
b31_grid = b31.generate(0, 0, texture="all_holed")
b31_dir = OUT / "b31e765ef780"
(b31_dir / "input.json").write_text(json.dumps(b31_grid) + "\n")
b31_comps = components(b31_grid, nonzero=True)
b31_rival = [[8 if value else 0 for value in row] for row in b31_grid]
(b31_dir / "rival.json").write_text(json.dumps(b31_rival) + "\n")
b31_probe = {
    "task_id": "b31e765ef780",
    "generator_sha256": sha(b31_path),
    "seed": 0,
    "sample_index": 0,
    "difficulty": None,
    "overrides": {"texture": "all_holed"},
    "input_shape": [len(b31_grid), len(b31_grid[0])],
    "self_check": b31.self_check(b31_grid),
    "component_count": len(b31_comps),
    "component_colors": [v for v, _ in b31_comps],
    "documented_invariant_violated": "at least one non-holed distractor component",
    "rival": "recolor every nonzero cell cyan",
    "rival_output_path": "checks/audit/b31e765ef780/rival.json",
}
(b31_dir / "probe.json").write_text(json.dumps(b31_probe, indent=2) + "\n")

# e71: independently remeasure the modal-frame-size shortcut.
e71, e71_path = load("e71b8db9e07b")
e71_dir = OUT / "e71b8db9e07b"
trials = 5000
success = 0
ties = 0
failures = 0
first = None
for sample_index in range(trials):
    try:
        grid = e71.generate("audit-mode", sample_index, difficulty="hard")
        facts = e71_facts(grid)
        dims = [tuple(f["interior_dims"]) for f in facts["frames"]]
        counts = Counter(dims)
        top = max(counts.values())
        modal = [d for d, count in counts.items() if count == top]
        if len(modal) != 1:
            ties += 1
        elif modal[0] == tuple(facts["prototype_dims"]):
            success += 1
        if first is None:
            rival, winners = modal_rival(grid)
            first = {
                "sample_index": sample_index,
                "facts": facts,
                "modal_winners": [list(x) for x in winners],
                "input": grid,
                "rival": rival,
                "self_check": e71.self_check(grid),
            }
    except Exception as exc:  # preserve actual generation failures in denominator
        failures += 1
        if first is None:
            first = {"sample_index": sample_index, "error": repr(exc)}

assert first is not None and "input" in first
(e71_dir / "input.json").write_text(json.dumps(first["input"]) + "\n")
(e71_dir / "rival.json").write_text(json.dumps(first["rival"]) + "\n")
# Separate exact-axis reproducer: hard ignores advertised grid_h override.
override_grid = e71.generate(123, 0, difficulty="hard", grid_h=14)
override_observed = [len(override_grid), len(override_grid[0])]
summary = {
    "task_id": "e71b8db9e07b",
    "generator_sha256": sha(e71_path),
    "seed": "audit-mode",
    "difficulty": "hard",
    "sample_index_range": [0, trials - 1],
    "trials": trials,
    "unique_modal_size_equals_prototype_bbox": success,
    "rate": success / trials,
    "modal_ties": ties,
    "generation_failures": failures,
    "example": {
        "sample_index": first["sample_index"],
        "prototype_dims": first["facts"]["prototype_dims"],
        "frame_interior_dims": [f["interior_dims"] for f in first["facts"]["frames"]],
        "modal_winners": first["modal_winners"],
        "self_check": first["self_check"],
        "rival_output_path": "checks/audit/e71b8db9e07b/rival.json",
    },
    "override_probe": {
        "seed": 123,
        "sample_index": 0,
        "difficulty": "hard",
        "overrides": {"grid_h": 14},
        "observed_shape": override_observed,
        "advertised_grid_h_domain": "14..28",
    },
}
(e71_dir / "probe.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({
    "b31": b31_probe,
    "e71": summary,
}, indent=2))
