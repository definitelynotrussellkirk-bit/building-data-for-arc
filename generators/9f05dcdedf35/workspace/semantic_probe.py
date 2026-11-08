"""Independent authoring probe; never a training-label source or blind-solve tool."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

TASK_ID = "9f05dcdedf35"
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def objects(grid):
    """Monochrome four-connected foreground components, independently derived."""
    seen, result = set(), []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            stack, cells = [(r, c)], set()
            seen.add((r, c))
            while stack:
                p = stack.pop()
                cells.add(p)
                for dr, dc in CARDINAL:
                    q = p[0] + dr, p[1] + dc
                    if (0 <= q[0] < h and 0 <= q[1] < w and q not in seen
                            and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        stack.append(q)
            result.append((color, cells))
    return result


def graph(grid, diagonal=False):
    objs = objects(grid)
    deltas = CARDINAL + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if diagonal else ())
    edges = [set() for _ in objs]
    for i, (_, cells) in enumerate(objs):
        for j in range(i + 1, len(objs)):
            other = objs[j][1]
            if any((r + dr, c + dc) in other for r, c in cells for dr, dc in deltas):
                edges[i].add(j)
                edges[j].add(i)
    return objs, edges


def repaint(grid, ids, objs=None):
    out = [list(row) for row in grid]
    objs = objects(grid) if objs is None else objs
    for i in ids:
        for r, c in objs[i][1]:
            out[r][c] = 8
    return out


def intended(grid):
    objs, edges = graph(grid)
    return repaint(grid, [i for i, neighbors in enumerate(edges) if len(neighbors) == 1], objs)


def predict(grid, name):
    objs, edges = graph(grid)
    degrees = list(map(len, edges))
    if name == "identity":
        return [list(row) for row in grid]
    if name == "delete_input8":
        out = intended(grid)
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 8:
                    out[r][c] = 0
        return out
    if name == "pixel_degree":
        out = [list(row) for row in grid]
        h, w = len(grid), len(grid[0])
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                degree = sum(0 <= r + dr < h and 0 <= c + dc < w
                             and grid[r + dr][c + dc] != 0 for dr, dc in CARDINAL)
                if value and degree == 1:
                    out[r][c] = 8
        return out
    if name == "contact_edges":
        owner = {p: i for i, (_, cells) in enumerate(objs) for p in cells}
        counts = [sum(owner.get((r + dr, c + dc), i) != i
                      for r, c in cells for dr, dc in CARDINAL)
                  for i, (_, cells) in enumerate(objs)]
        ids = [i for i, count in enumerate(counts) if count == 1]
    elif name == "nonmax_degree":
        ids = [i for i, degree in enumerate(degrees) if 0 < degree < max(degrees, default=0)]
    elif name == "degree_le_one":
        ids = [i for i, degree in enumerate(degrees) if degree <= 1]
    elif name == "all_touching":
        ids = [i for i, degree in enumerate(degrees) if degree > 0]
    elif name == "leaf_colors_globally":
        colors = {objs[i][0] for i, degree in enumerate(degrees) if degree == 1}
        ids = [i for i, (color, _) in enumerate(objs) if color in colors]
    elif name == "diagonal_contacts":
        objs, diagonal_edges = graph(grid, diagonal=True)
        ids = [i for i, neighbors in enumerate(diagonal_edges) if len(neighbors) == 1]
    elif name == "neighbor_colors":
        ids = [i for i, neighbors in enumerate(edges)
               if len({objs[j][0] for j in neighbors}) == 1]
    else:
        raise ValueError(name)
    return repaint(grid, ids, objs)


RIVAL_NAMES = ("pixel_degree", "contact_edges", "nonmax_degree", "degree_le_one",
               "all_touching", "leaf_colors_globally", "delete_input8", "identity",
               "diagonal_contacts", "neighbor_colors")


def observe(grid):
    objs, edges = graph(grid)
    main = [i for i, neighbors in enumerate(edges) if neighbors]
    degrees = list(map(len, edges))
    shape = "branch" if max(degrees) == 3 else "chain"
    boxes = []
    centers = {}
    for i in main:
        rs, cs = zip(*objs[i][1])
        box = min(rs), min(cs), max(rs), max(cs)
        boxes.append(box)
        centers[i] = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    if shape == "branch":
        center = degrees.index(3)
        stem = next(i for i in edges[center] if degrees[i] == 2)
        dr, dc = centers[stem][0] - centers[center][0], centers[stem][1] - centers[center][1]
    else:
        dr = max(b[2] for b in boxes) - min(b[0] for b in boxes)
        dc = max(b[3] for b in boxes) - min(b[1] for b in boxes)
    return dict(height=len(grid), width=len(grid[0]),
                palette_size=len({color for color, _ in objs}), graph_shape=shape,
                chain_orientation="horizontal" if abs(dc) > abs(dr) else "vertical",
                component_span=max(max(b[2] - b[0] + 1, b[3] - b[1] + 1) for b in boxes))


def load_generator(root, explicit=None):
    candidates = [root / "generators" / TASK_ID / "generator.py",
                  root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"]
    path = explicit if explicit is not None else next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("leaf_generator_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def main():
    from reviewer_support import canonical_pairs, find_root
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--joint", action="store_true")
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--generator-source", type=Path, help="Pinned baseline source for before evidence")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output must be new")
    root = find_root(__file__)
    gen, source = load_generator(root,args.generator_source)
    report = dict(task_id=TASK_ID, generator_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  scope="Independent authoring evidence; Python labels are not training labels.",
                  draws=0, failures=[], racket_cases=[])
    cases = []
    for pair in canonical_pairs(TASK_ID, root=root):
        errors = gen.self_check(pair["input"])
        if errors or intended(pair["input"]) != pair["output"]:
            report["failures"].append(dict(kind="canonical", pair=pair, errors=errors))
        cases.append(dict(input=pair["input"], expected=pair["output"], source="canonical"))
    for band in ("easy", "medium", "hard"):
        for index in range(16):
            grid = gen.generate(37 + index, index, difficulty=band)
            label = intended(grid)
            report["draws"] += 1
            errors = gen.self_check(grid)
            if errors:
                report["failures"].append(dict(kind="default", band=band, index=index, errors=errors))
            if index % 4 < 2:
                survivors = [name for name in RIVAL_NAMES if predict(grid, name) == label]
                if survivors:
                    report["failures"].append(dict(kind="teaching", band=band,index=index,
                                                   survivors=survivors,input=grid))
            cases.append(dict(input=grid, expected=label, source="generated",band=band,
                              seed=37+index,sample_index=index))
    if args.joint:
        names = ("height", "width", "palette_size", "chain_orientation", "graph_shape", "component_span")
        combinations = itertools.product(range(8,15), range(8,17), (5,6),
                                         ("horizontal","vertical"),("chain","branch"),(1,2))
        for number, values in enumerate(combinations):
            controls = dict(zip(names,values))
            for band in (None,"easy","medium","hard"):
                for index in (0,2):
                    grid = gen.generate(number,index,difficulty=band,**controls)
                    report["draws"] += 1
                    errors = gen.self_check(grid)
                    actual = observe(grid)
                    if errors or actual != controls:
                        report["failures"].append(dict(kind="joint",seed=number,index=index,
                                                       band=band,controls=controls,actual=actual,errors=errors))
        report["joint_combinations"] = number+1
    if args.racket:
        from arcpuzzles.catalog import Catalog
        catalog = Catalog(root=root)
        receipt = catalog.apply(TASK_ID,[case["input"] for case in cases])
        report["racket_receipt"] = receipt
        for case,result in zip(cases,receipt["results"],strict=True):
            actual = result["output"]
            report["racket_cases"].append(dict(**case,actual=actual,equal=actual==case["expected"]))
            if actual != case["expected"]:
                report["failures"].append(dict(kind="racket",case=case,actual=actual))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(dict(draws=report["draws"],racket_cases=len(report["racket_cases"]),
                          failures=len(report["failures"]),out=str(args.out))))
    return bool(report["failures"])


if __name__ == "__main__":
    raise SystemExit(main())
