#!/usr/bin/env python3
"""Rerun this family's bounded, source-bound semantic and export audit.

From the outer review packet:
  python3 review.py run python3 generators/1d26c382ab68/workspace/parametric/audit.py --out ../checks/1d26c382ab68/self-review

The command labels both settings using protected Racket, reports every failure,
and refuses to reuse an existing output directory. No qualification or approval
is granted by this reviewer-authored receipt.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import _grid, _real_evaluator
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("choose a fresh output directory")
    root = find_root(__file__)
    home = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("_audited_rotation_adapter", home / "adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    args.out.mkdir(parents=True)
    public = args.out / "public"
    public.mkdir()
    failures, jobs, cache, examples = [], [], {}, {}
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    source_files = [home / name for name in
                    ("adapter.py", "prototype.py", "canonical.rkt", "reflection.rkt", "promotion.json", "audit.py")]
    source_files.extend([home.parents[1] / "generator.py",
                         home.parents[1] / "tests/test_parametric_1d26c382ab68.py"])
    binding = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in source_files}
    try:
        for seed in (0, 17):
            for demos in (2, 6):
                input_sequences = []
                for target in ("rotation_match", "turn_guided_reflection"):
                    settings = {"target": target}
                    episode = adapter.generate(seed, settings, demos, 4)
                    program = adapter.program(settings)
                    pairs = episode["train"] + episode["test"]
                    sequence = [pair["input"] for pair in pairs]
                    input_sequences.append(sequence)
                    for index, pair in enumerate(pairs):
                        key = hashlib.sha256((program + json.dumps(pair["input"])).encode()).hexdigest()
                        if key not in cache:
                            cache[key] = _grid(apply(program, pair["input"]))
                        if cache[key] != pair["output"]:
                            failures.append({"seed": seed, "demos": demos, "target": target,
                                             "pair": index, "failure": "Racket label differs"})
                    certificate = adapter.teaching_check(episode)
                    if certificate["survivors"] != [target] or certificate["ambiguities"]:
                        failures.append({"seed": seed, "demos": demos, "target": target,
                                         "failure": "finite-rival ambiguity", "certificate": certificate})
                    one = adapter.generate(seed, settings, demos, 1)
                    view = adapter.model_view(episode, 0)
                    if public_challenge_bytes(view) != public_challenge_bytes(adapter.model_view(one, 0)):
                        failures.append({"failure": "first turn changed with query count"})
                    hidden = deepcopy(episode)
                    hidden.update(seed=-99, settings={"secret": True}, program_solution="private")
                    hidden["train"][0]["private"] = "private"
                    for pair in hidden["test"]:
                        pair["output"] = [[9]]
                    if adapter.model_view(hidden, 0) != view:
                        failures.append({"failure": "private fields changed visible projection"})
                    public_name = public_challenge_id(view) + ".json"
                    path = public / public_name
                    if path.exists():
                        failures.append({"failure": "duplicate public bytes"})
                    else:
                        path.write_bytes(public_challenge_bytes(view))
                    observations = [adapter.analyze(pair["input"]) for pair in pairs]
                    jobs.append({"seed": seed, "settings": settings, "demos": demos, "queries": 4,
                                 "labels_checked": len(pairs), "teaching": certificate,
                                 "input_sha256": [hashlib.sha256(json.dumps(g).encode()).hexdigest() for g in sequence],
                                 "turns": [row["turn"] for row in observations],
                                 "scales": [row["scale"] for row in observations],
                                 "public_file": "public/" + public_name})
                    if seed == 0 and demos == 2:
                        examples[target] = {"train": episode["train"],
                                            "explanation": "Identical lower scene, different upper template and selected object."}
                if input_sequences[0] != input_sequences[1]:
                    failures.append({"failure": "private setting changed sampled inputs", "seed": seed, "demos": demos})
    except Exception as error:
        failures.append({"failure": type(error).__name__, "message": str(error)})
    finally:
        bridge.close()
    report = {"schema": "rotation-template-parametric-self-review-v1", "status": "passed" if not failures else "failed",
              "task_id": "1d26c382ab68", "source_sha256": binding, "racket": identity,
              "episodes_checked": len(jobs), "label_claims_checked": sum(row["labels_checked"] for row in jobs),
              "distinct_protected_racket_evaluations": len(cache), "jobs": jobs,
              "minimal_teaching_examples": examples, "failures": failures,
              "limits": "Finite listed rivals and seeds; Python rival predictions, independently Racket-checked true labels. No owner acceptance or training admission."}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                     ("status", "episodes_checked", "label_claims_checked", "distinct_protected_racket_evaluations", "failures")}))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
