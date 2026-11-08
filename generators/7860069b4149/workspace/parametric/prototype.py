#!/usr/bin/env python3
"""Proposed episode-fixed trail-policy family for ARC task 7860069b4149.

This is authoring evidence, not an accepted production family.  Every retained
label is executed through the protected Racket bridge.  The Python mirror is an
independent parity diagnostic only.
"""
from __future__ import annotations

from contextlib import nullcontext
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)

TASK_ID = "7860069b4149"
ALLOWED_TRAIL_MODES = ("continuous", "terminal_only")
DEFAULT_TRAIL_MODE = "continuous"
DEFAULT_TRAIN_COUNT = 3
DEFAULT_QUERY_COUNT = 4
PROTOTYPE_VERSION = "1.0.0"
ROOT = find_root(__file__)

_GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

_DEMO_PROFILES = (
    dict(grid_h=9, grid_w=12, anchor_side="left", shape_kind="l3", sweep_steps=4),
    dict(grid_h=11, grid_w=13, anchor_side="right", shape_kind="wide_u", sweep_steps=3),
    dict(grid_h=12, grid_w=10, anchor_side="top", shape_kind="t4", sweep_steps=5),
    dict(grid_h=14, grid_w=15, anchor_side="bottom", shape_kind="hollow_box", sweep_steps=4),
    dict(grid_h=13, grid_w=18, anchor_side="left", shape_kind="zigzag4", sweep_steps=7),
    dict(grid_h=16, grid_w=14, anchor_side="right", shape_kind="l5", sweep_steps=5),
)
_QUERY_PROFILES = (
    dict(grid_h=10, grid_w=14, anchor_side="bottom", shape_kind="l3", sweep_steps=4),
    dict(grid_h=14, grid_w=18, anchor_side="right", shape_kind="wide_u", sweep_steps=6),
    dict(grid_h=20, grid_w=21, anchor_side="top", shape_kind="hollow_box", sweep_steps=8),
    dict(grid_h=30, grid_w=30, anchor_side="left", shape_kind="wide_u", sweep_steps=12),
    dict(grid_h=18, grid_w=22, anchor_side="bottom", shape_kind="t4", sweep_steps=8),
    dict(grid_h=24, grid_w=19, anchor_side="left", shape_kind="l5", sweep_steps=9),
    dict(grid_h=27, grid_w=26, anchor_side="right", shape_kind="zigzag4", sweep_steps=10),
    dict(grid_h=29, grid_w=30, anchor_side="top", shape_kind="wide_u", sweep_steps=12),
)


def _validate_mode(trail_mode: str) -> None:
    if type(trail_mode) is not str or trail_mode not in ALLOWED_TRAIL_MODES:
        raise ValueError(f"trail_mode must be one of {ALLOWED_TRAIL_MODES}, got {trail_mode!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(train_count: int, query_count: int) -> None:
    if type(train_count) is not int:
        raise TypeError("train_count must be an exact integer")
    if type(query_count) is not int:
        raise TypeError("query_count must be an exact integer")
    if not 2 <= train_count <= 6:
        raise ValueError("train_count must be in 2..6")
    if not 1 <= query_count <= 8:
        raise ValueError("query_count must be in 1..8")


def canonical_source(*, root: Path = ROOT) -> str:
    matches = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    matches.append(row)
    if not matches:
        raise ValueError(f"canonical task {TASK_ID} is missing")
    sources = {row.get("program_solution") for row in matches}
    if len(sources) != 1:
        raise ValueError(f"canonical variants for {TASK_ID} disagree")
    source = sources.pop()
    if not isinstance(source, str) or not source.startswith("(rule!"):
        raise ValueError(f"canonical task {TASK_ID} has no exact Racket program")
    return source


def program_for(trail_mode: str = DEFAULT_TRAIL_MODE, *, root: Path = ROOT) -> str:
    """Return exact Racket source for one proposed episode-level policy."""
    _validate_mode(trail_mode)
    source = canonical_source(root=root)
    if trail_mode == DEFAULT_TRAIL_MODE:
        return source
    head = "(let loop ((k 1) (out g))"
    tail = "shifted) out (loop (+ k 1) (paint-cells out shifted color))"
    if source.count(head) != 1 or source.count(tail) != 1:
        raise ValueError("canonical source no longer matches the guarded trail template")
    return source.replace(head, "(let loop ((k 1) (last cells))").replace(
        tail,
        "shifted) (paint-cells g last color) (loop (+ k 1) shifted)",
    )


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        active.define_grid("g", grid)
        return active.eval_text(f"({wrap_rule(program)} g)")
    finally:
        if owns_bridge:
            active.shutdown()


def _facts(grid):
    errors = _GEN.self_check(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] not in (0, 9)]
    anchor = next((r, c) for r in range(height) for c in range(width) if grid[r][c] == 9)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    ar, ac = anchor
    if ac < c0:
        direction, steps = (0, 1), width - 1 - c1
    elif ac > c1:
        direction, steps = (0, -1), c0
    elif ar < r0:
        direction, steps = (1, 0), height - 1 - r1
    else:
        direction, steps = (-1, 0), r0
    return cells, direction, steps, grid[cells[0][0]][cells[0][1]]


def python_output(grid, *, trail_mode: str = DEFAULT_TRAIL_MODE):
    """Independent parity mirror; Racket remains the label authority."""
    _validate_mode(trail_mode)
    if trail_mode == "continuous":
        return _GEN.rule_mirror(grid)
    cells, (dr, dc), steps, color = _facts(grid)
    output = deepcopy(grid)
    for row, col in cells:
        output[row + dr * steps][col + dc * steps] = color
    return output


def grid_sha256(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def normalized_program_sha256(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()


def select_setting(seed: int) -> str:
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:trail-mode:{seed}".encode()).digest()
    return ALLOWED_TRAIL_MODES[digest[0] % len(ALLOWED_TRAIL_MODES)]


def _derived_seed(seed: int, role: str, index: int, attempt: int = 0) -> int:
    payload = f"{TASK_ID}:input:{seed}:{role}:{index}:{attempt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0x7FFFFFFF


def _sample_profile(seed: int, role: str, index: int):
    profiles = _DEMO_PROFILES if role == "demo" else _QUERY_PROFILES
    base = dict(profiles[index % len(profiles)])
    digest = hashlib.sha256(f"{TASK_ID}:profile:{seed}:{role}:{index}".encode()).digest()
    # Keep geometry fixed enough to guarantee the intended hard cases while
    # varying foreground color and placement independently of the hidden rule.
    base["foreground_color"] = 1 + digest[0] % 8
    return base


def _sample_inputs(seed: int, train_count: int, query_count: int):
    rows = []
    seen = set()
    for role, count in (("demo", train_count), ("query", query_count)):
        for index in range(count):
            profile = _sample_profile(seed, role, index)
            for attempt in range(16):
                input_seed = _derived_seed(seed, role, index, attempt)
                grid = _GEN.generate(input_seed, index, **profile)
                digest = grid_sha256(grid)
                if digest in seen:
                    continue
                if python_output(grid, trail_mode="continuous") == python_output(
                    grid, trail_mode="terminal_only"
                ):
                    continue
                seen.add(digest)
                rows.append(
                    {
                        "role": role,
                        "role_index": index,
                        "grid": grid,
                        "input_seed": input_seed,
                        "sample_index": index,
                        "profile": profile,
                        "input_sha256": digest,
                    }
                )
                break
            else:
                raise RuntimeError(f"could not sample a distinct separating {role} input {index}")
    return rows


def make_episode(
    seed: int,
    *,
    trail_mode: str | None = None,
    train_count: int = DEFAULT_TRAIN_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one proposed private episode with all labels executed in Racket."""
    _validate_seed(seed)
    _validate_counts(train_count, query_count)
    selected = select_setting(seed) if trail_mode is None else trail_mode
    _validate_mode(selected)
    rival = next(mode for mode in ALLOWED_TRAIL_MODES if mode != selected)
    samples = _sample_inputs(seed, train_count, query_count)
    programs = {mode: program_for(mode, root=root) for mode in ALLOWED_TRAIL_MODES}
    outputs = {mode: [] for mode in ALLOWED_TRAIL_MODES}

    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        for row in samples:
            for mode in ALLOWED_TRAIL_MODES:
                actual = execute_rule(programs[mode], row["grid"], bridge=active)
                mirror = python_output(row["grid"], trail_mode=mode)
                if actual != mirror:
                    raise AssertionError(f"Racket/Python parity failed for trail_mode={mode}")
                outputs[mode].append(actual)
    finally:
        if owns_bridge:
            active.shutdown()

    pairs = [
        {"input": row["grid"], "output": outputs[selected][index]}
        for index, row in enumerate(samples)
    ]
    demo_mismatches = [
        index for index in range(train_count)
        if outputs[selected][index] != outputs[rival][index]
    ]
    query_mismatches = [
        index for index in range(query_count)
        if outputs[selected][train_count + index] != outputs[rival][train_count + index]
    ]
    if not demo_mismatches:
        raise AssertionError("demonstrations do not identify the selected trail_mode")
    program = programs[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {"trail_mode": selected},
        "seed": seed,
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "normalized_program_sha256": normalized_program_sha256(program),
        "input_provenance": [
            {key: row[key] for key in ("role", "role_index", "input_seed", "sample_index", "profile", "input_sha256")}
            for row in samples
        ],
        "parameter_rivals": [
            {
                "trail_mode": rival,
                "status": "refuted_by_demonstrations",
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        ],
        "ambiguities": [],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return _public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    return _public_challenge_id(episode)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(public_bytes(episode))


def public_query_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Project one visible query per turn without revealing future inputs or count hints."""
    if type(episode) is not dict or type(episode.get("test")) is not list or not episode["test"]:
        raise ValueError("episode must contain at least one query")
    return [
        json.loads(_public_challenge_bytes({"train": episode.get("train"), "test": [pair]}))
        for pair in episode["test"]
    ]


def _json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def write_evidence(
    *,
    seed: int,
    out: str | Path,
    train_count: int = DEFAULT_TRAIN_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write privacy-separated, hash-bound evidence for both settings."""
    _validate_seed(seed)
    _validate_counts(train_count, query_count)
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"output already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))
    try:
        context = nullcontext(bridge) if bridge is not None else RacketBridge()
        with context as active:
            rows = []
            baseline_inputs = None
            for mode in ALLOWED_TRAIL_MODES:
                episode = make_episode(
                    seed,
                    trail_mode=mode,
                    train_count=train_count,
                    query_count=query_count,
                    root=root,
                    bridge=active,
                )
                inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                if baseline_inputs is None:
                    baseline_inputs = inputs
                elif inputs != baseline_inputs:
                    raise AssertionError("trail_mode changed sampled inputs")

                private_rel = Path("private") / f"episode-{mode}.json"
                rule_rel = Path("private/rules") / f"trail-{mode}.rkt"
                visible_id = public_id(episode)
                public_rel = Path("public") / f"challenge-{visible_id}.json"
                _write_bytes(temp / private_rel, _json_bytes(episode))
                _write_bytes(temp / rule_rel, episode["program"].encode())
                _write_bytes(temp / public_rel, public_bytes(episode))
                rows.append(
                    {
                        "trail_mode": mode,
                        "private_path": private_rel.as_posix(),
                        "rule_path": rule_rel.as_posix(),
                        "public_path": public_rel.as_posix(),
                        "public_id": visible_id,
                    }
                )

        report = {
            "schema": "arcpuzzles-parametric-authoring-evidence-v1",
            "task_id": TASK_ID,
            "status": "proposed_unapproved",
            "training_admitted": False,
            "seed": seed,
            "train_count": train_count,
            "query_count": query_count,
            "settings_checked": list(ALLOWED_TRAIL_MODES),
            "generator_sha256": GENERATOR_SHA256,
            "episodes": rows,
        }
        _write_bytes(temp / "report.json", _json_bytes(report))
        files = {}
        for path in sorted(temp.rglob("*")):
            if path.is_file():
                rel = path.relative_to(temp).as_posix()
                files[rel] = _sha256_bytes(path.read_bytes())
        manifest = {
            "schema": "arcpuzzles-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "files": files,
        }
        _write_bytes(temp / "manifest.json", _json_bytes(manifest))
        temp.rename(out)
        return report
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def _safe_evidence_path(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative:
        raise ValueError("evidence path must be a nonempty relative POSIX path")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or rel.as_posix() != relative:
        raise ValueError(f"unsafe evidence path: {relative!r}")
    resolved_root = root.resolve()
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(resolved_root):
        raise ValueError(f"evidence path escapes root: {relative!r}")
    return candidate


def verify_evidence(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("missing manifest.json")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "arcpuzzles-parametric-evidence-manifest-v1":
        raise ValueError("unexpected evidence manifest schema")
    if manifest.get("task_id") != TASK_ID:
        raise ValueError("evidence manifest task mismatch")
    files = manifest.get("files")
    if type(files) is not dict or not files:
        raise ValueError("manifest files must be a nonempty object")

    listed = set(files)
    actual = {
        candidate.relative_to(root).as_posix()
        for candidate in root.rglob("*")
        if candidate.is_file() and candidate != manifest_path
    }
    if actual != listed:
        raise ValueError(
            "manifest file inventory mismatch: "
            f"missing={sorted(actual - listed)}, extra={sorted(listed - actual)}"
        )
    for rel, expected in files.items():
        if type(expected) is not str or len(expected) != 64:
            raise ValueError(f"invalid evidence hash for path: {rel}")
        candidate = _safe_evidence_path(root, rel)
        if not candidate.is_file() or _sha256_bytes(candidate.read_bytes()) != expected:
            raise ValueError(f"evidence hash mismatch: {rel}")

    report = json.loads((root / "report.json").read_text())
    if report.get("schema") != "arcpuzzles-parametric-authoring-evidence-v1":
        raise ValueError("unexpected evidence report schema")
    if report.get("task_id") != TASK_ID:
        raise ValueError("evidence report task mismatch")
    if report.get("generator_sha256") != GENERATOR_SHA256:
        raise ValueError("evidence generator binding is stale or mismatched")
    if report.get("settings_checked") != list(ALLOWED_TRAIL_MODES):
        raise ValueError("report does not cover exact settings")
    train_count = report.get("train_count")
    query_count = report.get("query_count")
    _validate_counts(train_count, query_count)
    episodes = report.get("episodes")
    if type(episodes) is not list:
        raise ValueError("report episodes must be a list")
    modes = [row.get("trail_mode") for row in episodes if type(row) is dict]
    if modes != list(ALLOWED_TRAIL_MODES):
        raise ValueError("report episode rows do not cover exact settings")

    for row in episodes:
        mode = row.get("trail_mode")
        _validate_mode(mode)
        private_rel = row.get("private_path")
        public_rel = row.get("public_path")
        rule_rel = row.get("rule_path")
        if {private_rel, public_rel, rule_rel} - listed:
            raise ValueError(f"episode paths are not bound by manifest: {mode}")
        private_path = _safe_evidence_path(root, private_rel)
        public_path = _safe_evidence_path(root, public_rel)
        rule_path = _safe_evidence_path(root, rule_rel)
        private = json.loads(private_path.read_text())
        if private.get("schema") != "arcpuzzles-proposed-parametric-episode-v1":
            raise ValueError(f"private episode schema mismatch: {mode}")
        if private.get("task_id") != TASK_ID:
            raise ValueError(f"private task mismatch: {mode}")
        if private.get("parameters") != {"trail_mode": mode}:
            raise ValueError(f"private setting mismatch: {mode}")
        if len(private.get("train", [])) != train_count or len(private.get("test", [])) != query_count:
            raise ValueError(f"private count mismatch: {mode}")
        exact_program = program_for(mode)
        if private.get("program") != rule_path.read_text() or private.get("program") != exact_program:
            raise ValueError(f"private program mismatch: {mode}")
        if private.get("program_sha256") != hashlib.sha256(exact_program.encode()).hexdigest():
            raise ValueError(f"private program hash mismatch: {mode}")
        if private.get("normalized_program_sha256") != normalized_program_sha256(exact_program):
            raise ValueError(f"private normalized program hash mismatch: {mode}")
        expected_public = public_bytes(private)
        if public_path.read_bytes() != expected_public:
            raise ValueError(f"public/private projection mismatch: {mode}")
        public = json.loads(expected_public)
        if any("output" in pair for pair in public["test"]):
            raise ValueError("public query answer leaked")
        if public_id(private) != row.get("public_id"):
            raise ValueError(f"public id mismatch: {mode}")
    return {"valid": True, "task_id": TASK_ID, "files_checked": len(files)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    episode = sub.add_parser("episode")
    episode.add_argument("--seed", type=int, required=True)
    episode.add_argument("--mode", choices=ALLOWED_TRAIL_MODES)
    episode.add_argument("--demos", type=int, default=DEFAULT_TRAIN_COUNT)
    episode.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)
    evidence = sub.add_parser("evidence")
    evidence.add_argument("--seed", type=int, required=True)
    evidence.add_argument("--out", required=True)
    evidence.add_argument("--demos", type=int, default=DEFAULT_TRAIN_COUNT)
    evidence.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)
    verify = sub.add_parser("verify")
    verify.add_argument("path")
    args = parser.parse_args(argv)
    if args.command == "episode":
        print(json.dumps(make_episode(args.seed, trail_mode=args.mode, train_count=args.demos, query_count=args.queries), indent=2))
    elif args.command == "evidence":
        print(json.dumps(write_evidence(seed=args.seed, out=args.out, train_count=args.demos, query_count=args.queries), indent=2))
    else:
        print(json.dumps(verify_evidence(args.path), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
