"""Transfer current generator identities and retained public episodes to a bank."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .catalog import Catalog
from .review_full_packet import canonical_json
from .review_solve import instance_hash


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_question_sources(catalog: Catalog, out: Path) -> dict:
    out = out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Use a new source-bundle directory")
    registry, questions, exclusions = {}, {}, []
    for row in catalog.query():
        if not row.get("generator_sha256"):
            continue
        registry[row["generator_sha256"]] = {"generator_hash": row["generator_sha256"], "generator_id": row["id"],
            "kind": row["kind"], "version": row.get("version"), "rule_hash": row.get("rule_hash"),
            "approved": row["approved"], "train_safety": row["train_safety"],
            "family": row.get("family"), "source_split": row.get("split"), "current_source": True}
    for public_path in sorted((catalog.root / "var/datasets").rglob("public.jsonl")):
        directory = public_path.parent
        try:
            staged_registry, staged_questions = {}, {}
            manifest_path = directory / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            files = manifest["files"]
            for name in ("public.jsonl", "labels.private.jsonl"):
                if _hash(directory / name) != files[name]["sha256"]:
                    raise ValueError("Export projection hash mismatch")
            labels = {r["episode_id"]: r for r in
                      (json.loads(s) for s in (directory / "labels.private.jsonl").read_text().splitlines())}
            for line in public_path.read_text().splitlines():
                row = json.loads(line)
                private = labels[row["episode_id"]]
                provenance = private.get("provenance", {})
                ghash = provenance.get("generator_sha256")
                if not ghash:
                    raise ValueError("Episode lacks a generator source hash")
                public = {"train": row["train"], "test": [{"input": p["input"]} for p in row["test"]]}
                ihash = instance_hash(public)
                # Hash private labels separately; never place their grids in the source bundle.
                labels_hash = hashlib.sha256(canonical_json({"test_outputs": private["test_outputs"]})).hexdigest()
                key = (ghash, ihash)
                prior = staged_questions.get(key, questions.get(key))
                if prior and prior["private_labels_sha256"] != labels_hash:
                    raise ValueError("Same public episode has conflicting labels")
                staged_registry.setdefault(ghash, {"generator_hash": ghash, "generator_id": private.get("task_id"),
                    "kind": "historical_export", "current_source": False, "provenance": provenance})
                question = {"generator_hash": ghash, "instance_hash": ihash, "generator_id": private.get("task_id"),
                    "source_kind": "retained_generated_export", "source_split": provenance.get("split"),
                    "public": public, "private_labels_sha256": labels_hash, "provenance": provenance,
                    "source_export_sha256": _hash(manifest_path), "source_status": manifest.get("status"),
                    "source_episode_ids": [row["episode_id"]], "training_admitted": False}
                if key in staged_questions:
                    staged_questions[key]["source_episode_ids"].append(row["episode_id"])
                else:
                    staged_questions[key] = question
            # Only commit a fully validated export, never its successful prefix.
            for ghash, generator in staged_registry.items():
                registry.setdefault(ghash, generator)
            for key, question in staged_questions.items():
                if key in questions:
                    questions[key]["source_episode_ids"].extend(question["source_episode_ids"])
                else:
                    questions[key] = question
        except (OSError, ValueError, KeyError, TypeError) as exc:
            exclusions.append({"source_export": str(directory.relative_to(catalog.root)), "reason": str(exc)})
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("generators", [registry[k] for k in sorted(registry)]),
                       ("questions", [questions[k] for k in sorted(questions)]), ("exclusions", exclusions)):
        (out / (name + ".jsonl")).write_bytes(b"".join(canonical_json(r) + b"\n" for r in rows))
    manifest = {"schema": "arc-question-source-bundle-v1", "counts": {"generators": len(registry),
        "questions": len(questions), "excluded_exports": len(exclusions)},
        "files": {p.name: _hash(p) for p in out.iterdir() if p.is_file()}, "training_admitted": False}
    (out / "manifest.json").write_bytes(canonical_json(manifest) + b"\n")
    return manifest
