"""The arcpuzzles command-line interface."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shlex
import signal
import os
from pathlib import Path
import sys

from .catalog import Catalog, sha256
from . import review
from .runtime import CHECK_PHASES, STAGES, GenerationFailure, apply_rule, check, generate, generation_source_identity, parse_apply_inputs, prepare_runtime
from .datasets import STYLES, MODES


def _override(value: str) -> tuple[str, object]:
    """Parse a generator argument without evaluating code or shell syntax."""
    key, separator, raw = value.partition("=")
    if not separator or not key.isidentifier():
        raise argparse.ArgumentTypeError("Expected NAME=JSON, for example height=12 or scene_profile=\"match_0_single\"")
    try:
        return key, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Override {key}: value must be JSON (quote string values)") from exc


def _filters(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--approved", dest="approved", action="store_true", default=None,
                       help="reviewed_safe, positive weight, no veto, current generator/rule hashes")
    group.add_argument("--not-approved", dest="approved", action="store_false")
    parser.add_argument("--source", help="exact source or source family, e.g. training or bank")
    parser.add_argument("--skill", help="case-insensitive exact skill tag")
    parser.add_argument("--primitive", help="exact Racket primitive")
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    parser.add_argument("--kind", choices=("per_puzzle", "generic"))
    parser.add_argument("--train-safety", help="raw approval/review label, e.g. unverified or reviewed_safe")
    parser.add_argument("--search", help="substring in ID, summary, or skills")
    parser.add_argument("--has-generator", action="store_true", default=None)
    parser.add_argument("--audit-unresolved", action="store_true", default=None,
                        help="generators with unresolved or not-yet-triaged audits")
    parser.add_argument("--family", help="recorded root rule family ID")
    parser.add_argument("--split", help="recorded split assignment; missing lineage is never guessed")


def _filter_values(args) -> dict:
    names = ("approved", "source", "skill", "primitive", "difficulty", "kind", "audit_unresolved",
             "train_safety", "search", "has_generator", "family", "split")
    return {key: getattr(args, key) for key in names if getattr(args, key, None) is not None}


def _json(value, output: Path | None = None) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output is None:
        print(content, end="")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            handle.write(content)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="arcpuzzles", description="Query, generate, check, and review the local ARC puzzle library.")
    top.add_argument("--library", type=Path, help="explicit ARCpuzzles library (default: this checkout or bundled wheel)")
    commands = top.add_subparsers(dest="command", required=True)
    query = commands.add_parser("list", aliases=["query"], help="filter puzzle/generator metadata")
    _filters(query)
    query.add_argument("--limit", type=int, default=50, help="maximum rows; 0 means no rows")
    query.add_argument("--all", action="store_true", help="remove the default 50-row limit")
    query.add_argument("--offset", type=int, default=0)
    query.add_argument("--sample", type=int, help="sample matching rows reproducibly")
    query.add_argument("--seed", type=int, default=0)
    query.add_argument("--count", action="store_true", help="print total matching count, before paging")
    query.add_argument("--format", choices=("table", "json", "jsonl", "ids"), default="table")
    detail = commands.add_parser("show", aliases=["get"], help="puzzle details, reference rules, and notes")
    detail.add_argument("id")
    detail.add_argument("--challenge", action="store_true", help="demo pairs and query inputs only; no solutions/summary")
    detail.add_argument("--variant", type=int, default=0)
    detail.add_argument("--out", type=Path)
    grid = commands.add_parser("grid", help="inspect a visible grid/task JSON; safe shapes/colors, no task lookup")
    grid.add_argument("file", type=Path, help="grid array or visible task JSON; task query outputs are ignored")
    grid.add_argument("--compare", type=Path, help="actual grid JSON to compare with FILE as expected; shapes may differ")
    grid.add_argument("--json", action="store_true", help="structured task statistics instead of labelled visible arrays")
    commands.add_parser("stats", help="counts, source families, and approval reasons")
    parametric = commands.add_parser("parametric", help="qualify, accept and use source-bound parameter variants")
    parameter_actions = parametric.add_subparsers(dest="action", required=True)
    parameter_actions.add_parser("list", help="list accepted variant families and any source drift")
    parameter_status = parameter_actions.add_parser("status")
    parameter_status.add_argument("id")
    qualify = parameter_actions.add_parser("qualify", help="execute every setting on fresh seeds through protected Racket")
    qualify.add_argument("id")
    qualify.add_argument("--seed", type=int, action="append")
    qualify.add_argument("--demos", type=int, default=3)
    qualify.add_argument("--queries", type=int, default=4)
    qualify.add_argument("--timeout", type=float, default=180)
    qualify.add_argument("--out", type=Path, required=True)
    accept_parameter = parameter_actions.add_parser("accept", help="accept the exact qualified source/rule binding")
    accept_parameter.add_argument("id")
    accept_parameter.add_argument("--qualification", type=Path, required=True)
    accept_parameter.add_argument("--reason", required=True)
    for action in ("generate", "export"):
        parameter_run = parameter_actions.add_parser(action)
        parameter_run.add_argument("id")
        parameter_run.add_argument("--count", type=int, default=1)
        parameter_run.add_argument("--seed", type=int, default=0)
        parameter_run.add_argument("--demos", type=int, default=3)
        parameter_run.add_argument("--queries", type=int, default=4)
        parameter_run.add_argument("--settings", type=json.loads, help="private fixed episode settings as JSON")
        parameter_run.add_argument("--timeout", type=float, default=180)
        parameter_run.add_argument("--out", type=Path, required=action == "export")
    parameter_verify = parameter_actions.add_parser("verify-export")
    parameter_verify.add_argument("directory", type=Path)
    gen = commands.add_parser("generate", help="generate episodes and verify outputs through Racket")
    gen.add_argument("id")
    gen.add_argument("--count", type=int, default=1)
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--sample-index", type=int, default=0, help="first generator sample index in each episode")
    gen.add_argument("--override", type=_override, action="append", default=[], metavar="NAME=JSON",
                     help="repeat for generator-specific axes; values must be JSON")
    gen.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    gen.add_argument("--train", type=int, help="explicit demo count; omitted uses declared minimum, floor 3")
    gen.add_argument("--test", type=int, default=1)
    gen.add_argument("--allow-unapproved", action="store_true", help="explicit research use; output retains unapproved label")
    gen.add_argument("--reference", choices=("canonical", "archival"), default="canonical",
                     help="archival rules require --allow-unapproved and never inherit canonical approval")
    gen.add_argument("--timeout", type=float, default=180, help="seconds for this whole invocation")
    gen.add_argument("--out", type=Path, help="new JSONL file; refuses to overwrite. Completed episodes of an "
                     "interrupted run are kept in OUT.partial.jsonl")
    gen.add_argument("--resume", action="store_true",
                     help="continue OUT.partial.jsonl from an interrupted run with identical arguments")
    apply = commands.add_parser("apply", help="run a task's reference rule on hand-made input grids (audit evidence)")
    apply.add_argument("id")
    apply.add_argument("--input", type=Path, required=True,
                       help="JSON file: a grid, a list of grids, {\"input\": grid} or {\"inputs\": [...]}")
    apply.add_argument("--reference", choices=("canonical", "archival"), default="canonical")
    apply.add_argument("--allow-unapproved", action="store_true", help="required for --reference archival")
    apply.add_argument("--check-generator-domain", action="store_true", help="record selected self_check results independently of Racket")
    apply.add_argument("--timeout", type=float, default=120)
    apply.add_argument("--out", type=Path, help="new JSON file; refuses to overwrite")
    sync = commands.add_parser("authority-sync", help="review exact-text proposals; explicit --apply requires a saved proposal")
    sync.add_argument("id")
    sync.add_argument("--selected-only", action="store_true", required=True,
                      help="canonical program_solution to selected target_code; preserves archival raw_code")
    sync.add_argument("--out", type=Path, help="new JSON proposal file; refuses to overwrite")
    sync.add_argument("--apply", type=Path, metavar="REVIEWED_PROPOSAL.json",
                      help="explicitly apply this exact current dry-run proposal; retains recovery snapshots")
    export = commands.add_parser("export", help="bounded mixed sampling with separate challenges, labels and optional training formats")
    _filters(export)
    export.add_argument("--id", action="append", help="restrict sampling to these IDs; repeatable, other filters still apply")
    export.add_argument("--count", type=int, required=True, help="accepted episodes, or synthetic chains; not rendered row count")
    export.add_argument("--seed", type=int, default=0)
    export.add_argument("--style", choices=STYLES, default="challenges")
    export.add_argument("--render", choices=("raw", "chatml", "harmony"), default="raw")
    export.add_argument("--sampling", choices=("weighted", "uniform"), default="weighted")
    export.add_argument("--train", type=int, help="explicit demo count; omitted uses canonical minimum/floor4 or accepted adapter minimum")
    export.add_argument("--test", type=int, default=1)
    export.add_argument("--draw-difficulty", choices=("easy", "medium", "hard"),
                        help="generator difficulty argument; --difficulty filters recorded canonical metadata")
    export.add_argument("--allow-unapproved", action="store_true", help="explicit research sampling; source labels remain recorded")
    export.add_argument("--reference", choices=("canonical", "archival"), default="canonical",
                        help="archival reference execution is explicitly unapproved research")
    export.add_argument('--accepted-parameters', action='store_true',
                        help='opt in to current accepted families; other draws stay canonical; no training admission')
    export.add_argument("--max-attempts", type=int, help="total draw cap; default twice count")
    export.add_argument("--timeout", type=float, default=180, help="seconds per generation or render worker")
    export.add_argument("--mode", action="append", choices=MODES, help="DSL mode; repeatable; default predict/synth/exec/invert")
    export.add_argument("--mutations", type=int, default=8, help="mutation slots per hindsight episode")
    export.add_argument("--stages", type=int, default=3, help="prefixes requested in each synthetic chain")
    export.add_argument("--system-prompt", default="")
    export.add_argument("--fence", action="store_true", help="display Racket chat targets with code fences")
    export.add_argument("--group-queries", action="store_true", help="native v2 rows retain all query pairs together")
    export.add_argument("--tensors", choices=("none", "native", "bottleneck"), default="none",
                        help="native style: optional private CPU safetensors; requires tensors extra")
    export.add_argument("--canvas-size", type=int, default=30, help="tensor canvas size; oversized grids are rejected")
    export.add_argument("--out", type=Path, required=True, help="new export directory; incomplete runs retain their evidence")
    inspect_export = commands.add_parser("inspect-export", help="verify a complete dataset's hashes and public/private binding")
    inspect_export.add_argument("directory", type=Path)
    census = commands.add_parser("census", help="compare generation with the retained historical runner; never changes approval")
    _filters(census)
    census.add_argument("--draw-difficulty", choices=("easy", "medium", "hard"), default="medium")
    census.add_argument("--seed", type=int, default=17)
    census.add_argument("--limit", type=int)
    census.add_argument("--workers", type=int, default=4)
    census.add_argument("--timeout", type=float, default=15)
    census.add_argument("--out", type=Path, required=True)
    lessons = commands.add_parser("lesson-census", help="source-bound Racket lesson/rival census; never changes approval")
    lessons.add_argument("id")
    lessons.add_argument("--rescore", type=Path,
                         help="recheck complete saved census against current rivals at every query position; no generation or Racket execution")
    lessons.add_argument("--per-band", type=int, default=20)
    lessons.add_argument("--train", type=int, help="demo count (default: generator EXAMPLES_NEEDED or 3)")
    lessons.add_argument("--test", type=int, default=1)
    lessons.add_argument("--period", type=int, default=6, help="start-residue reporting modulus; not an inferred contract")
    lessons.add_argument("--enumerate-schedule-period", action="store_true",
                         help="enumerate declared LESSON_SCHEDULE_PERIOD starts per band and every query position at one fixed seed; overrides --per-band")
    lessons.add_argument("--schedule-seed", type=int, default=0,
                         help="fixed seed for schedule enumeration (default: 0)")
    lessons.add_argument("--rotate-query", action="store_true", help="hold out every materialized pair once; requires --test 1")
    lessons.add_argument("--rotation-policy", choices=("require", "diagnostic"), default="require",
                         help="require keeps rotations in the exit verdict; diagnostic reports them separately")
    lessons.add_argument("--band", action="append", choices=("easy", "medium", "hard"))
    lessons.add_argument("--timeout", type=float, default=330)
    lessons.add_argument('--gzip', action='store_true',
                         help='write the complete report as deterministic PATH.gz plus a hash-bound compression manifest; PATH must end in .json')
    lessons.add_argument("--out", type=Path, required=True,
                         help="new full JSON report path; --gzip writes PATH.gz instead. Also writes a compact .summary.json authoring companion")
    managed = commands.add_parser("check-run", help="managed detached source-bound battery")
    managed.add_argument("action", choices=("start","status","wait","resume"))
    managed.add_argument("target", help="task ID for start; stable run ID otherwise")
    managed.add_argument("--timeout", type=float, default=330)
    managed.add_argument("--phase", choices=CHECK_PHASES, default="after",
                         help="before baseline; after repair verification; audit peer inspection (strict checks)")
    managed.add_argument("--wait-seconds", type=float, default=30)
    gate = commands.add_parser("check", help="run the inherited generator battery or one stage")
    gate.add_argument("id")
    gate.add_argument("--stage", choices=(*STAGES, "task_tests", "audit"), default="lint",
                      help="inherited stage; task_tests for portable pytest; audit for task_tests plus semantic_gate on one snapshot")
    gate.add_argument("--resume", action="store_true", help="resume exact-source battery evidence in --out")
    gate.add_argument("--battery", action="store_true", help="all twelve stages, keeping failures visible")
    gate.add_argument("--full-results", action="store_true", help="retain all override case/finding details (default is root-cause summary)")
    gate.add_argument("--compact-results", action="store_true",
                      help="omit successful override case detail; retain totals, failures and replay settings")
    gate.add_argument("--require-rotations-identifiable", action="store_true",
                      help="fail semantic_gate (or battery) on query-rotation ambiguity, warnings or errors")
    gate.add_argument('--schedule-census', type=Path,
                      help='consume a complete source-bound fixed-seed schedule JSON, native .json.gz + neighboring .compression.json, or its one-file manifest; verifies and retains exact input bytes')
    gate.add_argument('--schedule-seed', type=int, default=0,
                      help='required receipt seed (default 0; finite coverage only)')
    gate.add_argument('--enumerate-schedule-period', action='store_true',
                      help='generate every declared start and query rotation at one fixed seed within the semantic stage; retain full labelled census')
    gate.add_argument("--phase", choices=CHECK_PHASES, default=None,
                      help="before baseline; after repair verification; audit peer inspection (strict checks); defaults to before or the saved phase with --resume")
    gate.add_argument("--timeout", type=float, default=330, help="overall timeout in seconds; increase for full battery")
    gate.add_argument("--out", type=Path,
                      help="logs/receipts directory. Without --resume, PATH itself must not exist (its parent may exist). "
                           "With --resume, PATH must be the original checkpoint directory")
    commands.add_parser("tools", help="list the preserved checks and their purposes")
    status = commands.add_parser('check-status', help='read checkpoint and controller/child liveness; never signals processes')
    status.add_argument('--out', type=Path, required=True)
    workspace = commands.add_parser("workspace", help="copy a complete independent runtime for inherited generation tools")
    workspace.add_argument("--id", help="include only this generator; default includes the full library")
    workspace.add_argument("--out", type=Path, required=True, help="new or empty runtime directory")
    lint = commands.add_parser("lint", help="validate library structure and source mappings without executing generators")
    lint.add_argument("--verify-import", action="store_true", help="also compare imported files to their original hashes")
    lint.add_argument("--imports", action="store_true", help="also import every generator in a separate local runtime")
    serve = commands.add_parser("serve", help="start the read-only HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    reviews = commands.add_parser("review", help="prepare and manage local improvement requests")
    reviews.add_argument("--root", type=Path, help="review workspace (default: library/REVIEW)")
    actions = reviews.add_subparsers(dest="action", required=True)
    pick = actions.add_parser("pick", help="claim a random matching, unclaimed generator")
    _filters(pick)
    pick.add_argument("--seed", type=int, default=0)
    pick.add_argument("--id", help="choose this exact generator instead of random selection")
    pick.add_argument("--question-id", help="bind this versioned review question")
    pick.add_argument("--cohort", type=Path, help="source-bound review cohort receipt")
    actions.add_parser("list", help="read assignment statuses")
    pack = actions.add_parser("pack", help="create a portable local ZIP for an assignment")
    pack.add_argument("id")
    pack.add_argument("--out", type=Path, required=True)
    priority = actions.add_parser("parametric-priority", help="inspect the source-bound original-task parametric work queue")
    priority.add_argument("--out", type=Path, help="write a new JSON receipt")
    pack_full = actions.add_parser("pack-full", help="build one reusable full-library review ZIP")
    pack_full.add_argument("--out", type=Path, required=True)
    pack_full.add_argument("--racket-archive", type=Path,
                           help="include the pinned offline Linux x86_64 Racket archive")
    pack_full.add_argument("--blind-solve", action="store_true",
                           help="require a blind solve of a second, untouched task before repair work")
    extract = actions.add_parser("evidence-extract", help="verify and unpack a return's bundled check evidence")
    extract.add_argument("zip", type=Path)
    extract.add_argument("--out", type=Path, required=True)
    replay = actions.add_parser("replay-return", help="replay exact return bytes in a fresh checkout; tests remain separate")
    replay.add_argument("--source-zip", type=Path, required=True)
    replay.add_argument("--return-zip", type=Path, required=True)
    replay.add_argument("--compare-work", type=Path, required=True, help="reviewed WORK directory containing repo/")
    replay.add_argument("--out", type=Path, required=True, help="new directory for checkout and hash receipts")
    replay.add_argument("--runtime-closure", action="store_true", help="extract only declared runtime/API dependencies and selected task; explicitly partial")
    intake = actions.add_parser("intake", help="retain and validate a returned review ZIP")
    intake.add_argument("zip", type=Path)
    collect = actions.add_parser("collect", help="retain and validate a folder of full-packet returns")
    collect.add_argument("directory", type=Path)
    inbox = actions.add_parser("inbox", help="build a local full-packet triage inbox")
    inbox.add_argument("--out", type=Path)
    notes_migrate = actions.add_parser("notes-migrate", help="preview moving old review notes into generator homes")
    notes_migrate.add_argument("--apply", action="store_true")
    compact = actions.add_parser("compact", help="extract useful current state and dispose processed managed ZIPs")
    compact.add_argument("--apply", action="store_true", help="verify extraction, then delete processed transports")
    audit_status = actions.add_parser("audit-status", help="append a generator audit resolution or reopen it")
    audit_status.add_argument("task")
    audit_status.add_argument("--return-id", required=True)
    audit_status.add_argument("--status", required=True,
                              choices=("unresolved", "resolved", "no_issue", "disputed", "needs_evidence"))
    audit_status.add_argument("--reason", required=True)
    solve_check = actions.add_parser("solve-check", help="independently replay an inspected reviewer's Python solves")
    solve_check.add_argument("id")
    solve_check.add_argument("--version", type=int, required=True)
    solve_check.add_argument("--timeout", type=float, default=30)
    bank_sources = actions.add_parser("bank-sources", help="export generator identities and retained public episodes")
    bank_sources.add_argument("--out", type=Path, required=True)
    review_check = actions.add_parser("check", help="apply and check a return in a disposable workspace")
    review_check.add_argument("id")
    review_check.add_argument("--version", type=int, required=True)
    review_check.add_argument("--timeout", type=float, default=4000)
    review_check.add_argument("--lint-override", type=Path,
                              help="full packet only: recheck with an explicit hash-recorded lint script")
    assess = actions.add_parser("assess", help="summarize a returned candidate and blockers")
    assess.add_argument("id")
    assess.add_argument("--version", type=int, required=True)
    integrate = actions.add_parser("integrate", help="select return components using reviewer-reported evidence or independent checks")
    integrate.add_argument("id")
    integrate.add_argument("--version", type=int, required=True)
    integrate.add_argument("--component", choices=("generator", "racket", "tests_notes"), action="append", default=[])
    integrate.add_argument("--reviewer-reported", action="store_true",
                           help="accept a full return using reviewer evidence; apply only changed files without rerunning checks")
    approve = actions.add_parser("approve", help="record safety review for accepted, source-matched repairs")
    approve.add_argument("id", nargs="?")
    approve.add_argument("--version", type=int)
    approve.add_argument("--all-integrated", action="store_true", help="backfill accepted live repairs")
    combine = actions.add_parser("combine", help="stage a reviewed combination of full returns")
    combine.add_argument("--source", action="append", required=True, help="ASSIGNMENT_ID:VERSION; repeat")
    combine.add_argument("--out", type=Path, required=True)
    disposition = actions.add_parser("disposition", help="record a full-return component or finding decision")
    disposition.add_argument("id")
    disposition.add_argument("--version", type=int, required=True)
    disposition.add_argument("--kind", choices=("generator", "racket", "tests_notes", "audit", "feedback", "decision"), required=True)
    disposition.add_argument("--status", choices=("accepted", "rejected", "needs_evidence", "deferred", "implemented"), required=True)
    disposition.add_argument("--reason", required=True)
    feedback = actions.add_parser("feedback", help="record a general feedback item disposition")
    feedback.add_argument("id")
    feedback.add_argument("--version", type=int, required=True)
    feedback.add_argument("--item", required=True)
    feedback.add_argument("--status", choices=("accepted", "implemented", "needs_evidence", "deferred", "declined"), required=True)
    feedback.add_argument("--reason", required=True)
    close = actions.add_parser("close", help="record a disposition and release the claim")
    close.add_argument("id")
    close.add_argument("--status", choices=("completed", "cancelled"), required=True)
    close.add_argument("--note", required=True)
    return top


def _generate_with_partial(catalog: Catalog, args) -> list[dict]:
    """Complete output only on full success; keep finished episodes of an interrupted run."""
    if args.out and args.out.exists():
        raise FileExistsError(f"Generation output already exists: {args.out}")
    partial = args.out.with_name(args.out.name + ".partial.jsonl") if args.out else None
    source_identity = generation_source_identity(catalog, args.id)
    identity = {"schema": "arcpuzzles-generate-partial-v1", "task_id": args.id, "count": args.count,
                "seed": args.seed, "sample_index": args.sample_index, "difficulty": args.difficulty,
                "overrides": dict(args.override), "n_train": args.train, "n_test": args.test,
                "reference": args.reference, "allow_unapproved": args.allow_unapproved,
                "generation_sources_sha256": source_identity}
    kept: list[dict] = []
    if args.resume:
        if partial is None or not partial.exists():
            raise FileNotFoundError("--resume needs --out and an existing OUT.partial.jsonl")
        lines = partial.read_text().splitlines()
        if not lines:
            raise ValueError(f"{partial} has no generation header")
        recorded = json.loads(lines[0])
        if not isinstance(recorded, dict) or not recorded.get("generation_sources_sha256"):
            raise ValueError(f"{partial} has no source fingerprint; retain it and start a new output, without --resume")
        if recorded["generation_sources_sha256"] != source_identity:
            raise ValueError("Generation sources changed since the interrupted run; retain it and start a new output")
        if recorded != identity:
            raise ValueError(f"{partial} was written with different generation arguments")
        kept = [json.loads(line) for line in lines[1:]]
        if len(kept) > args.count or any(not isinstance(item, dict) for item in kept):
            raise ValueError(f"{partial} has invalid or too many episodes")
        if [row.get("episode_index") for row in kept] != list(range(len(kept))):
            raise ValueError(f"{partial} episodes are not contiguous from index 0")
        row = catalog.describe(args.id)
        if any(item.get("task_id") != row.get("id", args.id)
               or type(item.get("seed")) is not int or item["seed"] != args.seed + index
               for index, item in enumerate(kept)):
            raise ValueError(f"{partial} episode task or seed differs from the generation request")
        if any(item["provenance"]["generator_sha256"] != row["generator_sha256"]
               or item["provenance"]["catalog_rule_hash"] != row["rule_hash"] for item in kept):
            raise ValueError("Generator or rule changed since the interrupted run; start a new output")
    elif partial is not None and partial.exists():
        raise FileExistsError(f"{partial} exists; continue it with --resume or move it aside")
    rows: list[dict] = []
    if len(kept) < args.count:
        try:
            rows = generate(catalog, args.id, count=args.count, seed=args.seed, difficulty=args.difficulty,
                            sample_index=args.sample_index, overrides=dict(args.override),
                            n_train=args.train, n_test=args.test, allow_unapproved=args.allow_unapproved,
                            timeout=args.timeout, reference=args.reference, start_index=len(kept))
        except GenerationFailure as exc:
            if partial is not None and exc.partial_episodes:
                partial.parent.mkdir(parents=True, exist_ok=True)
                with partial.open("a") as handle:
                    if handle.tell() == 0:
                        handle.write(json.dumps(identity) + "\n")
                    for item in exc.partial_episodes:
                        handle.write(json.dumps(item, ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                print(f"Kept {len(kept) + len(exc.partial_episodes)}/{args.count} completed episodes in "
                      f"{partial}; rerun with --resume to continue.", file=sys.stderr)
            raise
    complete = kept + rows
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x") as handle:
            handle.write("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in complete))
        if partial.exists():
            partial.unlink()
            print(f"Completed all {args.count} episodes; removed {partial}.", file=sys.stderr)
    return complete


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "grid":
            from .grids import inspect_grid, inspect_task, compare_grids, format_task
            value = json.loads(args.file.read_text(encoding="utf-8"))
            if args.compare is not None:
                _json(compare_grids(value, json.loads(args.compare.read_text(encoding="utf-8"))))
            elif isinstance(value, dict):
                if args.json:
                    _json(inspect_task(value))
                else:
                    print(format_task(value))
            else:
                _json(inspect_grid(value))
            return 0
        catalog = Catalog(args.library)
        if args.command in {"list", "query"}:
            filters = _filter_values(args)
            if args.count:
                print(len(catalog.query(**filters)))
                return 0
            rows = catalog.query(**filters, limit=None if args.all else args.limit, offset=args.offset,
                                 sample=args.sample, seed=args.seed)
            if args.format == "json":
                _json(rows)
            elif args.format == "jsonl":
                for row in rows:
                    print(json.dumps(row, ensure_ascii=False))
            elif args.format == "ids":
                for row in rows:
                    print(row["id"])
            else:
                print(f"{'ID':<38} {'APPROVED':<9} {'SAFETY':<20} SUMMARY")
                for row in rows:
                    summary = " ".join(row["summary"].split())[:100]
                    print(f"{row['id']:<38} {str(row['approved']).lower():<9} {row['train_safety']:<20} {summary}")
                print(f"{len(rows)} rows; use --all or --offset for more, --count for the matching total.", file=sys.stderr)
        elif args.command in {"show", "get"}:
            _json(catalog.challenge(args.id, variant=args.variant) if args.challenge else catalog.get(args.id), args.out)
        elif args.command == "stats":
            _json(catalog.stats())
        elif args.command == "generate":
            rows = _generate_with_partial(catalog, args)
            if not args.out:
                print("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), end="")
            print(f"Generated {len(rows)} episodes; {sum(len(r['rejections']) for r in rows)} recorded rejections.", file=sys.stderr)
        elif args.command == "check-run":
            from . import check_jobs
            if args.action == "start":
                _json(check_jobs.start(catalog,args.target,timeout=args.timeout,phase=args.phase))
            elif args.action == "resume":
                _json(check_jobs.resume(catalog.root,args.target))
            elif args.action == "wait":
                _json(check_jobs.wait(catalog.root,args.target,seconds=args.wait_seconds))
            else:
                _json(check_jobs.status(catalog.root,args.target))
        elif args.command == "parametric":
            from . import parametric_promotion as parameters
            if args.action == "list":
                records = [parameters.status(catalog, path.parent.parent.name)
                           for path in sorted((catalog.root/'generators').glob('*/parametric/accepted.json'))]
                _json([{key: row[key] for key in ('task_id', 'status', 'parameters', 'default',
                        'acceptance_sha256', 'reason') if key in row} for row in records])
            elif args.action == "status":
                _json(parameters.status(catalog, args.id))
            elif args.action == "qualify":
                _json(parameters.qualify(catalog, args.id, args.out, seeds=args.seed,
                                        demos=args.demos, queries=args.queries, timeout=args.timeout))
            elif args.action == "accept":
                _json(parameters.accept(catalog, args.id, args.qualification, reason=args.reason))
            elif args.action == "verify-export":
                _json(parameters.verify_export(args.directory))
            else:
                options = dict(count=args.count, seed=args.seed, demos=args.demos,
                               queries=args.queries, settings=args.settings, timeout=args.timeout)
                if args.action == "export":
                    _json(parameters.export(catalog, args.id, args.out, **options))
                else:
                    episodes = parameters.generate(catalog, args.id, **options)
                    content = ''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in episodes)
                    if args.out:
                        args.out.parent.mkdir(parents=True, exist_ok=True)
                        with args.out.open('x') as handle: handle.write(content)
                    else:
                        print(content, end='')
        elif args.command == "apply":
            if args.out and args.out.exists():
                raise FileExistsError(f"Apply output already exists: {args.out}")
            inputs = parse_apply_inputs(json.loads(args.input.read_text()))
            record = apply_rule(catalog, args.id, inputs, reference=args.reference,
                                check_generator_domain=args.check_generator_domain,
                                allow_unapproved=args.allow_unapproved, timeout=args.timeout)
            record["command"] = ["arcpuzzles", *(argv if argv is not None else sys.argv[1:])]
            record["cwd"] = str(Path.cwd())
            content = json.dumps(record, indent=1) + "\n"
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                with args.out.open("x") as handle:
                    handle.write(content)
            else:
                print(content, end="")
            failed = [r["index"] for r in record["results"] if r["error"]]
            if failed:
                print(f"Rule failed on input(s) {failed}; see each result's error.", file=sys.stderr)
                return 1
        elif args.command == "export":
            result = catalog.export(args.out, count=args.count, seed=args.seed, task_ids=args.id,
                                    filters=_filter_values(args), style=args.style, render=args.render,
                                    sampling=args.sampling, n_train=args.train, n_test=args.test,
                                    difficulty=args.draw_difficulty, allow_unapproved=args.allow_unapproved,
                                    max_attempts=args.max_attempts, timeout=args.timeout, modes=args.mode,
                                    mutations=args.mutations, stages=args.stages,
                                    system_prompt=args.system_prompt, fence=args.fence,
                                    group_queries=args.group_queries, tensors=args.tensors, canvas_size=args.canvas_size,
                                    reference=args.reference, accepted_parameters=args.accepted_parameters)
            _json({key: result[key] for key in ("dataset_id", "status", "accepted_episodes",
                                               "attempted_episodes", "rendered_rows", "row_counts")})
            return 0 if result["status"] == "complete" else 1
        elif args.command == "census":
            from .census import census
            result = census(catalog, args.out, seed=args.seed, difficulty=args.draw_difficulty,
                            filters=_filter_values(args), workers=args.workers, timeout=args.timeout, limit=args.limit)
            _json(result)
            return 0 if not any(result["counts"].get(name) for name in ("different", "legacy_only", "infrastructure_error")) else 1
        elif args.command == "inspect-export":
            from .datasets import verify_dataset
            _json(verify_dataset(args.directory))
        elif args.command == "lesson-census":
            from .lesson_census import lesson_census, census_companion
            summary_out = args.out.with_suffix('.summary.json')
            compressed_out = args.out.with_suffix('.json.gz')
            compression_manifest = args.out.with_suffix('.compression.json')
            reserved = [args.out, summary_out]
            if args.gzip:
                from .review_evidence_bundle import _safe_path
                if args.out.suffix != '.json' or not _safe_path('checks/' + args.out.name):
                    raise ValueError('--gzip requires a portable .json output filename; it writes PATH.gz')
                reserved.extend((compressed_out, compression_manifest))
            for path in reserved:
                if path.exists() or path.is_symlink():
                    raise FileExistsError(f"Output already exists: {path}; choose a new report path")
            result = lesson_census(catalog, args.id, per_band=args.per_band, n_demos=args.train,
                                   n_queries=args.test, period=args.period, rotate_query=args.rotate_query, rescore=args.rescore,
                                   rotation_policy=args.rotation_policy, enumerate_schedule_period=args.enumerate_schedule_period,
                                   schedule_seed=args.schedule_seed,
                                   bands=tuple(args.band or ("easy", "medium", "hard")), timeout=args.timeout)
            if args.gzip:
                raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
                args.out.parent.mkdir(parents=True, exist_ok=True)
                with compressed_out.open('xb') as output:
                    with gzip.GzipFile(fileobj=output, filename='', mode='wb', mtime=0) as stream:
                        stream.write(raw)
                full_sha256, full_bytes = hashlib.sha256(raw).hexdigest(), len(raw)
                compressed_sha256 = sha256(compressed_out)
                _json({'schema': 'arcpuzzles-evidence-gzip-v1', 'compression': 'gzip',
                       'report_schema': result['schema'], 'status': result['status'],
                       'training_admitted': False,
                       'restore_argv': ['python3', '-m', 'gzip', '-d', compressed_out.name],
                       'restore_note': 'Restore a copy in a new directory; verify raw_size and raw_sha256 before using the full report.',
                       'files': [{'path': args.out.name, 'compressed_path': compressed_out.name,
                                  'raw_size': full_bytes, 'raw_sha256': full_sha256,
                                  'compressed_size': compressed_out.stat().st_size,
                                  'compressed_sha256': compressed_sha256}]}, compression_manifest)
            else:
                _json(result, args.out)
                full_sha256, full_bytes = sha256(args.out), args.out.stat().st_size
            companion = census_companion(result, full_report_sha256=full_sha256,
                                         full_report_path=str(args.out.resolve()),
                                         invocation=argv if argv is not None else sys.argv[1:])
            companion['full_report']['bytes'] = full_bytes
            if args.gzip:
                companion['full_report'].update(storage='gzip', compressed_path=str(compressed_out.resolve()),
                    compressed_sha256=compressed_sha256, compressed_bytes=compressed_out.stat().st_size,
                    compression_manifest=str(compression_manifest.resolve()))
            _json(companion, summary_out)
            _json({"task_id": result["task_id"], "status": result["status"],
                   "production_status": result.get("production_status", "unknown"),
                   "rotation_status": result.get("rotation_status", "unknown"),
                   "rotation_policy": result.get("rotation_policy", args.rotation_policy),
                   "schedule_coverage": result.get("schedule_coverage"),
                   "summary": result.get("summary", {}), "out": str(compressed_out if args.gzip else args.out),
                   "summary_out": str(summary_out),
                   **({'compression_manifest': str(compression_manifest)} if args.gzip else {})})
            return 2 if result["status"] == "error" else 1 if result["status"] == "ambiguous" else 0
        elif args.command == 'check-status':
            from .runtime import check_status
            _json(check_status(args.out.resolve()))
        elif args.command == "check":
            result = check(catalog, args.id, stage=args.stage, timeout=args.timeout, output=args.out,
                           full_battery=args.battery, phase=args.phase, resume=args.resume,
                           require_rotations_identifiable=args.require_rotations_identifiable,
                           schedule_census=args.schedule_census, schedule_seed=args.schedule_seed,
                           enumerate_schedule_period=args.enumerate_schedule_period,
                           compact_results=args.compact_results, full_results=args.full_results,
                           on_output=lambda chunk: print(chunk, end="", file=sys.stderr, flush=True))
            if not (sys.stdout.isatty() and sys.stderr.isatty()):
                # Live progress already went to stderr; replay stdout only for a redirected copy.
                print(result["stdout"], end="")
            print(json.dumps({key: result[key] for key in ("task_id", "stage", "phase", "exit_code", "timed_out", "passed")}), file=sys.stderr)
            return 124 if result["timed_out"] else (0 if result["passed"] else 1)
        elif args.command == "authority-sync":
            from .authority_sync import apply_selected_sync, propose_selected_sync
            if args.apply:
                if args.out:
                    raise ValueError("--out is for dry-run proposals; apply saves its own recovery receipt and prints it")
                _json(apply_selected_sync(catalog, args.id, args.apply))
            else:
                _json(propose_selected_sync(catalog, args.id), args.out)
        elif args.command == "tools":
            _json({name: {"file": f"shared/tools/{file}", "purpose": purpose} for name, (file, purpose) in STAGES.items()})
        elif args.command == "workspace":
            receipt = prepare_runtime(catalog, args.out, args.id)
            _json({"directory": str(args.out.resolve()), "files": len(receipt["files"]),
                   "task_id": receipt["task_id"], "manifest": str(args.out.resolve() / "RUNTIME_MANIFEST.json")})
        elif args.command == "lint":
            from .validation import validate_library
            result = validate_library(catalog, verify_import=args.verify_import, import_generators=args.imports)
            _json(result)
            return 0 if result["passed"] else 1
        elif args.command == "serve":
            from .server import make_server
            with make_server(catalog, args.host, args.port) as server:
                print(f"ARCpuzzles API: http://{server.server_address[0]}:{server.server_address[1]}/v1/puzzles", flush=True)
                server.serve_forever()
        elif args.command == "review":
            root = (args.root or catalog.root / "REVIEW").resolve()
            if args.action == "pick":
                _json(review.pick(catalog, seed=args.seed, task_id=args.id, review_root=root,
                                  question_id=args.question_id, cohort_receipt=args.cohort,
                                  **_filter_values(args)))
            elif args.action == "list":
                _json(review.assignments(root))
            elif args.action == "pack":
                _json({"zip": str(review.pack(root, args.id, args.out))})
            elif args.action == "parametric-priority":
                from .parametric_priority import build_parametric_priority
                _json(build_parametric_priority(catalog), args.out)
            elif args.action == "pack-full":
                from .review_full_packet import build_full_packet
                _json(build_full_packet(catalog, root, args.out,
                                        racket_archive=args.racket_archive, reviewer_solve=True,
                                        blind_solve=args.blind_solve, workspace_layout=True))
            elif args.action == "evidence-extract":
                from .review_evidence_bundle import extract_from_return
                _json(extract_from_return(args.zip, args.out))
            elif args.action == "replay-return":
                from .review_replay import replay_return
                _json(replay_return(args.source_zip, args.return_zip, args.compare_work,
                                    args.out, runtime_closure=args.runtime_closure))
            elif args.action == "intake":
                from .review_return import intake
                _json(intake(root, args.zip))
            elif args.action == "collect":
                from .review_full_collect import collect_full_returns
                _json(collect_full_returns(root, args.directory))
            elif args.action == "inbox":
                from .review_full_inbox import build_full_inbox
                _json(build_full_inbox(root, args.out or catalog.root / "var/review/full-inbox"))
            elif args.action == "compact":
                if root != catalog.root / "REVIEW":
                    raise ValueError("Compaction requires the owning library's REVIEW directory")
                from .review_retention import compact_reviews
                _json(compact_reviews(catalog.root, apply=args.apply))
            elif args.action == "solve-check":
                from .review_solve_tracker import verify_return_solve
                from .review_full_inbox import build_full_inbox
                result = verify_return_solve(root, args.id, args.version, timeout=args.timeout)
                result["inbox"] = build_full_inbox(root, catalog.root / "var/review/full-inbox")["html"]
                _json(result)
            elif args.action == "bank-sources":
                from .review_question_sources import export_question_sources
                _json(export_question_sources(catalog, args.out))
            elif args.action == "check":
                if (root / "assignments" / args.id / "ASSIGNMENT.json").is_file() and json.loads(
                        (root / "assignments" / args.id / "ASSIGNMENT.json").read_text()).get("schema") == "arcpuzzles-full-assignment-v2":
                    from .review_full_candidate import check_full_candidate
                    _json(check_full_candidate(catalog, root, args.id, args.version,
                                               timeout=args.timeout, lint_override=args.lint_override))
                else:
                    if args.lint_override is not None:
                        raise ValueError("--lint-override is only supported for full-packet returns")
                    from .review_candidate import check_candidate
                    _json(check_candidate(catalog, root, args.id, args.version, timeout=args.timeout))
            elif args.action == "assess":
                if (root / "assignments" / args.id / "ASSIGNMENT.json").is_file() and json.loads(
                        (root / "assignments" / args.id / "ASSIGNMENT.json").read_text()).get("schema") == "arcpuzzles-full-assignment-v2":
                    from .review_full_candidate import assess_full_candidate
                    _json(assess_full_candidate(root, args.id, args.version))
                else:
                    from .review_assess import assess
                    _json(assess(root, args.id, args.version))
            elif args.action == "integrate":
                if (root / "assignments" / args.id / "ASSIGNMENT.json").is_file() and json.loads(
                        (root / "assignments" / args.id / "ASSIGNMENT.json").read_text()).get("schema") == "arcpuzzles-full-assignment-v2":
                    from .review_full_integrate import integrate_full_candidate
                    _json(integrate_full_candidate(catalog, root, args.id, args.version, set(args.component),
                                                  reviewer_reported=args.reviewer_reported))
                else:
                    if args.reviewer_reported:
                        raise ValueError("--reviewer-reported is only supported for full-packet returns")
                    from .review_assess import integrate
                    _json(integrate(catalog, root, args.id, args.version, set(args.component)))
            elif args.action == "approve":
                from .review_approval import approve_reviews
                _json(approve_reviews(catalog, root, assignment_id=args.id,
                                      version=args.version, all_integrated=args.all_integrated))
            elif args.action == "combine":
                from .review_full_integrate import stage_full_combination
                sources = []
                for item in args.source:
                    identifier, separator, number = item.rpartition(":")
                    if not separator:
                        raise ValueError("Each --source must be ASSIGNMENT_ID:VERSION")
                    sources.append((identifier, int(number)))
                _json(stage_full_combination(root, sources, args.out))
            elif args.action == "disposition":
                from .review_full_integrate import record_full_disposition
                _json(record_full_disposition(root, args.id, args.version, args.kind, args.status, args.reason))
            elif args.action == "notes-migrate":
                from .review_notes import migrate_notes
                _json(migrate_notes(catalog.root, apply=args.apply))
            elif args.action == "audit-status":
                from .review_notes import record_audit_status
                _json(record_audit_status(catalog.root, catalog.resolve(args.task),
                                         args.return_id, args.status, args.reason))
            elif args.action == "feedback":
                from .review_assess import record_feedback
                _json(record_feedback(root, args.id, args.version, args.item, args.status, args.reason))
            else:
                _json(review.finish(root, args.id, status=args.status, note=args.note))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"arcpuzzles: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt as exc:
        result = getattr(exc, 'check_result', {})
        if result:
            print('arcpuzzles: check interrupted; completed evidence retained.', file=sys.stderr)
            if result.get('resume_argv') and result.get('child_cleanup', {}).get('session_empty') is True:
                print('Resume: ' + shlex.join(result['resume_argv']), file=sys.stderr)
            else:
                print('Inspect the checkpoint and child liveness before restarting; automatic resume is unavailable.', file=sys.stderr)
        return 128 + getattr(exc, 'signum', signal.SIGINT)


if __name__ == "__main__":
    raise SystemExit(main())
