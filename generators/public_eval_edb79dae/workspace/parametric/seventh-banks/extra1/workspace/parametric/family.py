#!/usr/bin/env python3
"""Direct public-parent legend/template grammar; owner registration pending.

The executable parameter is mapping_policy=once|terminal. Both policies fit the
two public demonstrations; the supplied public test solution selects once. New lessons
deliberately contain chains and disconnected templates to teach the distinction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK_ID = "public_eval_edb79dae"
POLICIES = ("once", "terminal")
RIVALS = (*POLICIES, "two_hops", "three_hops", "no_recolor", "full_blocks",
          "first_template", "destination_template", "largest_component")
SOURCE_ID = "edb79dae"
SOURCE_CHALLENGE_SHA256 = "c9190b5e5bdd993afe9b9048180eebf462a222b6597f33d4d8da0ac950544a85"
SOURCE_FILE = "shared/data/raw/arc-agi_evaluation_challenges.json"
OFFSETS = ((1, 0), (-1, 0), (0, 1), (0, -1))
ARROW_SOURCE_CELLS = {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def groups(cells):
    unseen = set(cells)
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        found, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for dr, dc in OFFSETS:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    found.add(point)
                    queue.append(point)
        result.append(found)
    return sorted(result, key=lambda points: (-len(points), sorted(points)))


def bounds(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def parse_grid(grid):
    """Admit an explicit input grammar; never use seed/settings to parse roles."""
    validate_grid(grid)
    h, w = len(grid), len(grid[0])
    counts = Counter(v for row in grid for v in row)
    ordered = counts.most_common()
    if len(ordered) < 4 or ordered[0][1] == ordered[1][1]:
        raise ValueError("need unique modal background and role colors")
    bg = ordered[0][0]
    objects = []
    for color in sorted(set(counts) - {bg}):
        objects.extend((color, part) for part in groups({(r, c) for r in range(h)
                       for c in range(w) if grid[r][c] == color}))
    frames = []
    for color, points in objects:
        r0, c0, r1, c1 = bounds(points)
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        if (fh >= 5 and fw >= 5 and len(points) == 2 * (fh + fw) - 4
                and all(r in (r0, r1) or c in (c0, c1) for r, c in points)):
            frames.append((color, (r0, c0, r1, c1)))
    if len(frames) != 1:
        raise ValueError("need exactly one hollow rectangular frame")
    frame_color, frame = frames[0]
    r0, c0, r1, c1 = frame

    def inside(r, c):
        return r0 <= r <= r1 and c0 <= c <= c1

    arrows, arrow_cells, mapping = [], set(), {}
    for r in range(h - 2):
        for c in range(w - 3):
            source, target = grid[r][c], grid[r][c + 2]
            if source == target or {source, target} & {bg, frame_color}:
                continue
            points = {(r + dr, c + dc) for dr in range(3) for dc in range(4)}
            if any(inside(*p) for p in points):
                continue
            if any(grid[r + dr][c + dc] != (source if (dr, dc) in ARROW_SOURCE_CELLS else target)
                   for dr in range(3) for dc in range(4)):
                continue
            if points & arrow_cells or source in mapping:
                raise ValueError("overlapping or duplicate-source legend tiles")
            arrows.append((r, c, source, target))
            arrow_cells.update(points)
            mapping[source] = target
    if not 2 <= len(mapping) <= 5:
        raise ValueError("need two to five unambiguous directed legend tiles")
    for start in mapping:
        seen, node = set(), start
        while node in mapping:
            if node in seen:
                raise ValueError("legend cycle is outside the shared once/terminal grammar")
            seen.add(node)
            node = mapping[node]

    raw_templates = {}
    for r in range(h):
        for c in range(w):
            if not inside(r, c) and (r, c) not in arrow_cells and grid[r][c] != bg:
                raw_templates.setdefault(grid[r][c], set()).add((r, c))
    if set(raw_templates) != set(mapping):
        raise ValueError("one complete exterior template is required for every legend source")
    blocks = []
    for color, points in objects:
        if not all(r0 < r < r1 and c0 < c < c1 for r, c in points):
            continue
        br0, bc0, br1, bc1 = bounds(points)
        n = br1 - br0 + 1
        if color not in mapping or n != bc1 - bc0 + 1 or len(points) != n * n:
            raise ValueError("frame content must be solid source-colored square blocks")
        blocks.append({"color": color, "bbox": (br0, bc0, br1, bc1), "size": n})
    if not blocks or len({block["size"] for block in blocks}) != 1:
        raise ValueError("occupied blocks must have one common square size")
    n = blocks[0]["size"]
    if not 3 <= n <= 5 or set(block["color"] for block in blocks) != set(mapping):
        raise ValueError("square size must be3..5 and every source must occur inside frame")
    templates = {}
    for color, points in raw_templates.items():
        tr0, tc0, tr1, tc1 = bounds(points)
        if tr1 - tr0 + 1 != n or tc1 - tc0 + 1 != n or len(points) >= n * n:
            raise ValueError("each template must span one non-solid square bounding box")
        templates[color] = {(r - tr0, c - tc0) for r, c in points}
    if any(grid[r][c] == frame_color for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
        raise ValueError("frame color cannot occur in its interior")
    return {"background": bg, "frame_color": frame_color, "frame": frame,
            "arrows": arrows, "mapping": mapping, "templates": templates,
            "blocks": sorted(blocks, key=lambda b: b["bbox"]), "tile_size": n}


def _predict_base(grid, policy="once"):
    """Python mirror and declared finite rivals; retained labels come from Racket."""
    if type(policy) is not str or policy not in RIVALS:
        raise ValueError("unknown mapping policy or rival")
    p = parse_grid(grid)
    r0, c0, r1, c1 = p["frame"]
    out = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    for block in p["blocks"]:
        source = block["color"]
        color = source
        hops = {"terminal": 9, "two_hops": 2, "three_hops": 3, "no_recolor": 0}.get(policy, 1)
        for _ in range(hops):
            color = p["mapping"].get(color, color)
        template_color = source
        if policy == "first_template":
            template_color = min(p["templates"])
        elif policy == "destination_template" and color in p["templates"]:
            template_color = color
        mask = p["templates"][template_color]
        if policy == "largest_component":
            mask = groups(mask)[0]
        if policy == "full_blocks":
            mask = {(r, c) for r in range(block["size"]) for c in range(block["size"])}
        br, bc, _, _ = block["bbox"]
        for dr in range(block["size"]):
            for dc in range(block["size"]):
                out[br - r0 + dr][bc - c0 + dc] = color if (dr, dc) in mask else p["background"]
    return out


_BASE_RIVALS=RIVALS
RIVALS=RIVALS+("global_terminal",)+tuple(f"fixed_color_{c}" for c in range(10))
def predict(grid,policy="once"):
 if policy in _BASE_RIVALS:return _predict_base(grid,policy)
 p=parse_grid(grid);out=_predict_base(grid,'once');r0,c0,_,_=p['frame']
 color=min(set(p['mapping'].values())-set(p['mapping'])) if policy=='global_terminal' else int(policy.rsplit('_',1)[1])
 for block in p['blocks']:
  br,bc,_,_=block['bbox']
  for dr,dc in p['templates'][block['color']]:out[br-r0+dr][bc-c0+dc]=color
 return out

def fit_rivals(demos):
    """Only demonstrations determine survival; no query inputs or answers here."""
    if type(demos) is not list or not demos:
        raise ValueError("need nonempty demonstrations")
    return [name for name in RIVALS if all(predict(pair["input"], name) == pair["output"] for pair in demos)]


def sample_input(seed, index):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000000, "index")
    rng = random.Random(int(digest(f"legend-template-v1:{seed}:{index}".encode()), 16))
    n = 3 + index % 3
    k = 4 if index == 0 else 2 + index % 3
    palette = rng.sample(range(10), k + 3)
    bg, frame_color = palette[:2]
    sources, terminal = palette[2:-1], palette[-1]
    mapping = dict(zip(sources, sources[1:] + [terminal]))
    fh = fw = 3 * (n + 1) + 3
    left = bool(index % 2)
    if left:
        fr, fc = 8, 0
        template_slots = [(i * (n + 1), fw + 2) for i in range(k)]
        arrow_slots = [(4 * (i // 2), 5 * (i % 2)) for i in range(k)]
        height, width = max(fr + fh, k * (n + 1) - 1), fw + n + 2
    else:
        fr, fc = n + 2, 6
        template_slots = [(0, 6 + i * (n + 1)) for i in range(k)]
        arrow_slots = [(4 * i, 0) for i in range(k)]
        height, width = max(fr + fh, 4 * k - 1), max(fc + fw, 6 + k * (n + 1) - 1)
    shift_r, shift_c = rng.randrange(2), rng.randrange(2)
    height, width = height + shift_r, width + shift_c
    if height > 30 or width > 30:
        raise AssertionError("internal layout exceeded ARC size limit")
    grid = [[bg] * width for _ in range(height)]

    def put(r, c, color):
        grid[r + shift_r][c + shift_c] = color

    for r in range(fh):
        for c in range(fw):
            if r in (0, fh - 1) or c in (0, fw - 1):
                put(fr + r, fc + c, frame_color)
    order = list(sources)
    rng.shuffle(order)
    for color, (r, c) in zip(order, arrow_slots):
        for dr in range(3):
            for dc in range(4):
                put(r + dr, c + dc, color if (dr, dc) in ARROW_SOURCE_CELLS else mapping[color])
    masks, used = {}, set()
    for i, color in enumerate(sources):
        for attempt in range(64):
            if i == 0:
                # Full bbox, one detached piece: test the grouping rule directly.
                mask = {(r, 0) for r in range(n)} | {(0, n - 1)}
            else:
                mask = {(r, c) for r in range(n) for c in range(n) if rng.random() < 0.55}
                mask |= {(0, rng.randrange(n)), (n - 1, rng.randrange(n)),
                         (rng.randrange(n), 0), (rng.randrange(n), n - 1)}
            key = tuple(sorted(mask))
            if len(mask) < n * n and key not in used:
                used.add(key)
                masks[color] = mask
                break
        else:
            raise ValueError("template sampling budget exhausted")
    order = list(sources)
    rng.shuffle(order)
    for color, (r, c) in zip(order, template_slots):
        for dr, dc in masks[color]:
            put(r + dr, c + dc, color)
    slots = [(r, c) for r in range(3) for c in range(3)]
    rng.shuffle(slots)
    labels = list(sources) + [rng.choice(sources) for _ in range(rng.randint(k + 1, 8) - k)]
    rng.shuffle(labels)
    for (sr, sc), color in zip(slots, labels):
        for dr in range(n):
            for dc in range(n):
                put(fr + 2 + sr * (n + 1) + dr, fc + 2 + sc * (n + 1) + dc, color)
    parse_grid(grid)
    return grid


PARAMETER="mapping_policy"
VALUES=POLICIES

def program(settings):
 if type(settings) is not dict or set(settings)!={PARAMETER} or settings[PARAMETER] not in POLICIES:raise ValueError('mapping_policy must be once or terminal')
 return (HERE/'canonical.rkt').read_text() if settings[PARAMETER]=='once' else (HERE/'terminal.rkt').read_text()

def draw(seed,index,branched=False,stress=False):
 g=sample_input(seed,index)
 if branched:
  p=parse_grid(g);mapping=p['mapping'];node=next(iter(set(mapping)-set(mapping.values())));order=[]
  while node in mapping:order.append(node);node=mapping[node]
  source=order[1]
  extra=next(c for c in range(10) if c not in {v for row in g for v in row})
  r,c,_,_=next(a for a in p['arrows'] if a[2]==source)
  for dr in range(3):
   for dc in range(4):
    if (dr,dc) not in ARROW_SOURCE_CELLS:g[r+dr][c+dc]=extra
 if stress:
  p=parse_grid(g);bg=p['background'];h,w=len(g),len(g[0]);out=[[bg]*30 for _ in range(30)]
  rr=30-h;cc=30-w
  for r,row in enumerate(g):out[r+rr][cc:cc+w]=row
  g=out
 parse_grid(g)
 return g

def generate(seed,settings,demos=2,queries=4):
 code=program(settings);integer(seed,0,2**63-1,'seed');integer(demos,2,6,'demos');integer(queries,1,4,'queries')
 def pair(index,branched=False,stress=False):
  g=draw(seed,index,branched,stress);return {'input':g,'output':predict(g,settings[PARAMETER])}
 trains=[pair(i,i%2==1) for i in range(demos)]
 order=[(6,False,False),(7,True,False),(8,False,False),(11,True,True)]
 random.Random(f'public-edb-query-order:{seed}').shuffle(order)
 tests=[pair(*spec) for spec in order[:queries]]
 return {'train':trains,'test':tests,'program_solution':code}

def wrong_order_program():
 # Recoloring the selector before template lookup may choose the destination's
 # shape, instead of preserving the original source template.
 return (HERE/'wrong_order.rkt').read_text()

def findings(e,policy):
 return [r for r in RIVALS if r!=policy and all(predict(p['input'],r)==p['output'] for p in e['train']) and any(predict(p['input'],r)!=p['output'] for p in e['test'])]

def public_turn(e,index):
 integer(index,0,len(e['test'])-1,'query_index')
 return copy.deepcopy({'train':e['train'],'test':[{'input':e['test'][index]['input']}]})
