"""Measure audit shortcuts on generated grids (Python only; Racket parity is in */counterexamples.json).

Usage from the packet root: python3 checks/audit/distribution_probe.py OUT.json
"""
import collections, hashlib, importlib.util, json, sys
from pathlib import Path

sys.path.insert(0, "repo/shared/runtime")


def load(task):
    path = Path(f"repo/generators/{task}/generator.py")
    spec = importlib.util.spec_from_file_location("g" + task, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def body_components(grid):
    body = grid[1:]
    h, w = len(body), len(body[0])
    seen, found = set(), []
    for r in range(h):
        for c in range(w):
            if body[r][c] and (r, c) not in seen:
                color, stack, cells = body[r][c], [(r, c)], []
                seen.add((r, c))
                while stack:
                    y, x = stack.pop()
                    cells.append((y + 1, x))
                    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen and body[ny][nx] == color:
                            seen.add((ny, nx))
                            stack.append((ny, nx))
                found.append(cells)
    return found


def modal_only(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        counts = collections.Counter(v for v in row if v)
        repeated = [c for c, n in counts.items() if n >= 2]
        if repeated:
            top = max(repeated, key=lambda c: (counts[c], -row.index(c)))
            out[r] = [0 if v == top else v for v in row]
    return out


report = {}
e42, e42_sha = load("e42dbdaedbe0")
rows = {}
for band in ("easy", "medium", "hard"):
    ties = absolute_fits = 0
    size_sets = collections.Counter()
    for s in range(500):
        grid = e42.generate(s, s, difficulty=band)
        sizes = sorted(len(c) for c in body_components(grid))
        size_sets[str(sizes)] += 1
        ties += len(set(sizes)) < len(sizes)
        absolute_fits += sizes == list(range(1, len(sizes) + 1))
    rows[band] = {"draws": 500, "size_ties": ties, "absolute_size_index_rival_equals_rank_rule": absolute_fits,
                  "top_size_sets": size_sets.most_common(4)}
report["e42dbdaedbe0"] = {"generator_sha256": e42_sha, "seeds": "s=0..499, sample_index=s", "bands": rows}

d4, d4_sha = load("4d8f78cee8b3")
equal = multi = n = 0
for band in (None, "easy", "medium", "hard"):
    for s in range(800):
        grid = d4.generate(s, s, difficulty=band)
        n += 1
        equal += modal_only(grid) == d4.rule_mirror(grid)
        multi += any(sum(1 for k in collections.Counter(v for v in row if v).values() if k >= 2) >= 2 for row in grid)
report["4d8f78cee8b3"] = {"generator_sha256": d4_sha, "seeds": "s=0..799, sample_index=s, bands None/easy/medium/hard",
                          "draws": n, "erase_only_most_frequent_color_equals_rule": equal,
                          "grids_with_a_row_holding_two_repeated_colors": multi}
Path(sys.argv[1]).write_text(json.dumps(report, indent=1))
print(json.dumps(report))
