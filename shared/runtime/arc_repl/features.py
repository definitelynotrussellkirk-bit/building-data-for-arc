"""
Feature computation registry — computable facts about grids, pairs, and tasks.

Each feature is registered with metadata for help/discovery.
"""

import numpy as np
from collections import Counter, defaultdict
from .registry import register_feature, FEATURE_REGISTRY
from .grid_ops import (find_objects, find_enclosed, bounding_box,
                       grid_colors, where_color, object_properties, spatial_relation)


# ============================================================
# Pair-level features (need input + output)
# ============================================================

@register_feature("pair", "diff <in_ref> <out_ref>", "Cell-level delta between input and output", "feature! diff @1 @2")
def diff(input_grid, output_grid):
    inp, out = np.array(input_grid), np.array(output_grid)
    if inp.shape != out.shape:
        return {"error": "shape_mismatch", "in": list(inp.shape), "out": list(out.shape)}
    delta = (out - inp).astype(int)
    mask = inp != out
    return {
        "changed": int(mask.sum()),
        "total": inp.size,
        "delta_values": sorted(set(delta[mask].tolist())) if mask.any() else [],
        "transitions": dict(Counter(
            (int(inp[r, c]), int(out[r, c])) for r, c in zip(*np.where(mask))
        )),
    }


@register_feature("pair", "change_type <in_ref> <out_ref>", "Classify changes: vanished/appeared/recolored", "feature! change_type @1 @2")
def change_type(input_grid, output_grid):
    inp, out = np.array(input_grid), np.array(output_grid)
    if inp.shape != out.shape:
        return {"error": "shape_mismatch"}
    mask = inp != out
    counts = {"vanished": 0, "appeared": 0, "recolored": 0}
    for r, c in zip(*np.where(mask)):
        old, new = int(inp[r, c]), int(out[r, c])
        if old != 0 and new == 0:
            counts["vanished"] += 1
        elif old == 0 and new != 0:
            counts["appeared"] += 1
        else:
            counts["recolored"] += 1
    return counts


@register_feature("pair", "change_mask <in_ref> <out_ref>", "Binary grid: 1 where changed, 0 where same")
def change_mask(input_grid, output_grid):
    inp, out = np.array(input_grid), np.array(output_grid)
    if inp.shape != out.shape:
        return {"error": "shape_mismatch"}
    return (inp != out).astype(int).tolist()


# ============================================================
# Grid-level features (need one grid)
# ============================================================

@register_feature("grid", "enclosure <grid_ref>", "Find enclosed background regions", "feature! enclosure @1")
def enclosure(grid, bg=0):
    enclosed = find_enclosed(grid, bg)
    positions = [(int(r), int(c)) for r, c in zip(*np.where(enclosed))]
    return {"count": len(positions), "positions": positions}


@register_feature("grid", "lattice <grid_ref>", "Detect lattice/tile structure", "feature! lattice @1")
def lattice(grid, bg=0):
    g = np.array(grid)
    h, w = g.shape
    sep_rows = [r for r in range(h) if len(set(g[r, :].tolist())) <= 1]
    sep_cols = [c for c in range(w) if len(set(g[:, c].tolist())) <= 1]
    if len(sep_rows) < 1 or len(sep_cols) < 1:
        return {"detected": False}

    def ranges(seps, total):
        result, start = [], None
        seps_set = set(seps)
        for i in range(total):
            if i not in seps_set:
                if start is None: start = i
            else:
                if start is not None:
                    result.append((start, i - 1))
                    start = None
        if start is not None:
            result.append((start, total - 1))
        return result

    row_ranges = ranges(sep_rows, h)
    col_ranges = ranges(sep_cols, w)
    tiles = []
    for ri, (r0, r1) in enumerate(row_ranges):
        for ci, (c0, c1) in enumerate(col_ranges):
            tile = g[r0:r1+1, c0:c1+1]
            tiles.append({"pos": (ri, ci), "bbox": (r0, c0, r1, c1),
                         "data": tile.tolist(), "key": tile.tobytes()})

    if len(tiles) < 4:
        return {"detected": False}

    key_counts = Counter(t["key"] for t in tiles)
    default_key = key_counts.most_common(1)[0][0]
    default_tile = next(t["data"] for t in tiles if t["key"] == default_key)
    signals = [{"pos": t["pos"], "bbox": t["bbox"], "data": t["data"]}
               for t in tiles if t["key"] != default_key]

    return {"detected": True, "shape": (len(row_ranges), len(col_ranges)),
            "n_tiles": len(tiles), "n_signals": len(signals),
            "signals": signals, "default_tile": default_tile}


@register_feature("grid", "objects <grid_ref>", "Connected components per color", "feature! objects @1")
def objects(grid, bg=0):
    return find_objects(grid, bg)


@register_feature("grid", "symmetry <grid_ref>", "Check for mirror/rotation symmetries", "feature! symmetry @1")
def symmetry(grid):
    g = np.array(grid)
    h, w = g.shape
    result = {
        "mirror_lr": bool(np.array_equal(g, np.fliplr(g))),
        "mirror_ud": bool(np.array_equal(g, np.flipud(g))),
        "rot_180": bool(np.array_equal(g, np.rot90(g, 2))),
    }
    if h == w:
        result["rot_90"] = bool(np.array_equal(g, np.rot90(g, 1)))
        result["transpose"] = bool(np.array_equal(g, g.T))
    return result


@register_feature("grid", "color_frequency <grid_ref>", "Count of each color", "feature! color_frequency @1")
def color_frequency(grid):
    g = np.array(grid)
    colors, counts = np.unique(g, return_counts=True)
    return {int(c): int(n) for c, n in zip(colors, counts)}


@register_feature("grid", "border_pattern <grid_ref>", "Colors on each border edge", "feature! border_pattern @1")
def border_pattern(grid):
    g = np.array(grid)
    h, w = g.shape
    return {
        "top": g[0, :].tolist(),
        "bottom": g[h-1, :].tolist(),
        "left": g[:, 0].tolist(),
        "right": g[:, w-1].tolist(),
    }


@register_feature("grid", "object_summary <grid_ref>", "Summary of all objects with properties")
def object_summary(grid, bg=0):
    objs = find_objects(grid, bg)
    return [{"color": o["color"], **object_properties(o)} for o in objs]


@register_feature("grid", "periodicity <grid_ref> <axis>", "Detect repeating row/col patterns")
def periodicity(grid, axis="both"):
    g = np.array(grid)
    h, w = g.shape
    result = {}
    if axis in ("row", "both"):
        for period in range(1, h // 2 + 1):
            if h % period == 0:
                tile = g[:period, :]
                if all(np.array_equal(g[i*period:(i+1)*period, :], tile) for i in range(h // period)):
                    result["row_period"] = period
                    break
    if axis in ("col", "both"):
        for period in range(1, w // 2 + 1):
            if w % period == 0:
                tile = g[:, :period]
                if all(np.array_equal(g[:, i*period:(i+1)*period], tile) for i in range(w // period)):
                    result["col_period"] = period
                    break
    return result


@register_feature("grid", "adjacency_graph <grid_ref>", "Which colors are adjacent to which")
def adjacency_graph(grid, bg=0):
    g = np.array(grid)
    h, w = g.shape
    edges = set()
    for r in range(h):
        for c in range(w):
            if g[r, c] == bg:
                continue
            for nr, nc in [(r+1, c), (r, c+1)]:
                if 0 <= nr < h and 0 <= nc < w and g[nr, nc] != bg and g[nr, nc] != g[r, c]:
                    edge = tuple(sorted([int(g[r, c]), int(g[nr, nc])]))
                    edges.add(edge)
    return {"edges": sorted(edges)}


# ============================================================
# Task-level features (use full task)
# ============================================================

@register_feature("task", "color_roles", "Per-color role: invariant/source/target/mixed", "feature! color_roles")
def color_roles(task):
    info = {}
    n = 0
    for pair in task["train"]:
        if "output" not in pair:
            continue
        inp, out = np.array(pair["input"]), np.array(pair["output"])
        if inp.shape != out.shape:
            continue
        n += 1
        for v in range(10):
            if v not in info:
                info[v] = {"kept": 0, "lost": 0, "gained": 0}
            in_m, out_m = inp == v, out == v
            info[v]["kept"] += int((in_m & out_m).sum())
            info[v]["lost"] += int((in_m & ~out_m).sum())
            info[v]["gained"] += int((~in_m & out_m).sum())
    result = {}
    for c, i in info.items():
        if i["kept"] == 0 and i["lost"] == 0 and i["gained"] == 0:
            continue
        if i["lost"] == 0 and i["gained"] == 0: role = "invariant"
        elif i["lost"] > 0 and i["gained"] == 0: role = "source"
        elif i["lost"] == 0 and i["gained"] > 0: role = "target"
        else: role = "mixed"
        result[c] = {"role": role, **i}
    return result


@register_feature("task", "input_invariant", "Cells identical across all train inputs", "feature! input_invariant")
def input_invariant(task):
    grids = [np.array(p["input"]) for p in task["train"]]
    if len(grids) < 2:
        return {"error": "need 2+ pairs"}
    if len(set(g.shape for g in grids)) != 1:
        return {"error": "different shapes"}
    stacked = np.stack(grids)
    inv = np.all(stacked == stacked[0], axis=0)
    return {"invariant_count": int(inv.sum()), "total": inv.size,
            "invariant_ratio": round(int(inv.sum()) / inv.size, 4)}


@register_feature("task", "output_invariant", "Cells identical across all train outputs", "feature! output_invariant")
def output_invariant(task):
    grids = [np.array(p["output"]) for p in task["train"] if "output" in p]
    if len(grids) < 2:
        return {"error": "need 2+ pairs"}
    if len(set(g.shape for g in grids)) != 1:
        return {"error": "different shapes"}
    stacked = np.stack(grids)
    inv = np.all(stacked == stacked[0], axis=0)
    return {"invariant_count": int(inv.sum()), "total": inv.size,
            "invariant_ratio": round(int(inv.sum()) / inv.size, 4)}


@register_feature("task", "shape_change", "How do input/output dimensions relate across pairs")
def shape_change(task):
    results = []
    for pair in task["train"]:
        if "output" not in pair:
            continue
        inp = np.array(pair["input"])
        out = np.array(pair["output"])
        results.append({
            "in": list(inp.shape), "out": list(out.shape),
            "same": inp.shape == out.shape,
            "ratio": (round(out.shape[0] / inp.shape[0], 2), round(out.shape[1] / inp.shape[1], 2)),
        })
    return results


@register_feature("task", "object_count_change", "How object count changes across pairs")
def object_count_change(task):
    results = []
    for pair in task["train"]:
        if "output" not in pair:
            continue
        in_objs = len(find_objects(pair["input"]))
        out_objs = len(find_objects(pair["output"]))
        results.append({"in": in_objs, "out": out_objs, "delta": out_objs - in_objs})
    return results


@register_feature("task", "consistent_mapping", "Check if same color mapping applies to all pairs")
def consistent_mapping(task):
    mappings = []
    for pair in task["train"]:
        if "output" not in pair:
            continue
        inp, out = np.array(pair["input"]), np.array(pair["output"])
        if inp.shape != out.shape:
            return {"consistent": False, "reason": "shape_mismatch"}
        m = {}
        for r in range(inp.shape[0]):
            for c in range(inp.shape[1]):
                ic, oc = int(inp[r, c]), int(out[r, c])
                if ic in m:
                    if m[ic] != oc:
                        m[ic] = None  # inconsistent within pair
                else:
                    m[ic] = oc
        mappings.append(m)

    if not mappings:
        return {"consistent": False}

    # Check consistency across pairs
    common = {}
    for m in mappings:
        for k, v in m.items():
            if v is None:
                continue
            if k in common:
                if common[k] != v:
                    common[k] = None
            else:
                common[k] = v

    clean = {k: v for k, v in common.items() if v is not None}
    return {"consistent": len(clean) > 0, "mapping": clean}


# ============================================================
# Legacy compatibility: PAIR_FEATURES, GRID_FEATURES, TASK_FEATURES
# Keep these for the executor's existing dispatch logic
# ============================================================

PAIR_FEATURES = {name: entry.fn for name, entry in FEATURE_REGISTRY.items() if entry.level == "pair"}
GRID_FEATURES = {name: entry.fn for name, entry in FEATURE_REGISTRY.items() if entry.level == "grid"}
TASK_FEATURES = {name: entry.fn for name, entry in FEATURE_REGISTRY.items() if entry.level == "task"}
