"""Compact source-bound verification for review-b74787e066759306."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, public_challenge_id

TASK_ID = "97dd5f3c96b9"
EXPECTED_GENERATOR_SHA256 = "8626cabe946ae140676985a8fae154be1dff2e910cc89b8ebce7b62ed6d9be31"
EXPECTED_RULE_HASH = "8d1d1f690046"
SETTINGS = {"pair_color", "fixed_8", "fixed_9"}
FORBIDDEN_PUBLIC_TOKENS = (
    "connector_color",
    "pair_color",
    "fixed_8",
    "fixed_9",
    "program_solution",
    "query_answers",
    '"seed"',
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_program(repo: Path) -> str:
    programs = set()
    with canonical_path(repo).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


def main() -> int:
    repo = Path.cwd().resolve()
    if not (repo / "generators" / TASK_ID).is_dir():
        raise RuntimeError("run from WORK/repo")
    work = repo.parent
    home = repo / "generators" / TASK_ID
    evidence = work / "checks/parametric/connector-color-v1"

    generator = home / "generator.py"
    if sha256(generator.read_bytes()) != EXPECTED_GENERATOR_SHA256:
        raise AssertionError("production generator drift")
    source_text = generator.read_text(encoding="utf-8")
    if f'RULE_HASH = "{EXPECTED_RULE_HASH}"' not in source_text:
        raise AssertionError("production rule hash drift")

    manifest = load_json(evidence / "manifest.json")
    expected_sources = {
        f"generators/{TASK_ID}/generator.py": EXPECTED_GENERATOR_SHA256,
        f"generators/{TASK_ID}/workspace/parametric/prototype.py": sha256(
            (home / "workspace/parametric/prototype.py").read_bytes()
        ),
        f"generators/{TASK_ID}/workspace/parametric/adapter.py": sha256(
            (home / "workspace/parametric/adapter.py").read_bytes()
        ),
        f"generators/{TASK_ID}/workspace/parametric/promotion.json": sha256(
            (home / "workspace/parametric/promotion.json").read_bytes()
        ),
    }
    if manifest["source_hashes"] != expected_sources:
        raise AssertionError("manifest source hashes do not match current selected files")
    if manifest["status"] != "proposed task-local prototype; not production-approved":
        raise AssertionError("prototype status drift")
    if manifest["counts"] != {"demos": 2, "queries": 4}:
        raise AssertionError("ordinary evidence count drift")
    if manifest["racket"].get("backend") != "racket" or manifest["racket"].get("protected") is not True:
        raise AssertionError("ordinary evidence is not protected Racket")

    canonical = canonical_program(repo)
    if (evidence / "rules/pair_color.rkt").read_text(encoding="utf-8") != canonical:
        raise AssertionError("pair_color rule is not exact canonical source")

    seen_settings = set()
    seen_public_ids = set()
    total_racket_evaluations = 0
    for receipt in manifest["episodes"]:
        public_id = receipt["public_id"]
        public_path = evidence / "public" / f"challenge-{public_id}.json"
        private_path = evidence / "private" / f"challenge-{public_id}.json"
        raw = public_path.read_bytes()
        public = json.loads(raw)
        private = load_json(private_path)
        if public_id != sha256(raw) or public_id != public_challenge_id(public):
            raise AssertionError(f"public identity mismatch: {public_id}")
        public_text = raw.decode("utf-8")
        if any(token in public_text for token in FORBIDDEN_PUBLIC_TOKENS):
            raise AssertionError(f"hidden metadata leaked into public challenge: {public_id}")
        if len(public["train"]) != 2 or len(public["test"]) != 4:
            raise AssertionError(f"public count mismatch: {public_id}")
        if any(set(pair) != {"input", "output"} for pair in public["train"]):
            raise AssertionError(f"malformed demonstration projection: {public_id}")
        if any(set(pair) != {"input"} for pair in public["test"]):
            raise AssertionError(f"query answers leaked: {public_id}")
        if private["public_id"] != public_id or private["public_sha256"] != public_id:
            raise AssertionError(f"private/public binding mismatch: {public_id}")
        chosen = private["settings"]["connector_color"]
        seen_settings.add(chosen)
        seen_public_ids.add(public_id)
        if private["runtime_identity"].get("protected") is not True:
            raise AssertionError(f"private receipt is not protected: {public_id}")
        survivors = [
            setting
            for setting, row in private["rival_checks"].items()
            if row["matches_all_demonstrations"]
        ]
        if survivors != [chosen]:
            raise AssertionError(f"finite survivor mismatch: {public_id}: {survivors}")
        for setting, row in private["rival_checks"].items():
            if setting != chosen and row["query_disagreement_indices"] != [0, 1, 2, 3]:
                raise AssertionError(f"query distinction mismatch: {public_id}: {setting}")
        total_racket_evaluations += private["label_execution"]["evaluation_count"]

    if seen_settings != SETTINGS or len(seen_public_ids) != 3:
        raise AssertionError("ordinary evidence does not cover each setting exactly once")
    if total_racket_evaluations != 54:
        raise AssertionError(f"unexpected retained evidence evaluation count: {total_racket_evaluations}")

    promotion = load_json(home / "workspace/parametric/promotion.json")
    if promotion["parameters"] != {"connector_color": ["pair_color", "fixed_8", "fixed_9"]}:
        raise AssertionError("promotion parameter contract drift")
    if promotion["limits"] != {"demos": [1, 16], "queries": [1, 16]}:
        raise AssertionError("promotion count limits drift")
    if (work / "AUDIT.md").exists():
        raise AssertionError("AUDIT.md must be absent because neither ticket is a finding")

    for ticket_id in ("ticket-c7cbd8cc64818db2", "ticket-c95e020b1688bb0e"):
        root = work / "checks/tickets" / ticket_id
        result = load_json(root / "result.json")
        probe = load_json(root / "probe.json")
        if result["status"] != "completed" or result["source_binding"]["source_sha256"] != probe["source_sha256"]:
            raise AssertionError(f"ticket result/source mismatch: {ticket_id}")

    print(json.dumps({
        "status": "pass",
        "production_generator_sha256": EXPECTED_GENERATOR_SHA256,
        "prototype_source_hashes": expected_sources,
        "public_challenges": len(seen_public_ids),
        "settings": sorted(seen_settings),
        "retained_protected_racket_evaluations": total_racket_evaluations,
        "supplementary_tickets": 2,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
