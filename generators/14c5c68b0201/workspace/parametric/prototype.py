#!/usr/bin/env python3
"""Proposed episode-level tiling-axis extension for ARC task 14c5c68b0201.

The selected production generator and canonical Racket authority remain
unchanged.  This task-local prototype varies only which axes receive the
stamp-periodic expansion, with one fixed setting per complete episode.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "14c5c68b0201"
CANONICAL_SHA256 = "fa934e93825cfb3338263045d7d27ce5d7f56f9ced48bbb04d897159bb8a112a"
TILING_AXES = ("both", "horizontal", "vertical")
DEFAULT_TILING_AXES = "both"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_VERSION = "proposed-tiling-axes-v1"
_COUNT_LIMIT = 12

_CANONICAL_PAINT_SITE = "              ((= stamp-val col) (set-cell o r c col))"
_HORIZONTAL_PAINT_SITE = (
    "              ((and (>= r sr1) (<= r sr2)\n"
    "                     (= (cell-at g r (+ sc1 dc)) col))\n"
    "               (set-cell o r c col))"
)
_VERTICAL_PAINT_SITE = (
    "              ((and (>= c sc1) (<= c sc2)\n"
    "                     (= (cell-at g (+ sr1 dr) c) col))\n"
    "               (set-cell o r c col))"
)
_PAINT_SITE_BY_SETTING = {
    "both": _CANONICAL_PAINT_SITE,
    "horizontal": _HORIZONTAL_PAINT_SITE,
    "vertical": _VERTICAL_PAINT_SITE,
}


def sha256(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_setting(tiling_axes: str) -> None:
    if type(tiling_axes) is not str:
        raise TypeError("tiling_axes must be a plain string")
    if tiling_axes not in TILING_AXES:
        raise ValueError(f"tiling_axes must be one of {TILING_AXES}")


def canonical_rule(*, root: Path | str | None = None) -> str:
    """Return the one distinct selected canonical Racket program, hash-pinned."""
    selected_root = ROOT if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str):
                    raise ValueError("canonical row has no Racket program_solution")
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"prototype requires one distinct canonical rule for {TASK_ID}, found {len(sources)}"
        )
    source = sources.pop()
    actual = sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket hash changed: expected {CANONICAL_SHA256}, got {actual}"
        )
    if source.count(_CANONICAL_PAINT_SITE) != 1:
        raise ValueError("canonical tiling paint site is not unique; reassess the prototype")
    if any(source.count(site) for site in (_HORIZONTAL_PAINT_SITE, _VERTICAL_PAINT_SITE)):
        raise ValueError("canonical source unexpectedly contains an alternative paint site")
    return source


def instantiate_rule(
    tiling_axes: str = DEFAULT_TILING_AXES,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact canonical or proposed alternative Racket program."""
    _validate_setting(tiling_axes)
    source = canonical_rule(root=root)
    if tiling_axes == DEFAULT_TILING_AXES:
        return source
    replacement = _PAINT_SITE_BY_SETTING[tiling_axes]
    program = source.replace(_CANONICAL_PAINT_SITE, replacement, 1)
    if program == source:
        raise ValueError("declared tiling-axis substitution did not change the program")
    return program


def restore_canonical(
    program: str,
    *,
    root: Path | str | None = None,
) -> str:
    """Prove that a program differs only at one declared tiling-axis site."""
    if type(program) is not str:
        raise TypeError("program must be Racket source text")
    canonical = canonical_rule(root=root)
    if program == canonical:
        return canonical
    restored = program
    matched = 0
    for setting in TILING_AXES:
        if setting == DEFAULT_TILING_AXES:
            continue
        site = _PAINT_SITE_BY_SETTING[setting]
        count = restored.count(site)
        if count:
            if count != 1:
                raise ValueError("program contains a non-unique alternative tiling paint site")
            restored = restored.replace(site, _CANONICAL_PAINT_SITE, 1)
            matched += 1
    if matched != 1 or restored != canonical or sha256(restored) != CANONICAL_SHA256:
        raise ValueError("program is not one declared tiling_axes variant")
    return restored


def evaluate(bridge: RacketBridge, program: str, grid: Any) -> list[list[int]]:
    """Execute one exact rule through the packet's Racket authority."""
    restore_canonical(program)
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's native Racket lambda")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def grid_sha256(grid: Any) -> str:
    return sha256(json.dumps(normalize_grid(grid), sort_keys=True, separators=(",", ":")))


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a plain Python integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain Python integer")
    if not 1 <= value <= _COUNT_LIMIT:
        raise ValueError(f"{name} must be between 1 and {_COUNT_LIMIT}")


def choose_tiling_axes(seed: int) -> str:
    """Choose one hidden rule setting for the complete episode."""
    _validate_seed(seed)
    return TILING_AXES[seed % len(TILING_AXES)]


def _distinguishes_axis_settings(grid: Any) -> bool:
    scene, errors = GEN._parse_scene(grid)
    if errors or scene is None:
        return False
    for hole in scene["holes"]:
        r1, c1, r2, c2 = hole["bbox"]
        sr1, sc1, sr2, sc2 = hole["stamp_bbox"]
        if not (sr2 - sr1 < r2 - r1 and sc2 - sc1 < c2 - c1):
            return False
    return True


def generate_inputs(
    seed: int,
    *,
    demo_count: int = 3,
    query_count: int = 4,
) -> list[list[list[int]]]:
    """Generate distinct lawful inputs without consulting the hidden setting."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    total = demo_count + query_count
    layout_names = tuple(GEN.LAYOUTS)
    bands = ("easy", "medium", "hard")
    result: list[list[list[int]]] = []
    seen: set[str] = set()
    max_attempts = max(64, total * 8)
    for candidate in range(max_attempts):
        requested = {
            "layout_profile": layout_names[(seed + candidate) % len(layout_names)],
            "motif_index": (seed * 3 + candidate) % len(GEN.MOTIFS),
            "anchor_profile": GEN.ANCHOR_PROFILES[(seed + candidate * 2) % len(GEN.ANCHOR_PROFILES)],
            "palette_band": GEN.PALETTE_BANDS[(seed + candidate) % len(GEN.PALETTE_BANDS)],
            "background_color": GEN.BACKGROUND_COLORS[(seed // 2 + candidate) % len(GEN.BACKGROUND_COLORS)],
        }
        grid = GEN.generate(
            1_405_000 + seed * 10_007 + candidate,
            seed * 101 + candidate,
            difficulty=bands[(seed + candidate) % len(bands)],
            **requested,
        )
        errors = GEN.self_check(grid)
        if errors:
            raise RuntimeError("selected generator returned an unlawful input: " + "; ".join(errors))
        if not _distinguishes_axis_settings(grid):
            continue
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        result.append(grid)
        if len(result) == total:
            return result
    raise RuntimeError(
        f"could not obtain {total} distinct axis-distinguishing inputs in {max_attempts} attempts"
    )


def make_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    tiling_axes: str | None = None,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private episode; every label comes from its matching Racket rule."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    chosen = choose_tiling_axes(seed) if tiling_axes is None else tiling_axes
    _validate_setting(chosen)
    program = instantiate_rule(chosen)
    inputs = generate_inputs(seed, demo_count=demo_count, query_count=query_count)
    pairs = []
    for grid in inputs:
        output = evaluate(bridge, program, grid)
        pairs.append(
            {
                "input": grid,
                "output": output,
                "input_sha256": grid_sha256(grid),
                "output_sha256": grid_sha256(output),
            }
        )
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": {"tiling_axes": chosen},
        "parameter_choice": "seed_modulo_three" if tiling_axes is None else "explicit_once_per_episode",
        "allowed_tiling_axes": list(TILING_AXES),
        "canonical_default": DEFAULT_TILING_AXES,
        "demo_count": demo_count,
        "query_count": query_count,
        "racket_program": program,
        "racket_sha256": sha256(program),
        "canonical_sha256": CANONICAL_SHA256,
        "generator_path": str(GENERATOR_PATH),
        "generator_sha256": GENERATOR_SHA256,
        "prototype_sha256": sha256(Path(__file__).read_bytes()),
        "input_constraint": (
            "every stamp bounding box is strictly smaller than its hole on both axes, "
            "so both, horizontal, and vertical tiling yield distinct outputs"
        ),
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
    }


def _episode_pairs(episode: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    if len(train) != episode.get("demo_count") or len(test) != episode.get("query_count"):
        raise ValueError("episode pair counts do not match demo_count/query_count")
    for pair in train + test:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            raise ValueError("private episode pairs require input and output")
    return train, test


def analyze_episode(bridge: RacketBridge, episode: dict[str, Any]) -> dict[str, Any]:
    """Check labels and whether demonstrations alone refute every declared rival."""
    train, test = _episode_pairs(episode)
    parameters = episode.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("episode parameters are missing")
    selected = parameters.get("tiling_axes")
    _validate_setting(selected)
    selected_program = instantiate_rule(selected)
    if episode.get("racket_program") != selected_program:
        raise ValueError("episode Racket source does not match its selected setting")

    pairs = train + test
    selected_outputs = []
    for pair in pairs:
        actual = evaluate(bridge, selected_program, pair["input"])
        if actual != pair["output"]:
            raise ValueError("stored episode label does not match selected Racket rule")
        selected_outputs.append(actual)

    rival_predictions: dict[str, list[list[list[int]]]] = {}
    refuting_demos: dict[str, list[int]] = {}
    for rival in TILING_AXES:
        if rival == selected:
            continue
        predictions = [evaluate(bridge, instantiate_rule(rival), pair["input"]) for pair in pairs]
        rival_predictions[rival] = predictions
        refuting_demos[rival] = [
            index
            for index, prediction in enumerate(predictions[: len(train)])
            if prediction != selected_outputs[index]
        ]

    query_rows = []
    ambiguous = 0
    nondistinguishing = 0
    for query_index in range(len(test)):
        absolute = len(train) + query_index
        rivals = []
        for rival in TILING_AXES:
            if rival == selected:
                continue
            query_differs = rival_predictions[rival][absolute] != selected_outputs[absolute]
            demos = refuting_demos[rival]
            if not demos:
                status = "ambiguous_from_demonstrations" if query_differs else "matches_query"
                ambiguous += int(query_differs)
            elif not query_differs:
                status = "refuted_but_query_not_distinguishing"
                nondistinguishing += 1
            else:
                status = "refuted_by_demonstrations"
            rivals.append(
                {
                    "tiling_axes": rival,
                    "racket_sha256": sha256(instantiate_rule(rival)),
                    "refuting_demonstration_indices": demos,
                    "query_differs": query_differs,
                    "status": status,
                }
            )
        query_rows.append({"query_index": query_index, "rivals": rivals})

    status = (
        "no_ambiguity_found"
        if ambiguous == 0 and nondistinguishing == 0
        else "ambiguity_or_nondistinguishing_query_found"
    )
    return {
        "status": status,
        "selected_tiling_axes": selected,
        "queries": query_rows,
        "ambiguous_rival_queries": ambiguous,
        "nondistinguishing_rival_queries": nondistinguishing,
        "racket_evaluations": len(pairs) * len(TILING_AXES),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project only visible demonstrations and answer-masked query inputs."""
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode/challenge must contain train and test lists")
    return deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in train
            ],
            "test": [{"input": pair["input"]} for pair in test],
        }
    )


def public_filename(episode_or_challenge: dict[str, Any]) -> str:
    challenge = public_challenge(episode_or_challenge)
    return f"challenge-{public_challenge_id(challenge)}.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _relative_file_receipts(out: Path) -> dict[str, str]:
    receipts: dict[str, str] = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "report.json":
            receipts[str(path.relative_to(out))] = sha256(path.read_bytes())
    return receipts


def _source_hashes(*, root: Path) -> dict[str, str]:
    test_path = root / "generators" / TASK_ID / "tests" / "test_parametric_tiling_axes.py"
    return {
        "prototype.py": sha256(Path(__file__).read_bytes()),
        "test_parametric_tiling_axes.py": sha256(test_path.read_bytes()),
        "generator.py": sha256(Path(GENERATOR_PATH).read_bytes()),
        "canonical_racket": sha256(canonical_rule(root=root)),
    }


def materialize(
    out: Path | str,
    *,
    seed: int = 0,
    demo_count: int = 3,
    query_count: int = 4,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Write three source-bound episodes, one per declared setting, to a new tree."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    selected_root = ROOT if root is None else Path(root).resolve()
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)

    report: dict[str, Any] = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "started",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": "tiling_axes",
            "allowed_values": list(TILING_AXES),
            "original_default": DEFAULT_TILING_AXES,
            "selection_scope": "once_per_episode",
            "input_constraints": (
                "stamp bounding box is strictly smaller than its containing hole "
                "on both axes; the same inputs are legal for every setting"
            ),
        },
        "seed": seed,
        "demo_count": demo_count,
        "query_count": query_count,
        "sources": _source_hashes(root=selected_root),
        "runtime": racket_runtime_status(),
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
        "episodes": [],
        "canonical_checks": [],
        "limitations": [
            "Proposed task-local prototype only; no production API, canonical authority, approval, or training-admission change.",
            "Evidence covers three retained episodes and the recorded deterministic input schedule, not every seed or conceivable rival.",
            "Rival checks cover only the declared both/horizontal/vertical settings.",
            "The selected generator's pre-existing pytest wrapper is unavailable in this packet because scripts.canonical_profile_gate is absent; task-local tests use shipped reviewer_support instead.",
        ],
    }

    task_dir = selected_root / "generators" / TASK_ID
    snapshots = {
        "prototype.py": Path(__file__),
        "test_parametric_tiling_axes.py": task_dir / "tests" / "test_parametric_tiling_axes.py",
        "generator.py": task_dir / "generator.py",
    }
    for name, source_path in snapshots.items():
        destination = out / "private" / "source_snapshot" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)

    programs = {setting: instantiate_rule(setting, root=selected_root) for setting in TILING_AXES}
    for setting, program in programs.items():
        _write_text(out / "private" / "rules" / f"{setting}.rkt", program)

    canonical_program = programs[DEFAULT_TILING_AXES]
    episode_rows: list[dict[str, Any]] = []
    all_analyses: list[dict[str, Any]] = []
    pending_episodes: list[dict[str, Any]] = []
    try:
        with RacketBridge(max_calls_before_restart=256) as bridge:
            for index, pair in enumerate(
                canonical_pairs(TASK_ID, root=selected_root, labeled_only=True)
            ):
                actual = evaluate(bridge, canonical_program, pair["input"])
                if actual != pair["output"]:
                    raise AssertionError(f"canonical Racket mismatch at labeled pair {index}")
                report["canonical_checks"].append(
                    {
                        "pair_index": index,
                        "input_sha256": grid_sha256(pair["input"]),
                        "output_sha256": grid_sha256(pair["output"]),
                    }
                )

            for index, setting in enumerate(TILING_AXES):
                episode_seed = seed + index
                episode = make_episode(
                    bridge,
                    episode_seed,
                    tiling_axes=setting,
                    demo_count=demo_count,
                    query_count=query_count,
                )
                analysis = analyze_episode(bridge, episode)
                if analysis["status"] != "no_ambiguity_found":
                    raise AssertionError(
                        f"episode {index} did not identify {setting}: {analysis['status']}"
                    )
                challenge = public_challenge(episode)
                public_bytes = public_challenge_bytes(challenge)
                pending_episodes.append(
                    {
                        "seed": episode_seed,
                        "tiling_axes": setting,
                        "episode": episode,
                        "analysis": analysis,
                        "public_bytes": public_bytes,
                        "public_id": public_challenge_id(challenge),
                    }
                )

            seen_public_payloads: set[bytes] = set()
            public_payload_by_id: dict[str, bytes] = {}
            for pending in pending_episodes:
                public_bytes = pending["public_bytes"]
                public_id = pending["public_id"]
                if public_bytes in seen_public_payloads:
                    raise ValueError(f"duplicate public challenge payload: {public_id}")
                seen_public_payloads.add(public_bytes)
                prior = public_payload_by_id.get(public_id)
                if prior is not None:
                    raise ValueError(f"public identifier collision: {public_id}")
                public_payload_by_id[public_id] = public_bytes

            pending_episodes.sort(key=lambda row: row["public_id"])
            for index, pending in enumerate(pending_episodes):
                setting = pending["tiling_axes"]
                episode = pending["episode"]
                analysis = pending["analysis"]
                public_id = pending["public_id"]
                public_bytes = pending["public_bytes"]
                private_rel = f"private/episodes/episode-{index:03d}.json"
                analysis_rel = f"private/analyses/episode-{index:03d}.json"
                public_rel = f"public/challenge-{public_id}.json"
                _write_json(out / private_rel, episode)
                _write_json(out / analysis_rel, analysis)
                public_path = out / public_rel
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(public_bytes)
                row = {
                    "index": index,
                    "seed": pending["seed"],
                    "tiling_axes": setting,
                    "private_path": private_rel,
                    "analysis_path": analysis_rel,
                    "public_path": public_rel,
                    "public_id": public_id,
                    "rule_path": f"private/rules/{setting}.rkt",
                    "episode_sha256": sha256(
                        json.dumps(episode, sort_keys=True, separators=(",", ":"))
                    ),
                    "public_sha256": sha256(public_bytes),
                    "racket_sha256": sha256(programs[setting]),
                }
                episode_rows.append(row)
                all_analyses.append(analysis)

            witness_input = pending_episodes[0]["episode"]["train"][0]["input"]
            witness_outputs = {
                setting: evaluate(bridge, program, witness_input)
                for setting, program in programs.items()
            }
            witness_hashes = {
                setting: grid_sha256(output) for setting, output in witness_outputs.items()
            }
            if len(set(witness_hashes.values())) != len(TILING_AXES):
                raise AssertionError("retained setting-difference witness is not distinguishing")
            report["setting_difference_witness"] = {
                "input_sha256": grid_sha256(witness_input),
                "output_sha256_by_tiling_axes": witness_hashes,
            }
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["files"] = _relative_file_receipts(out)
        _write_json(out / "report.json", report)
        raise

    report["episodes"] = episode_rows
    query_ambiguities = sum(row["ambiguous_rival_queries"] for row in all_analyses)
    nondistinguishing = sum(
        row["nondistinguishing_rival_queries"] for row in all_analyses
    )
    report["counts"] = {
        "episodes": len(episode_rows),
        "demonstrations": len(episode_rows) * demo_count,
        "queries": len(episode_rows) * query_count,
        "canonical_labels_passed": len(report["canonical_checks"]),
        "query_ambiguities": query_ambiguities,
        "nondistinguishing_rival_queries": nondistinguishing,
        "settings_seen": list(TILING_AXES),
        "distinct_public_challenges": len({row["public_sha256"] for row in episode_rows}),
    }
    report["status"] = (
        "no_ambiguity_found"
        if query_ambiguities == 0
        and nondistinguishing == 0
        and len(episode_rows) == len(TILING_AXES)
        else "failed"
    )
    report["files"] = _relative_file_receipts(out)
    _write_json(out / "report.json", report)
    return report


def verify_tree(
    out: Path | str,
    *,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Replay a materialized tree and reject byte, projection, source, or label drift."""
    out = Path(out).resolve()
    selected_root = ROOT if root is None else Path(root).resolve()
    errors: list[str] = []
    report_path = out / "report.json"
    if not report_path.is_file():
        return {"status": "failed", "errors": [f"missing report: {report_path}"]}
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "failed", "errors": [f"invalid report JSON: {exc}"]}

    if report.get("status") != "no_ambiguity_found":
        errors.append(f"materialized report status is {report.get('status')!r}")

    expected_sources = _source_hashes(root=selected_root)
    if report.get("sources") != expected_sources:
        errors.append("source hash map does not match current prototype/test/generator/canonical rule")

    receipts = report.get("files")
    if not isinstance(receipts, dict):
        errors.append("report file receipts are missing")
        receipts = {}
    for relative, expected_hash in receipts.items():
        path = (out / relative).resolve()
        try:
            if not path.is_relative_to(out):
                errors.append(f"unsafe receipt path: {relative}")
                continue
        except AttributeError:
            if out not in path.parents and path != out:
                errors.append(f"unsafe receipt path: {relative}")
                continue
        if not path.is_file():
            errors.append(f"missing retained file: {relative}")
            continue
        actual_hash = sha256(path.read_bytes())
        if actual_hash != expected_hash:
            errors.append(f"file hash mismatch: {relative}")

    episode_rows = report.get("episodes")
    if not isinstance(episode_rows, list) or len(episode_rows) != len(TILING_AXES):
        errors.append("report must retain exactly one episode per tiling_axes setting")
        episode_rows = []

    try:
        with RacketBridge(max_calls_before_restart=256) as bridge:
            canonical_program = instantiate_rule(DEFAULT_TILING_AXES, root=selected_root)
            canonical_count = 0
            for index, pair in enumerate(
                canonical_pairs(TASK_ID, root=selected_root, labeled_only=True)
            ):
                canonical_count += 1
                if evaluate(bridge, canonical_program, pair["input"]) != pair["output"]:
                    errors.append(f"canonical Racket replay mismatch at pair {index}")

            seen_settings: set[str] = set()
            for row in episode_rows:
                try:
                    private_path = (out / row["private_path"]).resolve()
                    public_path = (out / row["public_path"]).resolve()
                    analysis_path = (out / row["analysis_path"]).resolve()
                    rule_path = (out / row["rule_path"]).resolve()
                    for kind, path in (
                        ("private", private_path),
                        ("public", public_path),
                        ("analysis", analysis_path),
                        ("rule", rule_path),
                    ):
                        if not path.is_relative_to(out):
                            raise ValueError(f"unsafe {kind} path {path}")
                    episode = json.loads(private_path.read_text(encoding="utf-8"))
                    public = json.loads(public_path.read_text(encoding="utf-8"))
                    retained_analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
                    setting = episode["parameters"]["tiling_axes"]
                    seen_settings.add(setting)
                    if setting != row.get("tiling_axes"):
                        errors.append(f"episode setting mismatch for {row.get('private_path')}")
                    expected_program = instantiate_rule(setting, root=selected_root)
                    if rule_path.read_text(encoding="utf-8") != expected_program:
                        errors.append(f"Racket rule mismatch for setting {setting}")
                    projected = public_challenge(episode)
                    if public != projected:
                        errors.append(f"public/private projection mismatch: {row.get('public_path')}")
                    if public_path.read_bytes() != public_challenge_bytes(projected):
                        errors.append(f"public bytes are not canonical: {row.get('public_path')}")
                    if public_path.name != public_filename(projected):
                        errors.append(f"public filename/content mismatch: {row.get('public_path')}")
                    replay_analysis = analyze_episode(bridge, episode)
                    if replay_analysis != retained_analysis:
                        errors.append(f"analysis replay mismatch: {row.get('analysis_path')}")
                    if replay_analysis["status"] != "no_ambiguity_found":
                        errors.append(f"episode ambiguity on replay: {row.get('private_path')}")
                except Exception as exc:
                    errors.append(
                        f"episode verification failed for {row.get('private_path', '<unknown>')}: "
                        f"{type(exc).__name__}: {exc}"
                    )
            if seen_settings != set(TILING_AXES):
                errors.append(
                    f"settings seen {sorted(seen_settings)} do not match {list(TILING_AXES)}"
                )
            if canonical_count != 8:
                errors.append(f"expected 8 labeled canonical pairs, found {canonical_count}")
    except Exception as exc:
        errors.append(f"Racket replay failed: {type(exc).__name__}: {exc}")

    return {
        "status": "pass" if not errors else "failed",
        "errors": errors,
        "checked_files": len(receipts),
        "checked_episodes": len(episode_rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize_parser = subparsers.add_parser("materialize", help="write new evidence")
    materialize_parser.add_argument("--out", type=Path, required=True)
    materialize_parser.add_argument("--seed", type=int, default=0)
    materialize_parser.add_argument("--demos", type=int, default=3)
    materialize_parser.add_argument("--queries", type=int, default=4)

    verify_parser = subparsers.add_parser("verify", help="replay retained evidence")
    verify_parser.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "materialize":
        report = materialize(
            args.out,
            seed=args.seed,
            demo_count=args.demos,
            query_count=args.queries,
        )
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "counts": report["counts"],
                    "report": str(Path(args.out).resolve() / "report.json"),
                },
                sort_keys=True,
            )
        )
        return 0 if report["status"] == "no_ambiguity_found" else 1

    verification = verify_tree(args.out)
    print(json.dumps(verification, sort_keys=True))
    return 0 if verification["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
