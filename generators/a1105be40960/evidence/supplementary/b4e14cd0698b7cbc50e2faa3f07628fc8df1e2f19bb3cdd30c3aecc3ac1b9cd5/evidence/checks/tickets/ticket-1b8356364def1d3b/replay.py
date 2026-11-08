#!/usr/bin/env python3
"""Bounded replay of the pinned a1105be40960 bbox-area shortcut witness."""
from __future__ import annotations
from collections import deque
import copy
import hashlib
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import load_selected_generator, normalize_grid

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "a1105be40960"
TICKET = "ticket-1b8356364def1d3b"
RETURN_ID = "review-ef399102e8a4504c:v0001"
SOURCE_SHA = "a28d9ce3d0524cdce7ff44eb7c21a82e4e8a0c9aa6435d0a4a81316f61f3979b"
ASSETS_SHA = "14f57abbbffcb96035da19cc9745a7c339dd751de956799fa40a98d92b2161d2"
INDEX_SHA = "304df9ddbfba24fa239244fa536ff3dce415781b00a9f27a17746c00a7874585"
RECORD_SHA = "8ce76443f41b2a133208bbfbd6450a418d3971d7f73742009843ae4d005a596c"
RULE_HASH = "b3ce44730a7b"
BASE = REPO / "generators" / TASK / "counterexamples/review-ef399102e8a4504c-v0001"
ASSETS = BASE / "audit_assets.json"
INDEX = REPO / "generators" / TASK / "evidence/review_index.json"
SOURCE = REPO / "generators" / TASK / "generator.py"
RETAINED = BASE / "retained/checks/audit/a1105be40960"
OUT = HERE / "result.json"

def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())

def sha_json(value) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())

def canonical_program() -> str:
    rows = []
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    assert len(rows) == 1
    source = rows[0]["program_solution"]
    assert sha_bytes(" ".join(source.split()).encode())[:12] == RULE_HASH
    return source

def components(grid, color=4):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        comp = {start}
        while queue:
            r, c = queue.popleft()
            for nxt in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if nxt in remaining:
                    remaining.remove(nxt); comp.add(nxt); queue.append(nxt)
        result.append(comp)
    return result

def metrics(comp):
    rows=[r for r,_ in comp]; cols=[c for _,c in comp]
    return {"cells":len(comp), "bbox_area":(max(rows)-min(rows)+1)*(max(cols)-min(cols)+1),
            "top":min(rows), "left":min(cols)}

def pixel_count_rival(grid):
    out=copy.deepcopy(grid)
    comps=components(grid)
    k=sum(value==1 for row in grid for value in row)
    ranked=sorted(comps, key=lambda comp:(-len(comp), metrics(comp)["top"], metrics(comp)["left"]))
    if 1 <= k <= len(ranked):
        for r,c in ranked[k-1]: out[r][c]=3
    return out

def main() -> int:
    started=time.monotonic()
    if OUT.exists(): raise FileExistsError(OUT)
    assert sha_file(SOURCE)==SOURCE_SHA
    assert sha_file(ASSETS)==ASSETS_SHA
    assert sha_file(INDEX)==INDEX_SHA
    manifest=json.loads(ASSETS.read_text(encoding="utf-8"))
    assert manifest["return_id"]==RETURN_ID
    assert manifest["audited_generator_sha256"]==SOURCE_SHA
    verified=[]
    for row in manifest["files"]:
        path=REPO/row["path"]
        assert path.stat().st_size==row["bytes"]
        assert sha_file(path)==row["sha256"]
        verified.append({"path":row["path"],"sha256":row["sha256"],"bytes":row["bytes"]})

    index=json.loads(INDEX.read_text(encoding="utf-8"))
    records=[row for row in index["audits"] if row["return_id"]==RETURN_ID]
    assert len(records)==1
    record=records[0]
    assert sha_json(record)==RECORD_SHA
    assert record["source_sha256"]==SOURCE_SHA
    assert record["resolution"]=="needs_triage"

    grid=json.loads((RETAINED/"input.json").read_text(encoding="utf-8"))
    retained=json.loads((RETAINED/"shortcut_probe.json").read_text(encoding="utf-8"))
    assert retained["generator_sha256"]==SOURCE_SHA
    assert retained["executed_rule_hash"]==RULE_HASH
    witness=retained["counterexample"]
    assert grid==witness["input"]

    generator, generator_path, generator_sha = load_selected_generator(TASK, root=REPO)
    assert generator_path==SOURCE and generator_sha==SOURCE_SHA
    assert generator.self_check(grid)==witness["self_check"]==[]

    comps=components(grid)
    observed=sorted((metrics(comp) for comp in comps), key=lambda row:-row["bbox_area"])
    assert [(row["bbox_area"],row["cells"]) for row in observed]==[(16,7),(9,9)]
    assert sum(value==1 for row in grid for value in row)==1

    program=canonical_program()
    function=f"(lambda (g) {strip_rule_wrapper(program)})"
    datum="("+" ".join("("+" ".join(map(str,row))+")" for row in grid)+")"
    with RacketBridge(timeout=30,max_calls_before_restart=8) as bridge:
        runtime=bridge.runtime_identity
        official=normalize_grid(bridge.eval_text(f"({function} '{datum})"))
    rival=pixel_count_rival(grid)
    assert official==witness["official_racket_output"]
    assert rival==witness["pixel_count_rival_output"]
    assert official!=rival and witness["outputs_differ"] is True

    result={
      "schema":"arcpuzzles-audit-replay-ticket-v1",
      "ticket_id":TICKET,
      "task_id":TASK,
      "status":"reproduced",
      "audit_return_id":RETURN_ID,
      "audit_record_sha256":RECORD_SHA,
      "audit_not_cleared":True,
      "source_binding":{"generator_sha256":SOURCE_SHA,"assets_manifest_sha256":ASSETS_SHA,
                        "audit_index_sha256":INDEX_SHA,"rule_hash":RULE_HASH},
      "asset_files_verified":verified,
      "witness":{"self_check":[],"selector_k":1,"components_by_bbox_area":observed,
                 "input_sha256":sha_json(grid),"official_output_sha256":sha_json(official),
                 "pixel_count_rival_output_sha256":sha_json(rival),"outputs_differ":True},
      "racket_runtime":runtime,
      "summary":"The exact retained validator-accepted witness reproduces: bbox-area ranking selects the sparse 4x4-bbox L (area 16, 7 cells), while pixel-count ranking selects the solid 3x3 (area 9, 9 cells). The existing training-shortcut audit remains open.",
      "limitations":["One retained witness only; the prior 60-draw census was not rerun.",
                     "This reproduction does not clear, widen, or independently reclassify the existing audit."],
      "elapsed_seconds":round(time.monotonic()-started,6),
    }
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"reproduced","outputs_differ":True,"out":str(OUT),
                      "elapsed_seconds":result["elapsed_seconds"]},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
