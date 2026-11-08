"""Build a small, authoritative witness pack from the current declarations.

Run through run_with_racket.py from WORK. The public Racket apply command labels
all inputs; no Python mirror supplies expected outputs. This is authoring work,
never a visible-only solve tool. Existing evidence is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "f9cd85012aa8"


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--band", choices=("easy", "medium", "hard"), default="medium")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be a new path")
    args.out.mkdir(parents=True)
    destination = args.out.resolve()
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    tiny = [[6, 0, 0, 0, 0, 0],
            [6, 6, 0, 2, 2, 0],
            [0, 0, 0, 2, 2, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0]]
    cases = [{"name": f"canonical_{i}", "kind": "canonical", "input": pair["input"]}
             for i, pair in enumerate(canonical)]
    cases.append({"name": "tiny_largest_object", "kind": "hand_built_domain_witness",
                  "input": tiny, "exact_input_emitted_by_default": False})
    for index in range(module.LESSON_SCHEDULE_PERIOD):
        cases.append({"name": f"generated_{index}", "kind": "generated",
                      "seed": args.seed, "sample_index": index,
                      "difficulty": args.band, "overrides": {},
                      "input": module.generate(args.seed, index, difficulty=args.band)})
    input_path = destination / "inputs.json"
    racket_path = destination / "racket.json"
    save(input_path, [case["input"] for case in cases])
    command = [sys.executable, "-m", "arcpuzzles", "apply", TASK_ID,
               "--input", str(input_path), "--check-generator-domain", "--out", str(racket_path)]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    (destination / "apply.stdout.log").write_text(completed.stdout)
    (destination / "apply.stderr.log").write_text(completed.stderr)
    provenance = {"schema": "f9cd85012aa8-authoritative-witness-pack-v1",
                  "task_id": TASK_ID, "generator_sha256": source_hash,
                  "generator_source": str(source),
                  "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                  "reference_argv": command, "reference_exit_code": completed.returncode,
                  "seed": args.seed, "difficulty": args.band,
                  "limitations": "One fixed seed/band/cycle; finite declared rivals only. The tiny witness is hand-built, not an exact default draw."}
    save(destination / "commands.json", provenance)
    if completed.returncode:
        return completed.returncode
    receipt = json.loads(racket_path.read_text())
    rows = receipt["results"]
    errors = []
    if receipt.get("generator_sha256") != source_hash:
        errors.append("generator changed during reference execution")
    if len(rows) != len(cases):
        errors.append("reference result count mismatch")
    shortcuts = module.CANONICAL_SHORTCUTS
    competitors = module.LESSON_COMPETITORS
    canonical_fits = {name: [] for name in shortcuts}
    generated_refutations = {name: [] for name in competitors}
    focus = {"count_max", "aspect_max", "sole_else_unique_area12", "cap_four"}
    for case, row in zip(cases, rows):
        case["output"] = row.get("output")
        case["input_sha256"] = row.get("input_sha256")
        case["output_sha256"] = row.get("output_sha256")
        case["domain"] = row.get("generator_domain")
        case["input_dimensions"] = [len(case["input"]), len(case["input"][0])]
        case["output_dimensions"] = [len(case["output"]), len(case["output"][0])] if case["output"] else None
        if row.get("error") or not row.get("valid_output"):
            errors.append(f"{case['name']}: invalid reference result")
        if row.get("generator_domain", {}).get("status") != "valid":
            errors.append(f"{case['name']}: not in selected generator domain")
        predictions = {name: rival(case["input"]) for name, rival in competitors.items()}
        case["refuted_competitors"] = [name for name, output in predictions.items()
                                      if output != case["output"]]
        case["focus_rival_outputs"] = {name: output for name, output in predictions.items() if name in focus}
        if case["kind"] == "canonical":
            i = int(case["name"].rsplit("_", 1)[1])
            if case["output"] != canonical[i]["output"]:
                errors.append(f"{case['name']}: canonical label disagrees with Racket")
            for name, rival in shortcuts.items():
                canonical_fits[name].append(rival(case["input"]) == case["output"])
        if case["kind"] == "generated":
            for name in case["refuted_competitors"]:
                generated_refutations[name].append(case["sample_index"])
    for name, fits in canonical_fits.items():
        if not fits or not all(fits):
            errors.append(f"{name}: false canonical-shortcut declaration")
    for name, indices in generated_refutations.items():
        if len(indices) < 2:
            errors.append(f"{name}: fewer than two generated refutations")
    save(destination / "witnesses.json", dict(provenance, status="failed" if errors else "passed",
         executed_rule_hash=receipt["executed_rule_hash"], rule_text_sha256=receipt["rule_text_sha256"],
         canonical_fits=canonical_fits, generated_refutations=generated_refutations,
         errors=errors, cases=cases))
    print(json.dumps({"status": "failed" if errors else "passed", "cases": len(cases),
                      "unique_competitors": len(competitors), "errors": errors,
                      "generator_sha256": source_hash}))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
