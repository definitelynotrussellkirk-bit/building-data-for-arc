from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, path


def canonical_row(task_id: str):
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def rule_hash(row) -> str:
    normalized = " ".join(row["program_solution"].split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def all_pairs(row):
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def complete_once(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    hits = []
    for r in range(h - 1):
        for c in range(w - 1):
            cells = [(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)]
            vals = [grid[rr][cc] for rr, cc in cells]
            if vals.count(3) == 3 and vals.count(0) == 1:
                hits.append(cells[vals.index(0)])
    for r, c in hits:
        out[r][c] = 3
    return out


def complete_fixpoint(grid):
    out = [list(row) for row in grid]
    while True:
        nxt = complete_once(out)
        if nxt == out:
            return out
        out = nxt


def count_initial_hits(grid):
    h, w = len(grid), len(grid[0])
    count = 0
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [grid[r][c], grid[r + 1][c], grid[r][c + 1], grid[r + 1][c + 1]]
            count += vals.count(3) == 3 and vals.count(0) == 1
    return count


def components(grid, color=None, exclude=frozenset()):
    h, w = len(grid), len(grid[0])
    seen = set(exclude)
    found = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0 or (color is not None and grid[r][c] != color):
                continue
            target = grid[r][c]
            q = deque([(r, c)]); seen.add((r, c)); cells = []
            while q:
                rr, cc = q.popleft(); cells.append((rr, cc))
                for nr, nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen and grid[nr][nc] == target:
                        seen.add((nr,nc)); q.append((nr,nc))
            found.append((target, cells))
    return found


def crop_component(grid, cells, color):
    r0=min(r for r,c in cells); r1=max(r for r,c in cells)
    c0=min(c for r,c in cells); c1=max(c for r,c in cells)
    out=[[0]*(c1-c0+1) for _ in range(r1-r0+1)]
    for r,c in cells: out[r-r0][c-c0]=color
    return out


def audit_5b():
    task="5b40e03f0a23"; gen,path=load(task); row=canonical_row(task)
    cascade = [
        [3,3,0,0,0],
        [3,0,3,0,0],
        [0,3,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
    ]
    sample_stats=Counter(); mismatch_examples=[]
    for band in ("easy","medium","hard"):
        for i in range(200):
            grid=gen.generate(7000+i, i, difficulty=band)
            sample_stats["generated"] += 1
            sample_stats["self_check_failures"] += bool(gen.self_check(grid))
            sample_stats["fixpoint_vs_single_pass_disagreements"] += complete_fixpoint(grid) != complete_once(grid)
    for i in range(100):
        try:
            grid=gen.generate(9000+i, i, grid_h=7, grid_w=7, n_windows=5)
            hits=count_initial_hits(grid)
            sample_stats["n_windows_override_cases"] += 1
            if hits != 5:
                sample_stats["n_windows_override_mismatches"] += 1
                if len(mismatch_examples)<5:
                    mismatch_examples.append({"seed":9000+i,"sample_index":i,"observed_initial_windows":hits})
        except Exception as exc:
            sample_stats["n_windows_override_exceptions"] += 1
            if len(mismatch_examples)<5:
                mismatch_examples.append({"seed":9000+i,"sample_index":i,"exception":f"{type(exc).__name__}: {exc}"})
    identical_palette=0; identical_texture=0
    for i in range(20):
        base=gen.generate(11000+i,i)
        identical_palette += base == gen.generate(11000+i,i,palette_kind="warm")
        identical_texture += base == gen.generate(11000+i,i,texture="warm")
    pairs=all_pairs(row)
    report={
        "task_id":task,
        "generator_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "rule_hash":rule_hash(row),
        "generator_version":gen.VERSION,
        "sample_policy":"200 seeds per easy/medium/hard; seed=7000+i, sample_index=i",
        "sample_stats":dict(sample_stats),
        "override_examples_first_5":mismatch_examples,
        "ignored_axis_checks":{"palette_kind_warm_identical":identical_palette,"texture_warm_identical":identical_texture,"denominator":20},
        "canonical_pair_count":len(pairs),
        "single_pass_fits_canonical_pairs":sum(complete_once(p["input"])==p["output"] for p in pairs),
        "fixpoint_fits_canonical_pairs":sum(complete_fixpoint(p["input"])==p["output"] for p in pairs),
        "counterexample":{
            "input":cascade,
            "self_check":gen.self_check(cascade),
            "documented_invariant_violated":"active windows are not separated; completion cascades",
            "single_pass_rival_output":complete_once(cascade),
            "python_fixpoint_output":complete_fixpoint(cascade),
        },
    }
    out=PACKET/"checks/audit"/task
    (out/"input.json").write_text(json.dumps(cascade,indent=2)+"\n")
    (out/"probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")


def audit_5d():
    task="5d15679fbc44"; gen,path=load(task); row=canonical_row(task)
    no_target=[[0]*10 for _ in range(9)]
    no_target[0][0]=4; no_target[3][3]=6; no_target[4][3]=6
    stats=Counter(); examples=[]
    for band in ("easy","medium","hard"):
        for i in range(200):
            grid=gen.generate(13000+i,i,difficulty=band)
            stats["generated"] += 1
            stats["self_check_failures"] += bool(gen.self_check(grid))
            colors={v for row_ in grid for v in row_ if v}
            stats[f"palette_size_{len(colors)}"] += 1
            if len(colors) != 3: stats["palette_size_not_declared_exact_3"] += 1
            key=grid[0][0]
            comps=[cells for color,cells in components(grid,color=key) if (0,0) not in cells]
            if not comps:
                stats["no_key_target"] += 1
                continue
            sizes=sorted((len(c) for c in comps),reverse=True)
            stats[f"largest_key_blob_size_{sizes[0]}"] += 1
            if sizes[0] > 6: stats["largest_key_blob_above_declared_valid_6"] += 1
            if sizes[0] not in (4,5): stats["largest_key_blob_outside_summary_4_5"] += 1
            if len(sizes)>1 and sizes[0]==sizes[1]: stats["largest_key_blob_ties"] += 1
            if len(examples)<5 and (len(colors)!=3 or sizes[0]>6):
                examples.append({"band":band,"seed":13000+i,"sample_index":i,"palette_size":len(colors),"key_blob_sizes":sizes})
    ignored=Counter()
    for i in range(20):
        base=gen.generate(15000+i,i)
        ignored["blob_size_3_identical"] += base == gen.generate(15000+i,i,blob_size=3)
        ignored["blob_size_6_identical"] += base == gen.generate(15000+i,i,blob_size=6)
        ignored["palette_size_3_identical"] += base == gen.generate(15000+i,i,palette_size=3)
        ignored["n_distinct_colors_3_identical"] += base == gen.generate(15000+i,i,n_distinct_colors=3)
    noncorner=components(no_target,exclude={(0,0)})
    largest=max(noncorner,key=lambda item:len(item[1]))
    rival=crop_component(no_target,largest[1],largest[0])
    report={
        "task_id":task,
        "generator_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "rule_hash":rule_hash(row),
        "generator_version":gen.VERSION,
        "sample_policy":"200 seeds per easy/medium/hard; seed=13000+i, sample_index=i",
        "sample_stats":dict(stats),
        "distribution_examples_first_5":examples,
        "ignored_axis_checks":{**dict(ignored),"denominator":20},
        "counterexample":{
            "input":no_target,
            "self_check":gen.self_check(no_target),
            "documented_invariant_violated":"no key-color blob exists away from the key cell",
            "largest_nonkey_blob_rival_output":rival,
            "expected_rule_fallback_from_source":[[0]],
        },
    }
    out=PACKET/"checks/audit"/task
    (out/"input.json").write_text(json.dumps(no_target,indent=2)+"\n")
    (out/"probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")


audit_5b(); audit_5d()
print("wrote audit probes")
