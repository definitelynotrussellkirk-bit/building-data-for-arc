"""Native sampler over the retained tiling-axis rules.

Python labels are claims, verified by the native protected-Racket worker.
Production geometry and historical prototype APIs are unchanged.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes

HERE = Path(__file__).resolve().parent
AXES = ("both", "horizontal", "vertical")
_TEACHING_MOTIF = ((1, 1, 0), (0, 1, 1))


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"tiling_axes"}
            or type(settings["tiling_axes"]) is not str or settings["tiling_axes"] not in AXES):
        raise ValueError("settings must contain exactly tiling_axes=both|horizontal|vertical")
    return settings["tiling_axes"]


@lru_cache(maxsize=1)
def _retained():
    path = HERE / "prototype.py"
    name = "_retained_tiling_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=3)
def _program(axis):
    return _retained().instantiate_rule(axis)


def program(settings):
    return _program(_setting(settings))


def observables(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0])
            or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    scene, errors = _retained().GEN._parse_scene(grid)
    if errors or scene is None:
        raise ValueError("grid is outside the tiling grammar: " + "; ".join(errors))
    holes = []
    for hole in scene["holes"]:
        sr1, sc1, sr2, sc2 = hole["stamp_bbox"]
        color = hole["color"]
        holes.append({"bbox": list(hole["bbox"]), "stamp_bbox": list(hole["stamp_bbox"]),
                      "color": color, "origin": [sr1, sc1], "period": [sr2-sr1+1, sc2-sc1+1],
                      "motif": [[int(grid[r][c] == color) for c in range(sc1, sc2+1)] for r in range(sr1, sr2+1)]})
    return {"height": len(grid), "width": len(grid[0]), "background": scene["background"], "holes": holes}


def _paint(grid, axis, *, phase="stamp", fixed_period=False, first_only=False, solid=False, transpose=False, forced_height=None):
    scene = observables(grid)
    out = deepcopy(grid)
    holes = scene["holes"][:1] if first_only else scene["holes"]
    for hole in holes:
        r1, c1, r2, c2 = hole["bbox"]
        sr1, sc1, sr2, sc2 = hole["stamp_bbox"]
        motif = hole["motif"]
        if fixed_period:
            motif = [row[:2] for row in motif[:2]]
        if transpose:
            motif = [list(row) for row in zip(*motif)]
        if forced_height is not None:
            # On this grammar, cells beyond the stamp bbox do not have its color.
            motif = [motif[r][:] if r < len(motif) else [0]*len(motif[0]) for r in range(forced_height)]
        sh, sw = len(motif), len(motif[0])
        origin_r, origin_c = ((r1, c1) if phase == "hole" else (0, 0) if phase == "canvas" else (sr1, sc1))
        for r in range(r1, r2+1):
            for c in range(c1, c2+1):
                if axis == "horizontal" and not sr1 <= r <= sr2:
                    continue
                if axis == "vertical" and not sc1 <= c <= sc2:
                    continue
                if solid or motif[(r-origin_r) % sh][(c-origin_c) % sw]:
                    out[r][c] = hole["color"]
    return out


def solve(grid, settings):
    """Propose the retained rule's label on a structurally valid tiling scene."""
    return _paint(grid, _setting(settings))


def _stream(seed, split, index):
    raw = hashlib.sha256(f"native-tiling-v1/{seed}/{split}/{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big")), int.from_bytes(raw[:8], "big") % 2**63


def _construct(rng, height, width, boxes, motif_indices, background, *, teaching=False):
    grid = [[background] * width for _ in range(height)]
    colors = rng.sample(range(1, 8), len(boxes))
    for i, (box, motif_index, color) in enumerate(zip(boxes, motif_indices, colors)):
        r1, c1, r2, c2 = box
        motif = _TEACHING_MOTIF if motif_index == 4 else _retained().GEN.MOTIFS[motif_index]
        sh, sw = len(motif), len(motif[0])
        assert r2-r1+1 > sh and c2-c1+1 > sw
        for r in range(r1, r2+1):
            for c in range(c1, c2+1):
                grid[r][c] = 0
        # One nonzero phase offset plus a boundary stamp on the other large hole.
        top, left = ((r1+1, c1+1) if teaching or i == 0 else (r2-sh+1, c2-sw+1))
        for r, row in enumerate(motif):
            for c, bit in enumerate(row):
                if bit:
                    grid[top+r][left+c] = color
    observables(grid)
    return grid


def sample_input(seed, split, index):
    rng, child_seed = _stream(seed, split, index)
    if split == "train" and index == 0:
        return _construct(rng, 8, 10, [(1,1,5,6)], [4], 8, teaching=True)
    if split == "train" and index == 1:
        return _construct(rng, 12, 16, [(1,1,5,6),(6,9,10,14)], [2,3], 9, teaching=True)
    if (split == "train" and index in (2,3)) or (split == "test" and index in (0,1)):
        layouts = ("official_a", "official_c") if split == "train" else ("official_b", "official_d")
        slot = index-2 if split == "train" else index
        return _retained().GEN.generate(child_seed, index, difficulty="hard", layout_profile=layouts[slot],
                                       motif_index=rng.randrange(4), anchor_profile=("corners","edges")[slot],
                                       palette_band=rng.choice(("low","high")), background_color=rng.choice((8,9)))
    height, width = (((22,24),(26,28))[index-4] if split == "train" else ((24,24),(30,30))[index-2])
    hh, hw = height//2-3, width//2-3
    boxes = [(1,1,hh,hw), (height-hh-1,width-hw-1,height-2,width-2)]
    return _construct(rng, height, width, boxes, [rng.randrange(1,4),rng.randrange(4)], rng.choice((8,9)))


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, "seed", 0, 2**63-1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    _setting(settings)
    result = {"task_id": "14c5c68b0201", "seed": seed, "settings": deepcopy(settings),
              "program_solution": program(settings)}
    for split, count in (("train",demos),("test",queries)):
        result[split] = []
        for index in range(count):
            grid = sample_input(seed, split, index)
            result[split].append({"input": grid, "output": solve(grid, settings)})
    return result


def visible_turn(episode, index):
    _integer(index, "query index", 0, len(episode["test"])-1)
    return {"train": [{"input":deepcopy(p["input"]),"output":deepcopy(p["output"])} for p in episode["train"]],
            "test": [{"input":deepcopy(episode["test"][index]["input"])}]}


def rival_names(settings):
    axis = _setting(settings)
    names = ["axis_"+other for other in AXES if other != axis] + [
        "identity", "solid_fill", "hole_origin_phase", "canvas_origin_phase", "fixed_2x2",
        "first_hole_only", "fixed_background_8", "transpose_stamp"]
    # A fixed row period is answer-equivalent under horizontal-only expansion.
    if axis != "horizontal":
        names.append("fixed_height_3")
    return names


def rival_output(name, grid, settings):
    axis = _setting(settings)
    if name.startswith("axis_") and name[5:] in AXES:
        return _paint(grid, name[5:])
    if name == "identity":
        return deepcopy(grid)
    if name == "fixed_background_8":
        return _paint(grid,axis) if observables(grid)["background"] == 8 else deepcopy(grid)
    options = {"solid_fill":{"solid":True}, "hole_origin_phase":{"phase":"hole"},
               "canvas_origin_phase":{"phase":"canvas"}, "fixed_2x2":{"fixed_period":True},
               "first_hole_only":{"first_only":True}, "transpose_stamp":{"transpose":True},
               "fixed_height_3":{"forced_height":3}}
    if name not in options:
        raise ValueError("unknown rival")
    return _paint(grid, axis, **options[name])


def teaching_report(train, settings):
    if not train:
        raise ValueError("demonstrations are required")
    rows = []
    for name in rival_names(settings):
        index = next((i for i,p in enumerate(train) if rival_output(name,p["input"],settings) != p["output"]),None)
        rows.append({"name":name,"counterexample_demo":index})
    return {"rival_count":len(rows), "all_refuted":all(row["counterexample_demo"] is not None for row in rows),
            "rivals":rows, "scope":"finite demonstration-only alternatives"}


def write_batch(episodes, out):
    staged, seen, turns_seen = [], set(), set()
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = hashlib.sha256(payload).hexdigest()
        if identifier in seen:
            raise ValueError("duplicate visible episode")
        seen.add(identifier)
        turns = []
        for index in range(len(episode["test"])):
            raw = public_challenge_bytes(visible_turn(episode,index))
            turn_id = hashlib.sha256(raw).hexdigest()
            if turn_id in turns_seen:
                raise ValueError("duplicate visible query turn")
            turns_seen.add(turn_id)
            turns.append((turn_id,raw))
        staged.append((identifier,payload,turns,episode))
    if not staged:
        raise ValueError("at least one episode is required")
    staged.sort(key=lambda row:row[0])
    target=Path(out)
    target.mkdir(parents=True,exist_ok=False)
    (target/'public').mkdir(); (target/'turns').mkdir()
    private=[]
    for identifier,payload,turns,episode in staged:
        (target/'public'/f'{identifier}.json').write_bytes(payload)
        for turn_id,raw in turns:
            (target/'turns'/f'{turn_id}.json').write_bytes(raw)
        private.append({'public_id':identifier,'turn_ids':[row[0] for row in turns],'episode':episode})
    (target/'private.json').write_text(json.dumps({'episodes':private},sort_keys=True)+'\n')
    return {'public_ids':[row[0] for row in staged],'turn_count':sum(len(row[2]) for row in staged)}
