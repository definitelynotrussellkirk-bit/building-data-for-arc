"""Fresh public-only reviewer solves, with retained revisions and private scoring.

The no-reference rule is an explicit reviewer obligation, not a filesystem sandbox.
Earlier exposure and any reference consultation are recorded at finish time.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

from .catalog import Catalog
from .grids import format_task
from .review_full_packet import canonical_json
from .runtime import run_process


SCHEMA = "arcpuzzles-reviewer-solve-v1"
POLICY = "visible_examples_only_no_reference_consultation"
ATTEMPT_INTENTS = ("solve", "teaching_negative", "diagnostic_probe", "unknown")
BLIND_SCHEMA = "arcpuzzles-blind-solve-assignment-v1"
# The post-repair solve keeps its historical paths; a blind solve of a different,
# untouched task lives beside it so the two records can never be confused.
KINDS = {
    "post_repair": {"folder": "solve", "private": ".review/solve-private",
                    "contract": "ASSIGNMENT.json", "purpose": "fresh-reviewer-solve-v1"},
    "blind": {"folder": "solve-blind", "private": ".review/solve-private-blind",
              "contract": "BLIND_ASSIGNMENT.json", "purpose": "blind-reviewer-solve-v1"},
}


def _kind(kind: str) -> dict:
    if kind not in KINDS:
        raise ValueError(f"Unknown solve kind: {kind}")
    return KINDS[kind]
NOTES = """# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.
"""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def instance_hash(public: dict) -> str:
    return digest(canonical_json({"schema": "arc-public-episode-hash-v1",
                                  "train": public["train"], "test": public["test"]}))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value) + b"\n")


def _regular(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing regular solve artifact: {path.name}")
    return path.read_bytes()


def _demonstration_count(source: bytes) -> int:
    """Read the literal teaching minimum without importing reviewer code."""
    count = 3
    for statement in ast.parse(source).body:
        targets = (statement.targets if isinstance(statement, ast.Assign) else
                   [statement.target] if isinstance(statement, ast.AnnAssign) else [])
        if any(isinstance(target, ast.Name) and target.id == "EXAMPLES_NEEDED"
               for target in targets):
            value = ast.literal_eval(statement.value)
            if type(value) is not int or not 1 <= value <= 32:
                raise ValueError("EXAMPLES_NEEDED must be a literal integer in 1..32")
            count = max(3, value)
    return count


def _summary(root: Path, kind: str = "post_repair") -> dict:
    return json.loads(_regular(root / _kind(kind)["folder"] / "summary.json"))


def _frozen(root: Path, kind: str = "post_repair") -> tuple[dict, dict]:
    paths = _kind(kind)
    folder = paths["folder"]
    summary = _summary(root, kind)
    contract = json.loads(_regular(root / paths["contract"]))
    if summary["assignment_id"] != contract["assignment_id"] or summary["packet_id"] != contract["packet_id"]:
        raise ValueError("Solve assignment changed")
    source = root / "repo" / contract["generator"]["generator"]
    canonical = root / "repo/shared/data/canonical/puzzles.jsonl"
    if (digest(_regular(source)) != summary["generator_hash"]
            or digest(_regular(canonical)) != summary["canonical_sha256"]):
        raise ValueError("Generator or reference source changed after solve preparation")
    challenge_raw = _regular(root / folder / "challenge.json")
    challenge = json.loads(challenge_raw)
    if (digest(challenge_raw) != summary["challenge_sha256"]
            or instance_hash(challenge) != summary["instance_hash"]):
        raise ValueError("Public solve challenge changed")
    labels = json.loads(_regular(root / paths["private"] / "labels.json"))
    if digest(canonical_json(labels)) != summary["private_labels_sha256"]:
        raise ValueError("Private solve labels changed")
    return summary, {"public": challenge, "test_outputs": labels["test_outputs"]}


def prepare_solve(packet_root: Path, kind: str = "post_repair") -> dict:
    paths = _kind(kind)
    root = packet_root.resolve()
    summary_path = root / paths["folder"] / "summary.json"
    if summary_path.is_file() and _summary(root, kind)["status"] != "blocked":
        summary, _ = _frozen(root, kind)
        return summary
    if kind == "blind" and not (root / paths["contract"]).is_file():
        raise ValueError("This packet has no blind solve assignment; run assignment.py first")
    contract = json.loads(_regular(root / paths["contract"]))
    if kind == "blind" and contract.get("schema") != BLIND_SCHEMA:
        raise ValueError("This packet has no blind solve assignment")
    source = root / "repo" / contract["generator"]["generator"]
    source_bytes = _regular(source)
    generator_hash = digest(source_bytes)
    seed = int(digest(canonical_json({"assignment": contract["assignment_id"],
                   "generator_hash": generator_hash, "purpose": paths["purpose"]}))[:8], 16)
    config = {"n_train": 3, "n_test": 2, "difficulty": "medium"}
    base = {"schema": SCHEMA, "assignment_id": contract["assignment_id"],
            "packet_id": contract["packet_id"], "task_id": contract["task_id"],
            "generator_hash": generator_hash, "seed": seed, "config": config,
            "canonical_sha256": digest(_regular(root / "repo/shared/data/canonical/puzzles.jsonl")),
            "source_kind": "reviewer_authored", "solve_policy": POLICY,
            "feedback_policy": "visible_only",
            "reference_consulted_during_solve": None, "earlier_rule_exposure": "unknown",
            "attempt_count": 0, "training_admitted": False}
    if kind == "blind":
        base["solve_kind"] = "blind_before_repair"
    folder = root / paths["folder"]
    prefix = "python3 solve_episode.py" + (" blind" if kind == "blind" else "")
    manifest_path = root / "PACKET-MANIFEST.json"
    if manifest_path.is_file() and (root.parent / "review.py").is_file():
        layout = json.loads(_regular(manifest_path)).get("layout", {})
        if layout.get("workspace") == "WORK":
            prefix = "python3 review.py " + ("blind" if kind == "blind" else "solve")
    exposure_example = "no" if kind == "blind" else "yes"
    folder.mkdir(parents=True, exist_ok=True)
    if not (folder / "SOLVE_NOTES.md").exists():
        (folder / "SOLVE_NOTES.md").write_text(NOTES)
    (folder / "README.md").write_text(
        "# Solve from the examples\n\nDO NOT consult the Racket rule during this solve.\n"
        "Also keep generator source, reference solutions, private labels, and prior solution notes closed.\n"
        "The visible examples below are derived from challenge.json, with dimensions before every grid.\n"
        "Use only these examples and your own Python experiments. Earlier rule exposure must be recorded.\n\n"
        "Write solution.py with solve(grid), record your work in SOLVE_NOTES.md, then from the packet root run:\n\n"
        f"```sh\n{prefix} check --intent solve --note 'Hypothesis and why I tested this revision'\n"
        f"{prefix} finish --earlier-exposure {exposure_example} --reference-consulted no --reason 'Why I stopped'\n```\n\n"
        "Every check freezes your code and work log. Feedback covers visible examples and execution only.\n"
        "Private query correctness is withheld and independently checked after return.\n"
        + ("If blind generation is blocked, retain that result; do not edit this untouched generator.\n"
         if kind == "blind" else "If generation is blocked, fix the generator first and rerun prepare; failures remain recorded.\n"))
    try:
        config["n_train"] = _demonstration_count(source_bytes)
        episode = Catalog(root / "repo").generate(contract["task_id"], count=1, seed=seed,
                    allow_unapproved=True, **config)[0]
        if episode["provenance"]["generator_sha256"] != generator_hash:
            raise ValueError("Generated episode source changed")
        public = {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                             for p in episode["train"]],
                  "test": [{"input": deepcopy(p["input"])} for p in episode["test"]]}
        _validate_public(public)
        labels = {"test_outputs": [p["output"] for p in episode["test"]]}
        private = root / paths["private"]
        private.mkdir(parents=True, exist_ok=True)
        _write(private / "labels.json", labels)
        (private / "generator.py").write_bytes(source_bytes)
        (folder / "challenge.json").write_bytes(canonical_json(public) + b"\n")
        with (folder / "README.md").open("a", encoding="utf-8") as handle:
            handle.write("\n## Visible examples\n\n```text\n" + format_task(public) + "```\n")
        if not (folder / "solution.py").exists():
            (folder / "solution.py").write_text("def solve(grid):\n    # Infer the transformation from challenge.json.\n    raise NotImplementedError\n")
        base.update({"status": "prepared", "instance_hash": instance_hash(public),
                     "lesson_identifiability_checked": False,
                     "challenge_sha256": digest((folder / "challenge.json").read_bytes()),
                     "private_labels_sha256": digest(canonical_json(labels)),
                     "generation_provenance": episode["provenance"]})
    except Exception as exc:
        # Worker errors can quote the private rule. Retain them privately and expose only type/status.
        failures = folder / "prepare-failures"
        failures.mkdir(exist_ok=True)
        number = len(list(failures.glob("*.json"))) + 1
        base.update({"status": "blocked", "stopping_reason": "Episode generation blocked: " + type(exc).__name__})
        _write(failures / f"{number:04d}.json", base)
        private = root / paths["private"]
        private.mkdir(parents=True, exist_ok=True)
        _write(private / f"generation-error-{number:04d}.json", {"error": str(exc), "type": type(exc).__name__})
    _write(summary_path, base)
    return base


def evaluate_program(source: bytes, public: dict, test_outputs: list, *, timeout: float = 30) -> tuple[dict, dict]:
    """Give the Python worker public inputs only; compare its predictions in the controller."""
    with tempfile.TemporaryDirectory(prefix="arc-review-solve-") as directory:
        stage = Path(directory)
        (stage / "solution.py").write_bytes(source)
        _write(stage / "inputs.json", {"inputs": [p["input"] for p in public["train"] + public["test"]]})
        worker = Path(__file__).with_name("review_solve_worker.py")
        run = run_process([sys.executable, "-I", str(worker), str(stage)], stage, timeout=timeout)
        predictions = json.loads((stage / "predictions.json").read_text()) if (
            not run["timed_out"] and run["exit_code"] == 0 and (stage / "predictions.json").is_file()) else None
    expected = [p["output"] for p in public["train"]] + test_outputs
    visible_n = len(public["train"])
    valid = isinstance(predictions, list) and len(predictions) == len(expected)
    if not valid:
        predictions = None
    matches = [valid and _is_grid(got) and got == want for got, want in
               zip(predictions or [None] * len(expected), expected)]
    score = {"execution_status": "timeout" if run["timed_out"] else "error" if not valid else "completed",
             "visible_passed": sum(matches[:visible_n]), "visible_total": visible_n,
             "query_passed": sum(matches[visible_n:]), "query_total": len(test_outputs),
             "private_exact": bool(valid and all(matches)),
             "reported_label": "good" if valid and all(matches) else "bad"}
    return score, {key: run[key] for key in ("exit_code", "timed_out", "stdout", "stderr")}


def check_solve(packet_root: Path, solution: Path | None = None, *, note: str, timeout: float = 30,
                intent: str = "solve", kind: str = "post_repair") -> dict:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if not note.strip():
        raise ValueError("Record a hypothesis/revision note before checking")
    if intent not in ATTEMPT_INTENTS:
        raise ValueError("Unknown attempt intent")
    paths = _kind(kind)
    root = packet_root.resolve()
    summary, episode = _frozen(root, kind)
    if summary["status"] == "finished":
        raise ValueError("Solve is finished; retained attempts cannot be replaced")
    folder = root / paths["folder"]
    source = _regular(solution or folder / "solution.py")
    notes = _regular(folder / "SOLVE_NOTES.md")
    attempts = folder / "attempts"
    attempts.mkdir(exist_ok=True)
    number = len(list(attempts.glob("[0-9][0-9][0-9][0-9]"))) + 1
    revision = attempts / f"{number:04d}"
    revision.mkdir(exist_ok=False)
    (revision / "solution.py").write_bytes(source)
    (revision / "SOLVE_NOTES.md").write_bytes(notes)
    report = {"schema": "arcpuzzles-reviewer-solve-attempt-v1", "revision": number,
              "assignment_id": summary["assignment_id"], "generator_hash": summary["generator_hash"],
              "instance_hash": summary["instance_hash"], "program_hash": digest(source),
              "notes_sha256": digest(notes), "note": note, "verification": "reviewer_local",
              "attempt_intent": intent,
              "training_admitted": False}
    try:
        score, run = evaluate_program(source, episode["public"], episode["test_outputs"], timeout=timeout)
    except Exception as exc:
        score = {"execution_status": "controller_error", "private_exact": None, "reported_label": "unknown"}
        run = {"error_type": type(exc).__name__, "error": str(exc)}
    # Keep masked-query scores out of the actor's tool feedback and return files.
    # They are independently regenerated by the maintainer after submission.
    _write(root / paths["private"] / f"scores/{number:04d}.json", {**report, **score})
    feedback = {key: score[key] for key in ("execution_status", "visible_passed", "visible_total") if key in score}
    failed_visible = score.get("visible_passed") is not None and score["visible_passed"] < score["visible_total"]
    feedback["reported_label"] = "bad" if failed_visible or score["execution_status"] in {"timeout", "error"} else "unknown"
    report.update(feedback)
    _write(revision / "report.json", report)
    _write(revision / "execution.json", run)
    summary.update({"status": "attempted", "attempt_count": number, "last_reported_label": feedback["reported_label"]})
    _write(folder / "summary.json", summary)
    return report


def finish_solve(packet_root: Path, *, reference_consulted: bool, earlier_exposure: str, reason: str,
                 kind: str = "post_repair") -> dict:
    if earlier_exposure not in {"yes", "no", "unknown"} or not reason.strip():
        raise ValueError("Record earlier exposure and stopping reason")
    paths = _kind(kind)
    root = packet_root.resolve()
    summary = _summary(root, kind)
    if summary["status"] == "finished":
        raise ValueError("Solve is finished; retained finish notes cannot be replaced")
    if summary["status"] != "blocked":
        _frozen(root, kind)
        if not summary["attempt_count"]:
            raise ValueError("Submit at least one solve attempt, even if it is wrong")
    folder = root / paths["folder"]
    notes = _regular(folder / "SOLVE_NOTES.md")
    if not notes.strip():
        raise ValueError("Final solve notes must be nonempty")
    finished_notes = folder / "FINISHED_NOTES.md"
    with finished_notes.open("xb") as handle:
        handle.write(notes)
    summary.update({"status": "blocked" if summary["status"] == "blocked" else "finished",
                    "reference_consulted_during_solve": reference_consulted,
                    "earlier_rule_exposure": earlier_exposure, "stopping_reason": reason,
                    "final_notes_path": f"{paths['folder']}/FINISHED_NOTES.md",
                    "final_notes_sha256": digest(notes)})
    _write(folder / "summary.json", summary)
    return summary


def _is_grid(value) -> bool:
    return (isinstance(value, list) and 1 <= len(value) <= 30 and isinstance(value[0], list)
            and 1 <= len(value[0]) <= 30 and all(isinstance(row, list) and len(row) == len(value[0])
            and all(type(c) is int and 0 <= c <= 9 for c in row) for row in value))


def _validate_public(public: dict) -> None:
    if (set(public) != {"train", "test"} or not public["train"] or not public["test"]
            or any(set(p) != {"input", "output"} or not _is_grid(p["input"]) or not _is_grid(p["output"])
                   for p in public["train"])
            or any(set(p) != {"input"} or not _is_grid(p["input"]) for p in public["test"])):
        raise ValueError("Solve challenge must contain public grids only")


def validate_solve_payload(read, names: set[str], contract: dict, *, complete: bool,
                           kind: str = "post_repair") -> dict | None:
    """Static evidence binding; returned correctness claims still require independent replay."""
    f = _kind(kind)["folder"]
    if f"{f}/summary.json" not in names:
        if complete:
            raise ValueError(f"Completed return needs a reviewer {kind.replace('_', '-')} solve record")
        return None
    summary = json.loads(read(f"{f}/summary.json"))
    if kind == "blind" and summary.get("solve_kind") != "blind_before_repair":
        raise ValueError("Blind solve record is not marked blind_before_repair")
    if (summary.get("schema") != SCHEMA or summary.get("assignment_id") != contract["assignment_id"]
            or summary.get("packet_id") != contract["packet_id"] or summary.get("task_id") != contract["task_id"]
            or summary.get("solve_policy") != POLICY
            or summary.get("status") not in {"prepared", "attempted", "finished", "blocked"}):
        raise ValueError("Invalid reviewer solve identity or status")
    if f"{f}/SOLVE_NOTES.md" not in names or not read(f"{f}/SOLVE_NOTES.md").strip():
        raise ValueError("Reviewer solve needs its work log")
    # Older returns remain valid. When present, the new finish snapshot must
    # have both its fixed path and exact content hash bound in the summary.
    if "final_notes_path" in summary or "final_notes_sha256" in summary:
        if (summary.get("final_notes_path") != f"{f}/FINISHED_NOTES.md"
                or f"{f}/FINISHED_NOTES.md" not in names
                or not read(f"{f}/FINISHED_NOTES.md").strip()
                or digest(read(f"{f}/FINISHED_NOTES.md")) != summary.get("final_notes_sha256")):
            raise ValueError("Reviewer final notes snapshot hash or path differs")
    if summary["status"] == "blocked":
        if not summary.get("stopping_reason") or summary.get("attempt_count") != 0:
            raise ValueError("Blocked solve needs a reason and zero attempts")
        return summary
    required = {f"{f}/challenge.json", f"{f}/source/generator.py"}
    if not required <= names:
        raise ValueError("Missing solve challenge or generator source snapshot")
    public_raw = read(f"{f}/challenge.json")
    public = json.loads(public_raw)
    _validate_public(public)
    if (instance_hash(public) != summary.get("instance_hash")
            or digest(public_raw) != summary.get("challenge_sha256")
            or digest(read(f"{f}/source/generator.py")) != summary.get("generator_hash")):
        raise ValueError("Reviewer solve source or instance hash differs")
    reports = sorted(n for n in names if n.startswith(f"{f}/attempts/") and n.endswith("/report.json"))
    if summary.get("attempt_count") != len(reports):
        raise ValueError("Solve attempt count differs")
    for index, name in enumerate(reports, 1):
        home = f"{f}/attempts/{index:04d}"
        if name != home + "/report.json" or not {home + "/solution.py", home + "/SOLVE_NOTES.md"} <= names:
            raise ValueError("Missing or unordered solve revision")
        report = json.loads(read(name))
        if report.get("attempt_intent", "unknown") not in ATTEMPT_INTENTS:
            raise ValueError("Invalid solve attempt intent")
        if summary.get("feedback_policy") == "visible_only" and any(
                field in report for field in ("private_exact", "query_passed", "query_total")):
            raise ValueError("Visible-only solve report contains private query feedback")
        if (report.get("schema") != "arcpuzzles-reviewer-solve-attempt-v1" or report.get("revision") != index
                or report.get("assignment_id") != contract["assignment_id"]
                or report.get("generator_hash") != summary["generator_hash"]
                or report.get("instance_hash") != summary["instance_hash"]
                or report.get("program_hash") != digest(read(home + "/solution.py"))
                or report.get("notes_sha256") != digest(read(home + "/SOLVE_NOTES.md"))
                or not report.get("note") or report.get("reported_label") not in {"good", "bad", "unknown"}):
            raise ValueError("Solve revision hash or identity differs")
    if complete and (summary["status"] != "finished" or not reports
            or type(summary.get("reference_consulted_during_solve")) is not bool
            or summary.get("earlier_rule_exposure") not in {"yes", "no", "unknown"}
            or not summary.get("stopping_reason")):
        raise ValueError("Completed return needs finished solve, exposure declaration, and stopping reason")
    return summary


def _public_cli_result(value: dict) -> dict:
    """Project retained authoring records to visible-only CLI feedback.

    Keep provenance and private source/label metadata in their original records.
    New fields are private by default; nested payloads cannot bypass this list.
    This is a presentation boundary, not a filesystem access-control boundary.
    """
    fields = (
        "schema", "assignment_id", "packet_id", "task_id", "solve_kind",
        "status", "solve_policy", "feedback_policy", "source_kind",
        "generator_hash", "instance_hash", "challenge_sha256",
        "attempt_count", "training_admitted", "last_reported_label",
        "reference_consulted_during_solve", "earlier_rule_exposure",
        "stopping_reason", "final_notes_path", "final_notes_sha256",
        "revision", "program_hash", "notes_sha256", "note", "verification",
        "attempt_intent", "execution_status", "visible_passed", "visible_total",
        "reported_label",
    )
    return {key: value[key] for key in fields if key in value
            and (value[key] is None or type(value[key]) in (str, int, bool))}


def main(packet_root: Path, argv: list[str]) -> int:
    kind = "post_repair"
    if argv[:1] == ["blind"]:
        kind, argv = "blind", argv[1:]
    parser = argparse.ArgumentParser(
        prog="solve_episode.py" + (" blind" if kind == "blind" else ""),
        description="Prepare and record a fresh solve from visible pairs only"
                    + ("; blind: an untouched task, solved before any repair work" if kind == "blind" else ""))
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("prepare")
    check = actions.add_parser("check")
    check.add_argument("--solution", type=Path)
    check.add_argument("--note", required=True)
    check.add_argument("--timeout", type=float, default=30)
    check.add_argument("--intent", choices=ATTEMPT_INTENTS, default="solve",
                       help="solve attempt, deliberate teaching negative, or diagnostic probe")
    finish = actions.add_parser("finish")
    finish.add_argument("--reference-consulted", choices=("yes", "no"), required=True)
    finish.add_argument("--earlier-exposure", choices=("yes", "no", "unknown"), required=True)
    finish.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    if args.action == "prepare":
        value = prepare_solve(packet_root, kind)
    elif args.action == "check":
        value = check_solve(packet_root, args.solution, note=args.note, timeout=args.timeout,
                            intent=args.intent, kind=kind)
    else:
        value = finish_solve(packet_root, reference_consulted=args.reference_consulted == "yes",
                             earlier_exposure=args.earlier_exposure, reason=args.reason, kind=kind)
    if args.action == "prepare" and value.get("status") != "blocked":
        # Keep JSON stdout stable; present only the already-public arrays.
        public = json.loads(_regular(packet_root / _kind(kind)["folder"] / "challenge.json"))
        print(format_task(public), file=sys.stderr)
    print(json.dumps(_public_cli_result(value), indent=2))
    return 1 if value.get("status") == "blocked" else 0
