"""Bounded actual-default lesson review for strip transport."""
import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import find_root, load_selected_generator

TASK = "c181f41a09f0"
EXPECTED = "fdaef0b9eb49b55dd60c29589e8f5fca51519fe52b3357ab2f146234fdd7eba0"


def sha(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def replace_one(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Canonical expression drift")
    return source.replace(old, new)


def variants(source):
    out = {}
    for axis, low, high in (("c", "c1", "(- c2 2)"), ("r", "r1", "(- r2 2)")):
        old = f"(dst-{axis} (if (zero? d) {high} {low}))"
        out[("horizontal" if axis == "c" else "vertical") + "_always_low"] = replace_one(source, old, f"(dst-{axis} {low})")
        out[("horizontal" if axis == "c" else "vertical") + "_always_high"] = replace_one(source, old, f"(dst-{axis} {high})")
    mirrored = replace_one(source, "(tr (+ dr (- rr sr)))", "(tr (+ dr (- (- nr 1) (- rr sr))))")
    out["reverse_cap_block"] = replace_one(mirrored, "(tc (+ dc (- cc sc)))", "(tc (+ dc (- (- nc 1) (- cc sc))))")
    clear = "(cleared (paint-cells acc (positions-in-rect r1 c1 r2 c2) bg))"
    out["retain_unmarked_strip"] = replace_one(source, clear,
        "(cleared (if (and (eq? (hdir obj) #f) (eq? (vdir obj) #f)) acc (paint-cells acc (positions-in-rect r1 c1 r2 c2) bg)))")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    if not 1 <= args.count <= 8: raise ValueError("Bounded probe supports1..8 lessons")
    root = find_root(__file__)
    gen, _, source_sha = load_selected_generator(TASK, root=root)
    if source_sha != EXPECTED: raise ValueError("Peer source differs from the reviewed source")
    catalog = Catalog(root)
    desc = catalog.describe(TASK)
    selected = {x["program_solution"] for x in catalog.get(TASK)["variants"]}
    assert len(selected) == 1
    canonical = next(iter(selected)); programs = variants(canonical)
    request = {"count": args.count, "seed": args.seed, "n_train": None,
               "n_test": 1, "allow_unapproved": True, "timeout": 60}
    episodes = catalog.generate(TASK, **request)
    result = {"schema": "arcpuzzles-bounded-peer-rival-probe-v1", "task_id": TASK,
              "generator_sha256": source_sha, "rule_hash": gen.RULE_HASH,
              "canonical_program_sha256": sha(canonical.encode()),
              "probe_sha256": sha(Path(__file__).read_bytes()), "request": request,
              "approved_at_probe": desc.get("approved"), "approval_reasons": desc.get("approval_reasons"),
              "programs": programs, "canonical_program": canonical, "lessons": [], "findings": [],
              "summary": {n: {"demo_fits": 0, "query_disagreements_after_demo_fit": 0} for n in programs},
              "protected_evaluations": 0, "public_generated_pairs": sum(len(e["train"])+len(e["test"]) for e in episodes),
              "limits": "Four default lessons and six finite rivals by default; Racket evaluates rival demos, then only surviving queries. Retained findings also replay the exact canonical labels. No full battery, production edit, approval or parametric admission."}
    cache = {}
    runtime = root / "shared/runtime"
    with _local_imports(runtime, root / "generators" / TASK / "workspace"):
        execute, identity, bridge = _real_evaluator(runtime)
        result["racket"] = identity
        def apply(program, grid):
            key = (sha(program.encode()), sha(grid))
            if key not in cache:
                cache[key] = _grid(execute(program, grid)); result["protected_evaluations"] += 1
            return cache[key]
        try:
            retained = set()
            for index, ep in enumerate(episodes):
                row = {"index": index, "sample_index": ep.get("sample_index"),
                       "train_count": len(ep["train"]), "test_count": len(ep["test"]),
                       "profiles": {split: [gen.profile_signature(p["input"]) for p in ep[split]] for split in ("train", "test")},
                       "rivals": {}}
                for name, program in programs.items():
                    observed = [apply(program, pair["input"]) for pair in ep["train"]]
                    fits = all(a == p["output"] for a, p in zip(observed, ep["train"]))
                    row["rivals"][name] = {"demo_fits": fits}
                    if not fits: continue
                    result["summary"][name]["demo_fits"] += 1
                    answers = [apply(program, p["input"]) for p in ep["test"]]
                    wrong = [i for i, (a, p) in enumerate(zip(answers, ep["test"])) if a != p["output"]]
                    row["rivals"][name]["query_disagreements"] = wrong
                    result["summary"][name]["query_disagreements_after_demo_fit"] += len(wrong)
                    if wrong and name not in retained:
                        for pair in ep["train"] + ep["test"]: assert apply(canonical, pair["input"]) == pair["output"]
                        result["findings"].append({"rival": name, "lesson_index": index,
                            "train": ep["train"], "test": ep["test"],
                            "rival_outputs": {"train": observed, "test": answers}, "query_disagreements": wrong,
                            "status": "protected_racket_confirmed"})
                        retained.add(name)
                result["lessons"].append(row)
        finally: bridge.close()
    assert hashlib.sha256((root / "generators" / TASK / "generator.py").read_bytes()).hexdigest() == source_sha
    result["status"] = "findings" if result["findings"] else "bounded_no_finding"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": result["status"], "lessons": len(episodes), "findings": len(result["findings"]),
                      "summary": result["summary"], "protected_evaluations": result["protected_evaluations"],
                      "output": str(args.out), "sha256": sha(args.out.read_bytes())}, sort_keys=True))


if __name__ == "__main__": main()
