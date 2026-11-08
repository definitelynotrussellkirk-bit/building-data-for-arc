"""Bounded adversarial replay for the 66e63986855b reflection-extent prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK = "66e63986855b"
ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators" / TASK / "workspace" / "parametric" / "prototype.py"
EVIDENCE = ROOT.parent / "checks" / "parametric" / "reflection-extent-v1"
OUT = ROOT.parent / "checks" / "parametric" / "adversarial-report.json"


def load_prototype():
    spec = importlib.util.spec_from_file_location("reflection_extent_probe", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    started = time.monotonic()
    proto = load_prototype()
    findings: list[str] = []
    checks: dict[str, object] = {}
    report = json.loads((EVIDENCE / "report.json").read_text(encoding="utf-8"))
    episodes = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((EVIDENCE / "private" / "episodes").glob("*.json"))
    ]

    with RacketBridge(max_calls_before_restart=128) as bridge:
        rival_findings = [
            proto.parameter_rival_findings(episode, bridge=bridge, root=ROOT)
            for episode in episodes
        ]
        if any(rival_findings):
            findings.append(f"episode replay findings: {rival_findings}")
        checks["episode_racket_replay"] = {
            "episodes": len(episodes),
            "pairs": sum(len(e["train"]) + len(e["test"]) for e in episodes),
            "findings": rival_findings,
        }

        try:
            proto.materialize(EVIDENCE, bridge=bridge)
            findings.append("existing output directory was overwritten")
            existing_rejected = False
        except FileExistsError:
            existing_rejected = True
        checks["existing_output_rejected"] = existing_rejected

        with tempfile.TemporaryDirectory(prefix="reflection-extent-adversarial-") as tmp:
            duplicate = Path(tmp) / "duplicate"
            try:
                proto.materialize(
                    duplicate,
                    demos=1,
                    queries=1,
                    episode_seeds=(0, 0),
                    bridge=bridge,
                    root=ROOT,
                )
                findings.append("duplicate public payload was accepted")
                duplicate_rejected = False
            except ValueError as error:
                duplicate_rejected = "duplicate public payload" in str(error)
                if not duplicate_rejected:
                    findings.append(f"wrong duplicate rejection: {error}")
            if duplicate.exists():
                findings.append("duplicate rejection left a partial output directory")
            checks["duplicate_public_rejected_without_partial_output"] = (
                duplicate_rejected and not duplicate.exists()
            )

    programs_ok = True
    for key, record in report["programs"].items():
        path = EVIDENCE / record["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record["sha256"]:
            findings.append(f"program hash mismatch for extent {key}")
            programs_ok = False
    if (EVIDENCE / report["programs"]["2"]["path"]).read_text(
        encoding="utf-8"
    ) != proto.canonical_program(ROOT):
        findings.append("extent 2 is not byte-exact canonical")
        programs_ok = False
    checks["program_hashes_and_canonical_default"] = programs_ok

    forbidden = (
        "reflection_extent",
        "parameters",
        "seed",
        "program",
        "rival",
        "samples",
    )
    public_records = []
    public_ok = True
    episode_by_id = {public_challenge_id(e): e for e in episodes}
    for path in sorted((EVIDENCE / "public").glob("*.json")):
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        public = json.loads(payload)
        leaked = [term for term in forbidden if term in payload.decode("utf-8")]
        record = {
            "path": str(path.relative_to(ROOT.parent)),
            "sha256": digest,
            "filename_matches_visible_sha256": path.stem == digest,
            "hidden_terms": leaked,
            "queries": len(public.get("test", [])),
            "query_outputs_present": any("output" in pair for pair in public.get("test", [])),
        }
        public_records.append(record)
        if (
            path.stem != digest
            or leaked
            or record["query_outputs_present"]
            or path.stem not in episode_by_id
            or payload != public_challenge_bytes(episode_by_id[path.stem])
        ):
            public_ok = False
            findings.append(f"public projection failure: {record}")
    mutated = deepcopy(episodes[0])
    original_id = public_challenge_id(mutated)
    mutated["seed"] = 999999
    mutated["parameters"]["reflection_extent"] = 1
    mutated["test"][0]["output"] = [[9]]
    private_invariant = public_challenge_id(mutated) == original_id
    if not private_invariant:
        findings.append("public ID changed with private metadata/query answer")
        public_ok = False
    checks["public_projection"] = {
        "ok": public_ok,
        "records": public_records,
        "private_metadata_and_query_answer_invariant": private_invariant,
    }

    scalar_rejections = {}
    for label, call in {
        "bool_extent": lambda: proto.validate_extent(True),
        "string_extent": lambda: proto.validate_extent("2"),
        "bool_demo_count": lambda: proto.validate_counts(True, 4),
        "zero_query_count": lambda: proto.validate_counts(3, 0),
    }.items():
        try:
            call()
            scalar_rejections[label] = False
            findings.append(f"invalid scalar accepted: {label}")
        except ValueError:
            scalar_rejections[label] = True
    checks["invalid_scalar_rejections"] = scalar_rejections

    result = {
        "schema": "arc-reflection-extent-adversarial-v1",
        "task_id": TASK,
        "prototype_sha256": hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest(),
        "evidence_report_sha256": hashlib.sha256((EVIDENCE / "report.json").read_bytes()).hexdigest(),
        "surfaces": [
            "parameter/Racket parity and lesson certificate",
            "public/private export and rejection paths",
        ],
        "checks": checks,
        "findings": findings,
        "status": "no_measured_failure" if not findings else "fail",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": [
            "Bounded replay of the two retained episodes and declared alternate setting.",
            "Privacy scan covers serialized public files and named hidden fields, not arbitrary side channels.",
        ],
    }
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "findings": findings, "elapsed_seconds": result["elapsed_seconds"]}, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
