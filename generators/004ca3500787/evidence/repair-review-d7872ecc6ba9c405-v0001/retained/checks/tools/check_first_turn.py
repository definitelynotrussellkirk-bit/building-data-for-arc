#!/usr/bin/env python3
"""Check native single-query exports and first-turn private-field invariance.

Run from this packet through::

    python3 review.py run --receipt checks/first-turn/command.json \
      python3 ../checks/tools/check_first_turn.py \
      --bundle ../checks/TASK/preview --out ../checks/first-turn/report.json

Repeat --bundle to inspect multiple bundles. This uses the packet's existing
preview_public.py implementation and actual source-bound exported episodes.
V2 bundles follow the verified shuffled source_indices; legacy v1 bundles
retain source order. First-turn mutations use the first presented query.
It checks serialization only: no Racket execution, semantic label validation,
controller implementation, owner acceptance, or training admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


WORK = Path(__file__).resolve().parents[2]
LIMITATIONS = (
    "Python serialization and finite private-field mutation checks on the "
    "listed native-qualified exports only. The native verifier checks current "
    "source binding but does not authenticate editable receipts. No new "
    "Racket execution, label-correctness proof, controller, owner acceptance, "
    "or training admission. Reveal one public file at a time; retain bundle "
    "listings and private files with the controller."
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def display_path(path: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(WORK).as_posix()
    except ValueError:
        return str(path)


def file_binding(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": display_path(path), "sha256": sha(raw), "bytes": len(raw)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_native():
    helper = WORK / "preview_public.py"
    spec = importlib.util.spec_from_file_location("_first_turn_native_preview", helper)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def first_turn_variants(episode):
    """Change only information that must be hidden from the first model turn."""
    yield "single_query_only", {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][0]["input"])}],
    }

    metadata = deepcopy(episode)
    for name in tuple(metadata):
        if name not in ("train", "test"):
            metadata[name] = {"private_mutation": name}
    metadata["additional_private_metadata"] = {"seed": -1, "program": "not a program"}
    for split in ("train", "test"):
        for index, pair in enumerate(metadata[split]):
            pair["additional_private_metadata"] = {"split": split, "index": index}
    yield "private_metadata_rewritten", metadata

    answers = deepcopy(episode)
    for index, pair in enumerate(answers["test"]):
        # Deliberately not a grid: hidden answers must never be inspected.
        pair["output"] = {"private_answer_mutation": index}
    yield "query_answers_rewritten", answers

    absent_answers = deepcopy(episode)
    for pair in absent_answers["test"]:
        pair.pop("output", None)
    yield "query_answers_removed", absent_answers

    future = deepcopy(episode)
    future["test"] = [future["test"][0], {"private_future_query": True},
                      {"input": "not a visible grid", "output": None}, {}]
    yield "future_queries_replaced", future

    order = deepcopy(episode)
    order["test"] = [order["test"][0], *reversed(order["test"][1:]),
                     {"input": [[9]], "output": [[8]], "private_extra_query": True}]
    yield "future_queries_reordered_and_extended", order


def inspect_bundle(native, bundle: Path) -> dict:
    bundle = bundle.resolve()
    verified = native.verify_export(bundle)
    private = bundle / "private"
    qualification_path = private / "qualification.json"
    execution_path = private / "execution.json"
    manifest_path = private / "manifest.json"
    private_paths = [qualification_path, execution_path, manifest_path]
    before = [file_binding(path) for path in private_paths]
    qualification = json.loads(qualification_path.read_bytes())
    execution = json.loads(execution_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    require(manifest["schema"] in (native.SCHEMA, native.LEGACY_SCHEMA),
            "Unsupported native projection schema")
    cases, public_count = [], 0
    manifest_episodes = {item["episode_index"]: item for item in manifest["episodes"]}
    for episode_index, episode in enumerate(execution["episodes"]):
        mapping = manifest_episodes[episode_index]
        identifiers = mapping["view_ids"]
        require(len(identifiers) == len(episode["test"]), "Query count differs from manifest")
        source_indices = (mapping.get("source_indices") if manifest["schema"] == native.SCHEMA
                          else list(range(len(episode["test"]))))
        require(type(source_indices) is list
                and all(type(index) is int for index in source_indices)
                and sorted(source_indices) == list(range(len(episode["test"]))),
                "Manifest source_indices must be a complete integer permutation")
        if manifest["schema"] == native.SCHEMA:
            require(source_indices == native.query_order(len(episode["test"]),
                    episode["seed"] + manifest["presentation_seed"]),
                    "Manifest source_indices differ from native presentation order")
        first_bytes = None
        for position, query_index in enumerate(source_indices):
            query = episode["test"][query_index]
            visible = native.public_view_bytes(episode, query_index)
            identifier = sha(visible)
            expected = {
                "train": [{"input": pair["input"], "output": pair["output"]}
                          for pair in episode["train"]],
                "test": [{"input": query["input"]}],
            }
            require(json.loads(visible) == expected, "Public schema or visible values differ")
            independent_bytes = (json.dumps(expected, sort_keys=True, separators=(",", ":"),
                                             ensure_ascii=False) + "\n").encode("utf-8")
            require(visible == independent_bytes, "Public bytes differ from strict visible serialization")
            require(identifier == identifiers[position], "Query public ID differs from manifest")
            require((bundle / "public" / f"{identifier}.json").read_bytes() == visible,
                    "Saved public file differs from native visible bytes")
            public_count += 1
            if position == 0:
                first_bytes = visible
        presented = deepcopy(episode)
        presented["test"] = [deepcopy(episode["test"][index]) for index in source_indices]
        mutations = []
        for name, variant in first_turn_variants(presented):
            require(native.public_view_bytes(variant, 0) == first_bytes,
                    f"First-turn visibility changed for episode {episode_index}: {name}")
            mutations.append(name)
        # Positive control: changing a genuinely visible query cell must change bytes.
        visible_change = deepcopy(presented)
        cell = visible_change["test"][0]["input"][0][0]
        visible_change["test"][0]["input"][0][0] = (cell + 1) % 10
        require(native.public_view_bytes(visible_change, 0) != first_bytes,
                "Positive control failed: visible query-cell change was ignored")
        cases.append({
            "episode_index": episode_index,
            "seed": episode["seed"],
            "settings": episode["settings"],
            "demos": len(episode["train"]),
            "queries": len(episode["test"]),
            "source_indices": source_indices,
            "first_source_query_index": source_indices[0],
            "first_view_sha256": sha(first_bytes),
            "first_view_bytes": len(first_bytes),
            "invariance_checks": mutations,
            "visible_change_positive_control": "passed",
        })
    require([file_binding(path) for path in private_paths] == before,
            "Private qualification evidence changed during inspection")
    return {
        "bundle": display_path(bundle),
        "task_id": qualification["task_id"],
        "projection_schema": manifest["schema"],
        "presentation_seed": manifest.get("presentation_seed"),
        "native_verification": verified,
        "private_evidence": before,
        "public_views_checked": public_count,
        "first_turns_checked": len(cases),
        "invariance_checks": sum(len(case["invariance_checks"]) for case in cases),
        "positive_controls": len(cases),
        "cases": cases,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        parser.error("Choose a new report path; existing evidence is not overwritten")
    sources = [Path(__file__), WORK / "preview_public.py",
               WORK / "repo/shared/runtime/reviewer_support.py",
               WORK / "repo/src/arcpuzzles/query_presentation.py"]
    bindings = [file_binding(path) for path in sources]
    report = {
        "schema": "arcpuzzles-first-turn-visibility-check-v1",
        "status": "failed", "source_files": bindings, "bundles": [], "failures": [],
        "racket_replayed": False, "owner_acceptance": "not_performed",
        "training_admitted": False, "limitations": LIMITATIONS,
    }
    try:
        native = load_native()
        for bundle in args.bundle:
            report["bundles"].append(inspect_bundle(native, bundle))
        require([file_binding(path) for path in sources] == bindings,
                "Checker or native serializer source changed during execution")
        report["status"] = "passed"
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        report["failures"].append(f"{type(error).__name__}: {error}")
    for key in ("public_views_checked", "first_turns_checked", "invariance_checks", "positive_controls"):
        report[key] = sum(bundle[key] for bundle in report["bundles"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in
                     ("status", "public_views_checked", "first_turns_checked", "invariance_checks",
                      "positive_controls", "failures")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
