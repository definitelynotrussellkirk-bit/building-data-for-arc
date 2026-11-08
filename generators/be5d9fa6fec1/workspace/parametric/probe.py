"""Bounded runnable self-audit, protected Racket labels, and visible export.

Run through review.py run so the bundled Racket and same-tree imports are used.
"""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", action="append", type=int)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("choose a new output directory")
    seeds = args.seed if args.seed is not None else [0, 17]
    path = Path(__file__).resolve().with_name("adapter.py")
    spec = importlib.util.spec_from_file_location("row_run_probe_adapter", path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import public_challenge_bytes
    args.out.mkdir(parents=True)
    rows, examples, failures, evaluations = [], [], [], 0
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("a live protected Racket backend is required")
        for seed in seeds:
            for demos in (2, 6):
                paired_inputs = None
                for mode in ("fixed3", "height_plus_one"):
                    settings = {"step_mode": mode}
                    try:
                        episode = adapter.generate(seed, settings, demos, 4)
                        inputs = [p["input"] for p in episode["train"] + episode["test"]]
                        assert len({json.dumps(g) for g in inputs}) == demos + 4
                        assert paired_inputs is None or paired_inputs == inputs
                        paired_inputs = inputs
                        rule = wrap_rule(episode["program_solution"])
                        for pair in episode["train"] + episode["test"]:
                            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")"
                                                       for row in pair["input"]) + ")"
                            actual = bridge.eval_text(f"({rule} {literal})")
                            evaluations += 1
                            assert actual == pair["output"], "Racket/Python label mismatch"
                            pair["output"] = actual
                        teaching = adapter.teaching_report(episode["train"], settings)
                        assert teaching["all_refuted"], teaching
                        altered = deepcopy(episode)
                        altered.update(seed=-123, settings={"private": 9}, program_solution="private")
                        altered["test"][0]["output"][0][0] = 9
                        assert public_challenge_bytes(altered) == public_challenge_bytes(episode)
                        first = adapter.visible_turn(episode, 0)
                        single = adapter.generate(seed, settings, demos, 1)
                        assert public_challenge_bytes(first) == public_challenge_bytes(single)
                        rows.append({"seed": seed, "settings": settings, "demos": demos, "queries": 4,
                                     "labels": demos + 4, "teaching": teaching,
                                     "query_shapes": [[len(p["input"]), len(p["input"][0])]
                                                      for p in episode["test"]]})
                        examples.append(episode)
                    except Exception as error:
                        failures.append({"seed": seed, "settings": settings, "demos": demos,
                                         "error": str(error)})
    exported = adapter.write_batch(examples, args.out / "examples") if examples else None
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(path.parent.iterdir()) if p.suffix in (".py", ".json", ".rkt")}
    report = {"task_id": "be5d9fa6fec1", "status": "passed" if not failures else "failed",
              "source_sha256": sources, "racket": {key: value for key, value in identity.items()
                 if key in ("schema", "backend", "protected") or key.endswith("sha256")},
              "requests": len(seeds) * 4, "completed": len(rows), "failures": failures,
              "racket_evaluations": evaluations, "checks": rows, "export": exported,
              "limits": "Finite seeds and declared rivals only; no universal uniqueness or training-admission claim."}
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "requests", "completed", "failures", "racket_evaluations")}))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
