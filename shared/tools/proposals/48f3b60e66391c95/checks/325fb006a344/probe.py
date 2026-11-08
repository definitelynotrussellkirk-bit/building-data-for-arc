#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from collections import Counter
from pathlib import Path

TASK = "325fb006a344"


def load_generator(repo: Path):
    path = repo / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def components(grid):
    h, w = len(grid), len(grid[0])
    seen, out = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
                continue
            stack, comp = [(r, c)], set()
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < h and 0 <= cc < w) or (rr, cc) in seen or grid[rr][cc] != 3:
                    continue
                seen.add((rr, cc)); comp.add((rr, cc))
                stack += [(rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)]
            out.append(comp)
    return out


def normalize(cells):
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return {(r-r0, c-c0) for r, c in cells}


def consensus(grid, threshold):
    norms = [normalize(c) for c in components(grid)]
    counts = Counter(p for s in norms for p in s)
    keep = {p for p, n in counts.items() if n >= threshold(len(norms))}
    if not keep:
        return [[0]], norms
    r0=min(r for r,c in keep); r1=max(r for r,c in keep); c0=min(c for r,c in keep); c1=max(c for r,c in keep)
    out=[[0]*(c1-c0+1) for _ in range(r1-r0+1)]
    for r,c in keep: out[r-r0][c-c0]=3
    return out, norms


def read_racket(path):
    if path is None: return None
    data=json.loads(Path(path).read_text())
    return data["results"][0]["output"]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--racket-anchor", type=Path)
    ap.add_argument("--racket-threshold", type=Path)
    args=ap.parse_args()
    gen, source=load_generator(args.repo)
    anchor=gen.generate(478,7)
    threshold_case=gen.generate(32009,9,difficulty="medium")
    canonical_anchor, anchor_norms=consensus(anchor, lambda n: 2)
    intersection_anchor,_=consensus(anchor, lambda n: n)
    canonical_threshold, threshold_norms=consensus(threshold_case, lambda n: 2)
    majority_threshold,_=consensus(threshold_case, lambda n: n//2+1)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/"anchor-input.json").write_text(json.dumps(anchor,indent=2)+"\n")
    (args.out/"threshold-input.json").write_text(json.dumps(threshold_case,indent=2)+"\n")
    anchor_intersection=set.intersection(*anchor_norms) if anchor_norms else set()
    report={
      "schema":"arcpuzzles-peer-adversarial-probe-v1","task_id":TASK,
      "generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
      "anchor_defect":{
        "seed":478,"sample_index":7,"self_check":gen.self_check(anchor),
        "component_count":len(anchor_norms),"normalized_intersection":sorted(map(list,anchor_intersection)),
        "canonical_python_output":canonical_anchor,"all_copies_intersection_output":intersection_anchor,
        "finding":"The advertised shared base is lost after per-copy normalization; this ordinary draw has empty normalized intersection and canonical output [[0]]."
      },
      "threshold_teaching":{
        "seed":32009,"sample_index":9,"difficulty":"medium","self_check":gen.self_check(threshold_case),
        "component_count":len(threshold_norms),"canonical_python_output":canonical_threshold,
        "strict_majority_output":majority_threshold,
        "different_cells":sum(a!=b for ra,rb in zip(canonical_threshold,majority_threshold) for a,b in zip(ra,rb)),
        "finding":"The canonical >=2 rule differs from strict majority on this four-copy query, while the source canonical demonstrations use three copies where the rules coincide."
      },
      "recommended_repair":[
        "Normalize the shared base before adding extras and prevent extras above/left from shifting its normalized anchor.",
        "Add a lesson-scheduled four-copy demonstration with a cell shared by exactly two copies, so >=2 is distinguishable from strict majority/intersection."
      ],
      "racket":{}
    }
    ra=read_racket(args.racket_anchor); rt=read_racket(args.racket_threshold)
    if ra is not None:
        report["racket"]["anchor_matches_python"] = ra == canonical_anchor
        report["racket"]["anchor_output"] = ra
    if rt is not None:
        report["racket"]["threshold_matches_python"] = rt == canonical_threshold
        report["racket"]["threshold_output"] = rt
    assert report["anchor_defect"]["self_check"] == []
    assert report["anchor_defect"]["normalized_intersection"] == []
    assert canonical_anchor == [[0]]
    assert canonical_threshold != majority_threshold
    if args.racket_anchor or args.racket_threshold:
        assert report["racket"] == {"anchor_matches_python": True, "anchor_output": canonical_anchor,
                                    "threshold_matches_python": True, "threshold_output": canonical_threshold}
    (args.out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"task_id":TASK,"status":"finding_reproduced","racket":report["racket"],
                      "anchor_components":len(anchor_norms),"threshold_components":len(threshold_norms)},sort_keys=True))

if __name__ == "__main__": main()
