#!/usr/bin/env python3
"""Finite output-profile audit of retained real reference labels.

Generated input: official arcpuzzles-lesson-census-v1 JSON/gzip (requires
--adapter largest4_color3_to8), or a task-authored observation wrapper around
an unmodified public apply receipt. Canonical input is a task-authored wrapper
with ledger/program/rule hashes and explicit public-result indices. The wrapper
schema task-output-profile-observations-v1 is NOT an official shared format.
The complete canonical pair set is read from the actual checkout ledger;
--canonical-ledger can select that file explicitly in a relocated workflow.
No sampling, rival execution, Racket execution or training admission occurs.
Exit0 observed support per band; exit1 missing canonical profiles; exit2 errors.
Report destinations must be new; existing files and symlinks are preserved.
"""
from collections import Counter
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zlib

TASK_ID = "8738d400fb96"
ADAPTER = {"kind": "largest4_color3_to8", "shape_color": 3, "output_color": 8,
           "background": 0, "connectivity": 4}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def valid_hash(value, name, length=64):
    require(isinstance(value,str) and len(value)==length and all(c in "0123456789abcdef" for c in value), f"invalid {name}")
    return value


def positive(value, name):
    require(type(value) is int and value>0, f"invalid {name}")
    return value


def canonical_authority(ledger_path=None):
    """Read the actual authority rather than trusting receipt inventory fields."""
    if ledger_path is None:
        candidates = (base / suffix for base in Path(__file__).resolve().parents
                      for suffix in ("shared/data/canonical/puzzles.jsonl",
                                     "data/canonical/puzzles.jsonl"))
        ledger_path = next((p for p in candidates if p.is_file()), None)
    require(ledger_path is not None, "canonical ledger not found; pass --canonical-ledger")
    raw = Path(ledger_path).read_bytes()
    records = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        require(isinstance(row, dict), "malformed canonical record")
        if row.get("task_id") == TASK_ID:
            records.append(row)
    require(len(records) == 1, "expected exactly one selected canonical record")
    record = records[0]
    program = record.get("program_solution")
    require(isinstance(program, str) and bool(program), "canonical program missing")
    pairs = {}
    for split in ("train", "test"):
        examples = record.get(split)
        if isinstance(examples, dict):
            examples = [examples]
        require(isinstance(examples, list), "malformed canonical split")
        for index, pair in enumerate(examples):
            require(isinstance(pair, dict) and valid_grid(pair.get("input")), "malformed canonical input")
            if "output" not in pair:
                require(split == "test", "missing canonical training label")
                continue
            require(valid_grid(pair["output"]), "malformed canonical label")
            pairs[(split, index)] = pair
    require(bool(pairs), "no labelled canonical pairs")
    return {"ledger_sha256": hashlib.sha256(raw).hexdigest(),
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            # This explicit task adapter's canonical program contains no comments.
            "rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
            "pairs": pairs}


def valid_grid(grid):
    return (isinstance(grid,list) and bool(grid) and isinstance(grid[0],list) and bool(grid[0])
            and all(isinstance(row,list) and len(row)==len(grid[0])
                    and all(type(v) is int and 0<=v<=9 for v in row) for row in grid))


def classify(grid, output):
    """Explicit adapter: largest cardinal color3 mass versus color8 output."""
    require(valid_grid(grid) and valid_grid(output), "malformed integer grid")
    require(len(grid)==len(output) and len(grid[0])==len(output[0]), "output shape differs")
    require(all(v in (0,8) for row in output for v in row), "non-cyan output foreground")
    unseen = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3}
    require(bool(unseen), "no color3 component")
    masses = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        pending,cells = [start],{start}
        while pending:
            r,c = pending.pop()
            adjacent = {(r-1,c),(r+1,c),(r,c-1),(r,c+1)} & unseen
            unseen.difference_update(adjacent)
            cells.update(adjacent)
            pending.extend(adjacent)
        masses.append(len(cells))
    mass = max(masses)
    visible = sum(v==8 for row in output for v in row)
    require(visible<=mass, "output mass exceeds selected input mass")
    return "empty" if not visible else "full" if visible==mass else "partial"


def compare_support(canonical_profiles, profiles_by_band):
    """Task-independent comparison of finite categorical support."""
    required = set(canonical_profiles)
    require(bool(required) and isinstance(profiles_by_band,dict) and bool(profiles_by_band), "missing profile population")
    result = {}
    for band,profiles in profiles_by_band.items():
        require(isinstance(band,str) and band and bool(profiles), "empty requested band")
        counts = Counter(profiles)
        result[band] = {"observations":sum(counts.values()), "profile_counts":dict(counts), "missing":sorted(required-set(counts))}
    return result


def observations_wrapper(value, role, authority=None):
    require(value.get("schema")=="task-output-profile-observations-v1" and value.get("role")==role
            and value.get("task_id")==TASK_ID, "observation schema/role/task mismatch")
    require(value.get("adapter")==ADAPTER, "missing/mismatched explicit adapter")
    rule = valid_hash(value.get("rule_callable_sha256"), "rule_callable_sha256")
    valid_hash(value.get("executed_rule_hash"), "executed_rule_hash", 12)
    execution = value.get("execution",{})
    require(isinstance(execution,dict) and type(execution.get("exit_code")) is int
            and execution["exit_code"]==0 and execution.get("timed_out") is False, "incomplete reference execution")
    receipt = value.get("apply_receipt",{})
    require(isinstance(receipt,dict) and receipt.get("schema")=="arcpuzzles-apply-v1"
            and receipt.get("task_id")==TASK_ID and receipt.get("reference")=="canonical"
            and receipt.get("rule_hash_matches_catalog") is True, "invalid public apply receipt")
    require(receipt.get("rule_text_sha256")==rule and receipt.get("executed_rule_hash")==value["executed_rule_hash"], "rule binding mismatch")
    require(receipt.get("generator_sha256")==valid_hash(value.get("label_generator_sha256"),"label_generator_sha256"), "apply catalog-source mismatch")
    results = receipt.get("results")
    expected_results = positive(value.get("expected_apply_results"),"expected_apply_results")
    require(isinstance(results,list) and len(results)==expected_results, "missing apply results")
    for i,row in enumerate(results):
        require(isinstance(row,dict) and row.get("index")==i and row.get("valid_output") is True and row.get("error") is None, "errored public result")
        require(valid_grid(row.get("input")) and valid_grid(row.get("output")), "malformed paired grids")
        require(digest(row["input"])==row.get("input_sha256") and digest(row["output"])==row.get("output_sha256"), "paired grid hash mismatch")
    samples = value.get("samples")
    expected = positive(value.get("expected_pairs"),"expected_pairs")
    require(isinstance(samples,list) and len(samples)==expected, "missing paired observations")
    require(all(isinstance(s,dict) and type(s.get("result_index")) is int and 0<=s["result_index"]<expected_results for s in samples), "invalid result mapping")
    indices = [s["result_index"] for s in samples]
    require(len(indices)==len(set(indices)), "duplicate result mapping")
    mapped = [(s,results[s["result_index"]]) for s in samples]
    if role=="canonical":
        authority = authority or canonical_authority()
        require(value.get("ledger_sha256") == authority["ledger_sha256"], "canonical ledger binding mismatch")
        require(value.get("canonical_program_sha256") == authority["program_sha256"], "canonical program binding mismatch")
        require(value["executed_rule_hash"] == authority["rule_hash"], "canonical normalized rule mismatch")
        identities = [(s.get("split"), s.get("pair_index")) for s, _ in mapped]
        require(all(isinstance(split, str) and type(index) is int for split, index in identities), "invalid canonical pair identity")
        require(len(identities) == len(set(identities)) == len(authority["pairs"])
                and set(identities) == set(authority["pairs"]), "incomplete canonical pair inventory")
        for identity, (_, result) in zip(identities, mapped):
            pair = authority["pairs"][identity]
            require(result["input"] == pair["input"] and result["output"] == pair["output"],
                    "mapped result differs from authoritative canonical pair")
        return {"canonical":[r for _,r in mapped]},None,rule
    source = valid_hash(value.get("generator_sha256"),"generator_sha256")
    generation = value.get("generation",{})
    require(isinstance(generation,dict) and generation.get("source_sha256")==source and generation.get("expected_pairs")==expected, "generation source/count mismatch")
    require(expected==expected_results and set(indices)==set(range(expected_results)), "partial generated observations")
    require(generation.get("inputs_sha256")==digest([r["input"] for _,r in mapped]), "generation input-set mismatch")
    bands,counts = value.get("bands"),value.get("expected_per_band",{})
    require(isinstance(bands,list) and bool(bands) and all(isinstance(b,str) and b for b in bands)
            and len(bands)==len(set(bands)) and isinstance(counts,dict) and set(counts)==set(bands), "missing requested bands/counts")
    groups = {b:[] for b in bands}
    for sample,row in mapped:
        require(sample.get("band") in groups, "unknown sample band")
        groups[sample["band"]].append(row)
    require(all(len(groups[b])==positive(counts[b],"expected band count") for b in bands), "partial band observations")
    return groups,source,rule


def observations_census(value, adapter):
    require(adapter in (ADAPTER,ADAPTER["kind"]), "census requires explicit --adapter largest4_color3_to8")
    require(value.get("schema")=="arcpuzzles-lesson-census-v1" and value.get("task_id")==TASK_ID, "census task/schema mismatch")
    complete = {"no_ambiguity_found","no_declared_ambiguity","warning","ambiguous","no_contract","hook_only"}
    require(value.get("status") in complete and value.get("production_status") in complete
            and value.get("rotation_status") in complete|{"not_requested"} and value.get("errors")==[], "incomplete/errored census")
    execution = value.get("execution",{})
    require(isinstance(execution,dict) and execution.get("timed_out") is False and type(execution.get("exit_code")) is int
            and execution["exit_code"]==(1 if value["status"]=="ambiguous" else 0), "incomplete census execution")
    source,rule = (valid_hash(value.get(k),k) for k in ("generator_sha256","rule_callable_sha256"))
    manifest = value.get("runtime_manifest",{})
    require(isinstance(manifest,dict) and hashlib.sha256((json.dumps(manifest,indent=2)+"\n").encode()).hexdigest()==value.get("runtime_manifest_sha256"), "manifest hash mismatch")
    files = manifest.get("files",[])
    require(isinstance(files,list) and all(isinstance(f,dict) for f in files), "malformed manifest files")
    entries = [f for f in files if f.get("library_path")==f"generators/{TASK_ID}/generator.py"]
    require(manifest.get("task_id")==TASK_ID and len(entries)==1 and entries[0].get("sha256")==source, "manifest generator mismatch")
    lessons,summary,sampler = value.get("lessons"),value.get("summary",{}),value.get("sampler",{})
    require(isinstance(lessons,list) and bool(lessons) and isinstance(summary,dict) and isinstance(sampler,dict), "missing census population")
    require(positive(summary.get("requested"),"requested")==summary.get("materialized")==len(lessons), "partial census")
    require(all(type(summary.get(k)) is int and summary[k]==0 for k in ("materialization_errors","scoring_errors","rotation_scoring_errors")), "census scoring/materialization errors")
    bands = sampler.get("bands")
    require(isinstance(bands,list) and bool(bands) and all(isinstance(b,str) and b for b in bands) and len(bands)==len(set(bands)), "invalid sampler bands")
    demos,queries,n = (positive(sampler.get(k),k) for k in ("n_demos","n_queries","per_band"))
    require(type(sampler.get("rotate_query")) is bool, "invalid rotation setting")
    groups,identities = {b:[] for b in bands},set()
    rotation_count = 0
    for lesson in lessons:
        require(isinstance(lesson,dict) and lesson.get("errors")==[], "errored/malformed lesson")
        band,index = lesson.get("band"),lesson.get("index")
        require(band in groups and type(index) is int and 0<=index<n and (band,index) not in identities, "invalid lesson identity")
        identities.add((band,index))
        instance = lesson.get("instance",{})
        require(isinstance(instance,dict) and digest(instance)==lesson.get("instance_sha256"), "instance hash mismatch")
        require(instance.get("task_id")==TASK_ID and instance.get("rule_task_id")==value.get("rule_task_id")
                and instance.get("rule_file")==value.get("rule_file"), "instance rule binding mismatch")
        train,tests = instance.get("train"),instance.get("test")
        tests = [tests] if isinstance(tests,dict) else tests
        require(isinstance(train,list) and len(train)==demos and isinstance(tests,list) and len(tests)==queries, "incomplete instance pairs")
        for pair in train+tests:
            require(isinstance(pair,dict) and valid_grid(pair.get("input")) and valid_grid(pair.get("output")), "malformed labelled pair")
            groups[band].append(pair)
        rotations = lesson.get("rotations",[])
        require(isinstance(rotations,list) and all(isinstance(r,dict) and r.get("errors")==[] for r in rotations), "errored rotations")
        require(len(rotations)==(demos+1 if sampler["rotate_query"] else 0) and (not rotations or queries==1), "incomplete rotation scoring")
        rotation_count += len(rotations)
    require(len(identities)==n*len(bands) and all(len(groups[b])==n*(demos+queries) for b in bands), "partial band census")
    require(sum(map(len,groups.values()))==summary.get("pairs") and rotation_count==summary.get("rotations"), "census pair/rotation count mismatch")
    if sampler.get("enumerate_schedule_period"):
        coverage = value.get("schedule_coverage",{})
        require(isinstance(coverage,dict) and coverage.get("status")=="complete_fixed_seed"
                and coverage.get("expected_lessons")==len(lessons) and coverage.get("expected_rotations")==rotation_count, "incomplete schedule census")
    return groups,source,rule


def analyze(canonical, generated, adapter=None, *, canonical_ledger=None):
    require(isinstance(canonical,dict) and isinstance(generated,dict), "expected receipt objects")
    authority = canonical_authority(canonical_ledger)
    cgroups,_,crule = observations_wrapper(canonical,"canonical",authority)
    if generated.get("schema")=="arcpuzzles-lesson-census-v1":
        groups,source,rule = observations_census(generated,adapter)
        require(generated.get("rule_source_sha256") == authority["program_sha256"], "census program source mismatch")
        require(generated.get("declared_rule_hash") == authority["rule_hash"], "census declared rule mismatch")
        ledger_entries = [f for f in generated["runtime_manifest"]["files"]
                          if f.get("library_path") == "shared/data/canonical/puzzles.jsonl"]
        require(len(ledger_entries) == 1 and ledger_entries[0].get("sha256") == authority["ledger_sha256"],
                "census canonical ledger mismatch")
    else:
        groups,source,rule = observations_wrapper(generated,"generated")
        require(generated.get("executed_rule_hash")==canonical.get("executed_rule_hash"), "normalized rule mismatch")
    require(rule==crule, "canonical/generated callable source mismatch")
    ccounts = Counter(classify(p["input"],p["output"]) for p in cgroups["canonical"])
    profiles = {b:[classify(p["input"],p["output"]) for p in pairs] for b,pairs in groups.items()}
    comparison = compare_support(ccounts,profiles)
    return {"schema":"task-output-profile-support-v1","task_id":TASK_ID,"adapter":ADAPTER,
            "status":"missing_canonical_output_profiles" if any(v["missing"] for v in comparison.values()) else "observed_support_in_each_band",
            "generator_sha256":source,"rule_callable_sha256":rule,"canonical_ledger_sha256":canonical["ledger_sha256"],
            "canonical_program_sha256":canonical["canonical_program_sha256"],"canonical_profile_counts":dict(ccounts),
            "required_profiles":sorted(ccounts),"per_band":comparison,
            "limits":["Finite support: a rare supported profile may be missed; targeted draws should resolve a failure before rejection.",
                      "Coarse output mass classes do not establish rule correctness, semantic diversity or useful frequency.",
                      "Intentional narrowed domains may need an explicit owner decision rather than an automatic coverage veto.",
                      "Retained reference labels/provenance are consumed without new sampling or reference execution.",
                      "No empirical Qwen3.5-9B benefit, approval or training admission is claimed."]}


def read(path):
    data = Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if data.startswith(b"\x1f\x8b") else data),hashlib.sha256(data).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical",required=True)
    parser.add_argument("--canonical-ledger", help="Actual canonical puzzles.jsonl; otherwise locate this checkout's copy")
    parser.add_argument("--generated",required=True)
    parser.add_argument("--adapter",choices=[ADAPTER["kind"]])
    parser.add_argument("--out",required=True)
    args = parser.parse_args(argv)
    try:
        canonical,chash = read(args.canonical)
        generated,ghash = read(args.generated)
        result = analyze(canonical,generated,args.adapter,canonical_ledger=args.canonical_ledger)
        result.update(canonical_receipt_sha256=chash,generated_receipt_sha256=ghash,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        code = 1 if result["status"]=="missing_canonical_output_profiles" else 0
    except (ValueError,KeyError,TypeError,OSError,EOFError,zlib.error) as exc:
        result = {"schema":"task-output-profile-support-v1","status":"error","errors":[f"{type(exc).__name__}: {exc}"]}
        code = 2
    out = Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    try:
        with out.open("x") as report:
            report.write(json.dumps(result,indent=2)+"\n")
    except OSError as exc:
        print(f"error: report not written: {exc}", file=sys.stderr)
        return 2
    print(f"{result['status']}: {out}")
    return code


if __name__=="__main__":
    sys.exit(main())
