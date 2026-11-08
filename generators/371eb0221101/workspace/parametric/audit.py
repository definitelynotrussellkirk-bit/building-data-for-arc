#!/usr/bin/env python3
"""Bounded semantic/export audit for the native L-rotation family.

Run from the packet outer folder:
  python3 review.py run python3 generators/371eb0221101/workspace/parametric/audit.py --out ../checks/371eb0221101/self-review

All true labels are replayed through protected Racket. Rival predictions remain
finite Python checks. This tool grants no qualification or owner acceptance.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _real_evaluator
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    args = parser.parse_args(argv)
    seeds = args.seed if args.seed is not None else [0, 17]
    if not 1 <= len(seeds) <= 4 or len(set(seeds)) != len(seeds) or any(not 0 <= s < 2**63 for s in seeds):
        parser.error("provide one to four distinct seeds in 0..2^63-1")
    if args.out.exists():
        parser.error("choose a fresh output directory")
    root = find_root(__file__)
    home = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("_audited_native_l_adapter", home / "adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()
    sources = [home / name for name in ("adapter.py", "native.py", "prototype.py", "promotion.json", "audit.py")]
    sources += [home.parents[1] / "generator.py", home.parents[1] / "tests/test_native_rotation.py"]
    binding = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    programs = {rule: adapter.program({"rotation_rule": rule})
                for rule in ("clockwise", "counterclockwise", "color_count")}
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    failures, jobs, cache, examples = [], [], {}, {}
    try:
        for seed in seeds:
            for demos in (2, 6):
                inputs_by_setting = []
                for rule in ("clockwise", "counterclockwise", "color_count"):
                    settings = {"rotation_rule": rule}
                    episode = adapter.generate(seed, settings, demos, 4)
                    if episode["program_solution"] != programs[rule]:
                        raise ValueError("executed setting program changed during audit")
                    pairs = episode["train"] + episode["test"]
                    inputs = [p["input"] for p in pairs]
                    inputs_by_setting.append(inputs)
                    for i, pair in enumerate(pairs):
                        key = hashlib.sha256((episode["program_solution"]+json.dumps(pair["input"])).encode()).hexdigest()
                        if key not in cache:
                            cache[key] = _grid(apply(episode["program_solution"], pair["input"]))
                        if cache[key] != pair["output"]:
                            failures.append({"seed": seed, "demos": demos, "rule": rule,
                                             "pair": i, "failure": "Racket label differs"})
                    certificate = adapter.teaching_check(episode)
                    if certificate["survivors"] != [rule] or certificate["ambiguities"]:
                        failures.append({"failure": "finite-rival ambiguity", "seed": seed,
                                         "demos": demos, "rule": rule, "certificate": certificate})
                    view = adapter.model_view(episode, 0)
                    one = adapter.generate(seed, settings, demos, 1)
                    if public_challenge_bytes(view) != public_challenge_bytes(adapter.model_view(one, 0)):
                        failures.append({"failure": "first turn depends on query count"})
                    hidden = deepcopy(episode)
                    hidden.update(seed=-123, settings={"secret": True}, program_solution="private")
                    hidden["train"][0]["private"] = "private"
                    for pair in hidden["test"]:
                        pair["output"] = [[9]]
                    if adapter.model_view(hidden, 0) != view:
                        failures.append({"failure": "private data leaks into model view"})
                    filename = public_challenge_id(view)+".json"
                    path = public_dir / filename
                    if path.exists():
                        failures.append({"failure": "duplicate visible bytes"})
                    else:
                        path.write_bytes(public_challenge_bytes(view))
                    observations = [adapter.analyze(g) for g in inputs]
                    jobs.append({"seed": seed, "settings": settings, "demos": demos, "queries": 4,
                                 "labels_checked": len(pairs), "teaching": certificate,
                                 "input_sha256": [hashlib.sha256(json.dumps(g).encode()).hexdigest() for g in inputs],
                                 "profiles": [{k: row[k] for k in ("height", "width", "n_objects", "color_counts")} for row in observations],
                                 "public_file": "public/"+filename})
                    if seed == seeds[0] and demos == 2:
                        examples[rule] = {"train": episode["train"],
                                          "explanation": "One remote L changes color; count vectors 1,2,3,4 become 1,1,4,4. Mixed scales defeat pixel-count substitutes."}
                if inputs_by_setting[0] != inputs_by_setting[1] or inputs_by_setting[0] != inputs_by_setting[2]:
                    failures.append({"failure": "setting altered sampled inputs", "seed": seed, "demos": demos})
    except Exception as exc:
        failures.append({"failure": type(exc).__name__, "message": str(exc)})
    finally:
        bridge.close()
    report = {"schema": "l-rotation-native-self-review-v1", "task_id": "371eb0221101",
              "status": "passed" if not failures else "failed", "source_sha256": binding,
              "programs": {rule: {"text": source, "sha256": hashlib.sha256(source.encode()).hexdigest()}
                           for rule, source in programs.items()},
              "racket": identity, "episodes_checked": len(jobs),
              "label_claims_checked": sum(job["labels_checked"] for job in jobs),
              "distinct_protected_racket_evaluations": len(cache), "jobs": jobs,
              "minimal_teaching_examples": examples, "failures": failures,
              "limits": "Finite declared rivals and seeds; Python rival predictions with independently Racket-checked true labels. Contextual gating, not iterative state simulation. No acceptance or training admission."}
    (args.out / "report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: report[k] for k in ("status", "episodes_checked", "label_claims_checked", "distinct_protected_racket_evaluations", "failures")}))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
