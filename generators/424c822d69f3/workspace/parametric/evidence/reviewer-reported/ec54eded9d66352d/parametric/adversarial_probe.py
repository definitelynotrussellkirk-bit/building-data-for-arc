#!/usr/bin/env python3
"""Bounded adversarial probe for the selected parametric prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    here = Path(__file__).resolve()
    root = find_root(here)
    task = root / "generators/424c822d69f3"
    prototype_path = task / "workspace/parametric/prototype.py"
    verifier_path = task / "workspace/parametric/verify_evidence.py"
    prototype = load_module("adversarial_parametric_prototype", prototype_path)
    verifier = load_module("adversarial_parametric_verifier", verifier_path)
    generator, generator_path, generator_sha = load_selected_generator(prototype.TASK_ID, root=root)

    boundary_rows = []
    with RacketBridge() as bridge:
        for seed, demo_count, query_count in ((2, 1, 8), (3, 8, 1)):
            episode = prototype.make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
                bridge=bridge,
            )
            mode = episode["parameters"]["selection_mode"]
            opposite = next(value for value in prototype.ALLOWED_SELECTION_MODES if value != mode)
            selected_rule = prototype.materialize_rule(mode, root=root)
            opposite_rule = prototype.materialize_rule(opposite, root=root)
            pairs = episode["train"] + episode["test"]
            selected_matches = sum(
                prototype.execute_rule(selected_rule, pair["input"], bridge=bridge) == pair["output"]
                for pair in pairs
            )
            opposite_changes = sum(
                prototype.execute_rule(opposite_rule, pair["input"], bridge=bridge) != pair["output"]
                for pair in pairs
            )
            boundary_rows.append({
                "seed": seed,
                "selection_mode": mode,
                "demonstrations": demo_count,
                "queries": query_count,
                "distinct_inputs": len({
                    json.dumps(pair["input"], separators=(",", ":")) for pair in pairs
                }),
                "selected_racket_matches": selected_matches,
                "opposite_racket_changes": opposite_changes,
                "candidate_indices": [
                    row["candidate_index"] for row in episode["input_provenance"]
                ],
                "ambiguities": len(episode["ambiguities"]),
            })

    base_episode = prototype.make_episode(0, root=root)
    accepted = {row["candidate_index"] for row in base_episode["input_provenance"]}
    max_accepted = max(accepted)
    skipped = []
    for attempt in range(max_accepted + 1):
        if attempt in accepted:
            continue
        candidate = generator.generate(prototype._candidate_seed(0, attempt), attempt)
        try:
            prototype.extremum_facts(candidate)
        except ValueError as error:
            skipped.append({"candidate_index": attempt, "rejection": str(error)})
        else:
            skipped.append({"candidate_index": attempt, "rejection": "not-an-extremum-rejection"})

    rejection_rows = []
    for name, action in (
        ("boolean_demo_count", lambda: prototype.make_episode(0, demo_count=True, root=root)),
        (
            "canonical_source_drift",
            lambda: prototype.materialize_rule(
                "nearest", source=prototype.canonical_source(root=root) + "\n"
            ),
        ),
        (
            "duplicate_public_payload",
            lambda: prototype._public_records([base_episode, copy.deepcopy(base_episode)]),
        ),
    ):
        try:
            action()
        except ValueError as error:
            rejection_rows.append({"case": name, "error_type": "ValueError", "message": str(error)})
        else:
            raise AssertionError(f"expected rejection for {name}")

    evidence = here.parent / "nearest-farthest-v1"
    retained_verification = verifier.verify_evidence(evidence, root=root)
    with tempfile.TemporaryDirectory(prefix="424c822d69f3-adversarial-") as temporary:
        tampered = Path(temporary) / "evidence"
        shutil.copytree(evidence, tampered)
        report = json.loads((tampered / "report.json").read_text(encoding="utf-8"))
        public_path = tampered / report["episodes"][0]["public_path"]
        public = json.loads(public_path.read_text(encoding="utf-8"))
        public["test"][0]["input"][0][0] = (public["test"][0]["input"][0][0] + 1) % 10
        public_path.write_text(
            json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        manifest_path = tampered / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        relative = public_path.relative_to(tampered).as_posix()
        for row in manifest["files"]:
            if row["path"] == relative:
                row["sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
                break
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            verifier.verify_evidence(tampered, root=root)
        except ValueError as error:
            tamper_rejection = {"error_type": "ValueError", "message": str(error)}
        else:
            raise AssertionError("hash-valid changed public file was accepted")

    private_only = copy.deepcopy(base_episode)
    private_only["test"][0]["output"] = [[9]]
    private_only["seed"] = 1000
    private_id_invariant = (
        prototype.public_id(base_episode) == prototype.public_id(private_only)
        and prototype.public_bytes(base_episode) == prototype.public_bytes(private_only)
    )
    if not private_id_invariant:
        raise AssertionError("private-only changes altered public identity")

    result = {
        "schema": "424c822d69f3-parametric-adversarial-v1",
        "status": "bounded_no_finding",
        "prototype_version": prototype.VERSION,
        "source_bindings": {
            "prototype_sha256": hashlib.sha256(prototype_path.read_bytes()).hexdigest(),
            "verifier_sha256": hashlib.sha256(verifier_path.read_bytes()).hexdigest(),
            "generator_path": str(generator_path.relative_to(root)),
            "generator_sha256": generator_sha,
            "nearest_rule_sha256": hashlib.sha256(
                prototype.materialize_rule("nearest", root=root).encode()
            ).hexdigest(),
            "farthest_rule_sha256": hashlib.sha256(
                prototype.materialize_rule("farthest", root=root).encode()
            ).hexdigest(),
        },
        "count_boundaries": boundary_rows,
        "tie_filter": {
            "accepted_candidate_indices": sorted(accepted),
            "skipped_before_last_accept": skipped,
        },
        "rejection_paths": rejection_rows,
        "retained_verification": retained_verification,
        "hash_valid_public_tamper_rejection": tamper_rejection,
        "private_only_changes_preserve_public_identity": private_id_invariant,
        "limitations": [
            "Count-boundary replay covers paired seeds 2 and 3, not all seeds.",
            "The verifier attack mutates one public query cell and does not enumerate all corruption classes.",
            "Rival coverage is limited to the two declared nearest/farthest settings.",
        ],
    }
    output = here.parent / "adversarial.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "boundary_cases": len(boundary_rows),
        "skipped_ties": len(skipped),
        "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
