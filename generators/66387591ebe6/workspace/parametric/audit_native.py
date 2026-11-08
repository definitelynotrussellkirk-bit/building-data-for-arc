"""Bounded protected-Racket teaching and public-projection audit.

Run through the packet launcher; --out must name a fresh private evidence folder.
Only hash-named files in its public/ subfolder are public payloads. Their private
index distinguishes the complete controller challenge from its first-turn view.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "66387591ebe6"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import public_challenge_bytes, public_challenge_id


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _sources():
    files = [ROOT / "generators" / TASK / "generator.py"]
    files += sorted(p for p in HERE.iterdir() if p.suffix in {".py", ".rkt", ".json"})
    return {str(p.relative_to(ROOT)): _sha(p.read_bytes()) for p in files}


def _load_native():
    path = HERE / "native.py"
    name = "_audit_native_" + _sha(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _pivot(grid):
    pivots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(pivots) != 1:
        raise ValueError("Lookup reduction requires exactly one pivot")
    return pivots[0]


def _rotation(grid, turns):
    """Independent geometric reduction, not a source of episode labels."""
    pr, pc = _pivot(grid)
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    out[0][0], out[pr][pc] = grid[0][0], 9
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v in (0, 9) or (r, c) == (0, 0):
                continue
            dr, dc = r - pr, c - pc
            for _ in range(turns):
                dr, dc = dc, -dr
            rr, cc = pr + dr, pc + dc
            if not (0 <= rr < h and 0 <= cc < w) or (rr, cc) in {(0, 0), (pr, pc)}:
                raise ValueError("Input is not safe under all four pivot rotations")
            out[rr][cc] = v
    return out


def _cue(grid, kind):
    if kind == "key":
        return grid[0][0]
    if kind == "height":
        return len(grid)
    r, c = _pivot(grid)
    dr, dc = ((-1, 0), (0, 1), (1, 0), (0, -1))[grid[0][0] - 1]
    r, c = r + dr, c + dc
    while 0 <= r < len(grid) and 0 <= c < len(grid[0]):
        if grid[r][c] not in (0, 9) and (r, c) != (0, 0):
            return grid[r][c]
        r, c = r + dr, c + dc
    return 0  # The separate no-hit cue; foreground is never color zero.


def _lookup_program(canonical, kind, mapping):
    """Materialize one demo-fitted mapping for independent Racket replay."""
    old = "(rotated (rotate-about cells pivot (- key 1)))"
    if canonical.count(old) != 1:
        raise ValueError("Canonical rotation expression changed; review the lookup emitter")
    if kind == "key":
        cue = "key"
    elif kind == "height":
        cue = "(rows g)"
    else:
        cue = """(let* ((d (list-ref (list (list -1 0) (list 0 1)
                                            (list 1 0) (list 0 -1)) (- key 1))))
          (let walk ((r (+ (first pivot) (first d)))
                     (c (+ (second pivot) (second d))))
            (cond ((not (in-bounds? r c (rows g) (cols g))) 0)
                  ((and (not (equal? (list r c) (list 0 0)))
                        (not (= (at g r c) 0)) (not (= (at g r c) 9))) (at g r c))
                  (else (walk (+ r (first d)) (+ c (second d)))))))"""
    arms = " ".join(f"((= cue {k}) {v})" for k, v in sorted(mapping.items()))
    turns = f"(let ((cue {cue})) (cond {arms} (else 0)))"
    return canonical.replace(old, f"(rotated (rotate-about cells pivot {turns}))")


def _lookup_audit(kind, episode, canonical, execute):
    # Intersect turn sets, retaining symmetry rather than arbitrarily assigning a
    # turn to a symmetric grid. Query outputs are not used to fit the mapping.
    domains, rows = {}, []
    conflict = None
    for i, pair in enumerate(episode["train"]):
        cue = _cue(pair["input"], kind)
        turns = {t for t in range(4) if _rotation(pair["input"], t) == pair["output"]}
        if not turns:
            raise ValueError("Executed label is not any legal rigid rotation")
        domains[cue] = domains.get(cue, set(range(4))) & turns
        rows.append({"demo_index": i, "cue": cue, "matching_turns": sorted(turns)})
        if not domains[cue] and conflict is None:
            conflict = i
    result = {"family": f"{kind}_to_turn_lookup", "demo_reduction": rows,
              "survives_demos": conflict is None, "eliminating_demo": conflict,
              "method": "Intersect independent geometric turn sets of protected-Racket labels; replay every surviving witness in Racket.",
              "surviving_query_disagreements": []}
    if conflict is not None:
        return result
    mapping = {cue: min(turns) for cue, turns in domains.items()}
    # Freeze all allowed mappings before consulting any query label.
    frozen_domains = {cue: sorted(turns) for cue, turns in domains.items()}
    result["demo_fitted_turn_domains"] = frozen_domains
    program = _lookup_program(canonical, kind, mapping)
    if any(execute(program, p["input"]) != p["output"] for p in episode["train"]):
        raise ValueError("Synthesized lookup does not replay its demonstrated fit")
    for i, pair in enumerate(episode["test"]):
        cue = _cue(pair["input"], kind)
        for turn in frozen_domains.get(cue, list(range(4))):
            if _rotation(pair["input"], turn) == pair["output"]:
                continue
            candidate = {**mapping, cue: turn}
            rival = _lookup_program(canonical, kind, candidate)
            if any(execute(rival, p["input"]) != p["output"] for p in episode["train"]):
                raise ValueError("A query-directed completion violated demonstration fit")
            output = execute(rival, pair["input"])
            if output == pair["output"]:
                raise ValueError("Geometric lookup gap did not reproduce in Racket")
            result["surviving_query_disagreements"].append({
                "query_index": i, "cue": cue, "mapping": candidate,
                "program": rival, "program_sha256": _sha(rival.encode()),
                "output": output, "reference_output": pair["output"]})
            break
    return result


def audit(seed, demos, out):
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"Choose a fresh evidence folder: {out}")
    native = _load_native()
    before = _sources()
    report = {"schema": "66387591ebe6-native-self-audit-v1", "seed": seed,
              "demos": demos, "queries": 4, "source_sha256": before,
              "episodes": [], "failures": [], "limits": [
                  "Bounded sampled episodes and the named rival/lookup families only; no universal uniqueness claim.",
                  "Five-demo minimum reflects explicit key, hit-size and no-hit teaching cost.",
                  "Public full challenges are controller-side; reveal only the current query to the model.",
                  "This report grants neither owner acceptance nor training admission."]}
    private, publics, cache = [], {}, {}
    evaluations = 0
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        report["racket"] = identity

        def execute(program, grid):
            nonlocal evaluations
            key = (program, json.dumps(grid, separators=(",", ":")))
            if key not in cache:
                evaluations += 1
                cache[key] = _grid(apply(program, deepcopy(grid)))
            return deepcopy(cache[key])

        matched_inputs = None
        try:
            canonical = native.program({"turn_source": "key"})
            for setting in ("key", "hit_size"):
                settings = {"turn_source": setting}
                entry = {"settings": settings, "rivals": [], "lookup_families": []}
                report["episodes"].append(entry)
                try:
                    episode = native.generate(seed, settings, demos=demos, queries=4)
                    program = native.program(settings)
                    if episode.get("program_solution") != program:
                        raise ValueError("Generated program differs from program(settings)")
                    if len(episode["train"]) != demos or len(episode["test"]) != 4:
                        raise ValueError("Generated pair counts differ from the request")
                    inputs = [p["input"] for split in ("train", "test") for p in episode[split]]
                    if len({json.dumps(g) for g in inputs}) != demos + 4:
                        raise ValueError("Demonstrations and queries must have distinct inputs")
                    if matched_inputs is None:
                        matched_inputs = deepcopy(inputs)
                    elif inputs != matched_inputs:
                        raise ValueError("Shared-grammar settings have confounded input sampling")
                    for split in ("train", "test"):
                        for p in episode[split]:
                            if execute(program, _grid(p["input"])) != _grid(p["output"]):
                                raise ValueError(f"Generated {split} label differs from fresh Racket execution")
                    entry["replayed_labels"] = demos + 4
                    entry["query_sizes"] = [[len(p["input"]), len(p["input"][0])] for p in episode["test"]]
                    private.append({"seed": seed, "settings": settings, **episode})
                    for name, rival in native.rival_programs(settings).items():
                        row = {"name": name, "program_sha256": _sha(rival.encode())}
                        entry["rivals"].append(row)
                        try:
                            mismatches = [i for i, p in enumerate(episode["train"])
                                          if execute(rival, p["input"]) != p["output"]]
                            row.update(survives_demos=not mismatches,
                                       eliminating_demo=mismatches[0] if mismatches else None)
                            row["surviving_query_disagreements"] = []
                            if not mismatches:
                                for i, pair in enumerate(episode["test"]):
                                    prediction = execute(rival, pair["input"])
                                    if prediction != pair["output"]:
                                        row["surviving_query_disagreements"].append({
                                            "query_index": i, "input": pair["input"],
                                            "output": prediction, "reference_output": pair["output"]})
                                if row["surviving_query_disagreements"]:
                                    row["program"] = rival
                        except Exception as exc:
                            row["execution_error"] = f"{type(exc).__name__}: {exc}"
                            row["program"] = rival
                    entry["lookup_families"] = [_lookup_audit(kind, episode, canonical, execute)
                                                 for kind in ("key", "hit_color", "height")]
                    public = public_challenge_bytes(episode)
                    changed = deepcopy(episode)
                    changed.update(seed="changed private seed", settings={"private": "changed"},
                                   program_solution="changed private program")
                    for p in changed["test"]:
                        p["output"] = [[(v + 1) % 10 for v in row] for row in p["output"]]
                    if public_challenge_bytes(changed) != public:
                        raise ValueError("Private metadata or answers changed public bytes")
                    first = {"train": episode["train"], "test": episode["test"][:1]}
                    first_bytes = public_challenge_bytes(first)
                    single = native.generate(seed, settings, demos=demos, queries=1)
                    if public_challenge_bytes(single) != first_bytes:
                        raise ValueError("First-turn content depends on future query count")
                    for blob in (public, first_bytes):
                        publics[_sha(blob)] = blob
                    entry["public_projection"] = {
                        "full_id": public_challenge_id(episode), "first_turn_id": public_challenge_id(first),
                        "private_mutation_invariant": True, "single_query_first_turn_identical": True}
                    gaps = [r["name"] for r in entry["rivals"]
                            if r.get("execution_error") or r.get("surviving_query_disagreements")]
                    gaps += [r["family"] for r in entry["lookup_families"] if r["surviving_query_disagreements"]]
                    entry["status"] = "failed" if gaps else "passed"
                    if gaps:
                        report["failures"].append({"settings": settings, "rivals": gaps})
                except Exception as exc:
                    entry.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                    report["failures"].append({"settings": settings, "error": entry["error"]})
        finally:
            bridge.close()
    after = _sources()
    if after != before:
        report["failures"].append({"error": "Source changed during audit", "after_sha256": after})
    report.update(status="failed" if report["failures"] else "passed",
                  racket_evaluations=evaluations, attempted_settings=2,
                  successful_settings=sum(e.get("status") == "passed" for e in report["episodes"]))
    out.mkdir(parents=True)
    (out / "private-episodes.json").write_bytes(_json_bytes(private))
    (out / "self-review.json").write_bytes(_json_bytes(report))
    (out / "public").mkdir()
    for name, blob in sorted(publics.items()):
        (out / "public" / f"{name}.json").write_bytes(blob)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, choices=(5, 6), default=5)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = audit(args.seed, args.demos, args.out)
    print(json.dumps({k: report[k] for k in ("status", "seed", "demos", "queries", "attempted_settings",
                                             "successful_settings", "racket_evaluations", "failures")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
