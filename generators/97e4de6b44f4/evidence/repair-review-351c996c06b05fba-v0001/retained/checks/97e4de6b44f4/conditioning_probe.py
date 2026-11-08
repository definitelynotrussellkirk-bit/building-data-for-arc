#!/usr/bin/env python3
"""Replay four current public-generator draws and one marker-ignoring rival.

Run from the outer packet using its Racket launcher. This intentionally small
lesson reuses the retained symmetric index-2 witness and distinguishing index-3
witness; it does not estimate an ambiguity rate or claim the catalog exporter
emitted this particular lesson.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "97e4de6b44f4"
GENERATOR_SHA256 = "d8aa37144eb8de997c1b6807d8d796138d32f25333484f1ee5e22a3338b05001"
RULE_SHA256 = "b8b121971867a341c27a8b08fd27f8cff11b79e79ff71542466232b269ea3c07"
RETAINED = (
    "generators/97e4de6b44f4/counterexamples/review-7db198064734f44c-v0001/"
    "retained/checks/audits"
)


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def replay(root):
    generator, generator_path, source_hash = load_selected_generator(TASK_ID, root=root)
    if source_hash != GENERATOR_SHA256:
        raise ValueError("Generator source changed; reassess the bounded finding before replay")
    sources = {row["program_solution"] for row in
               (json.loads(line) for line in canonical_path(root).read_text().splitlines())
               if row.get("task_id") == TASK_ID}
    if len(sources) != 1:
        raise ValueError("Expected one canonical program")
    program = sources.pop()
    if sha(program) != RULE_SHA256:
        raise ValueError("Canonical authority differs from the retained finding")
    dispatch = "(if (= marker 8) (rotate-cw shape) (flip-lr shape))"
    if program.count(dispatch) != 1:
        raise ValueError("Canonical dispatch fragment must occur exactly once")
    rival = program.replace(dispatch, "(rotate-cw shape)", 1)
    pairs = []
    runtime = root / "shared/runtime"
    with _local_imports(runtime, generator_path.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for index in range(4):
                grid = _grid(generator.generate(0, index, difficulty="easy"))
                issues = generator.self_check(grid, difficulty="easy")
                if issues:
                    raise AssertionError(issues)
                pairs.append(dict(
                    request=dict(seed=0, sample_index=index, difficulty="easy", overrides={}),
                    input=grid, output=_grid(apply(program, grid)),
                    rival_output=_grid(apply(rival, grid)), validator_issues=issues,
                ))
        finally:
            bridge.close()
    inherited = {}
    for index, filename in ((2, "97e4de6b44f4_nonrectangular_equal_transforms_0.json"),
                            (3, "97e4de6b44f4_marker_conditioning_required.json")):
        path = root / RETAINED / filename
        original = json.loads(path.read_text())
        if (original["generator_sha256"] != source_hash
                or original["rule_sha256"] != RULE_SHA256
                or original["input"] != pairs[index]["input"]
                or original["actual_racket_output"] != pairs[index]["output"]
                or original["rival_output"] != pairs[index]["rival_output"]):
            raise AssertionError("Retained witness differs from the fresh source-bound replay")
        inherited[path.relative_to(root).as_posix()] = sha(path.read_bytes())
    matches = [pair["output"] == pair["rival_output"] for pair in pairs[:3]]
    differs = pairs[3]["output"] != pairs[3]["rival_output"]
    if not all(matches) or not differs:
        raise AssertionError("Expected three-demo fit followed by a distinct lawful query")
    return dict(
        task_id=TASK_ID, status="reproduced_unresolved",
        generator_source=dict(path=generator_path.relative_to(root).as_posix(), sha256=source_hash),
        canonical_program=program, canonical_program_sha256=RULE_SHA256,
        rival_name="always_rotate_cw", rival_program=rival, rival_program_sha256=sha(rival),
        racket=identity, train=pairs[:3], test=[pairs[3]],
        rival_fits_all_demonstrations=True, rival_query_differs=True,
        declared_examples_needed=generator.EXAMPLES_NEEDED,
        inherited_evidence=inherited,
        repair_demonstration=dict(input=pairs[3]["input"], output=pairs[3]["output"]),
        recommendation="Include a marker-9 demonstration whose flip differs from rotation; retain lawful symmetric inputs as optional examples.",
        limits=[
            "Exactly four ordinary public-generator draws and one rival were executed.",
            "This assembled lesson uses seed0 indices0..3; no production exporter emission rate is claimed.",
            "The finding concerns teaching sufficiency, not incorrect reference labels.",
            "No generator repair, audit resolution, approval or training admission is performed.",
        ],
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError("Choose a fresh evidence output path")
    result = replay(find_root(__file__))
    result["probe_source_sha256"] = sha(Path(__file__).read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(dict(task_id=TASK_ID, status=result["status"], demonstrations=3,
                          queries=1, rival_fits=True, query_differs=True, output=str(args.out))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
