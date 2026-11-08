#!/usr/bin/env python3
"""Unapproved episode-level ``alignment_scope`` prototype for b8d6fabb411e.

The selected canonical generator and Racket authority remain fixed.  This
module instantiates two nearby rules from the exact selected source:

``span`` (canonical/default)
    Connect a marker whenever its row/column lies anywhere in the square span.
``boundary`` (proposed alternative)
    Connect only markers on the square's two boundary rows or columns.

The hidden setting is chosen once per episode.  Inputs are setting-independent,
side-four members of the selected generator family containing both interior-
aligned and boundary-aligned firing markers, so demonstrations distinguish the
settings before the query.  Retained labels are produced by the bundled Racket
runtime, with a Python mirror used only as a parity check.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "b8d6fabb411e"
SCHEMA = "b8d6fabb411e-alignment-scope-prototype-v1"
PARAMETER_NAME = "alignment_scope"
SETTINGS = ("span", "boundary")
DEFAULT_SETTING = "span"
N_TRAIN = 3
N_TEST = 1
_FIXTURE_PROFILES = (
    "canonical_four",
    "color_control_three",
    "canonical_four",
    "color_control_three",
)

# These four exact substrings are deliberately narrow edit guards.  The
# canonical source contains two horizontal and two vertical span predicates.
ROW_SPAN_SITE = "(and (>= pr tr1) (<= pr tr2)"
ROW_BOUNDARY_SITE = "(and (or (= pr tr1) (= pr tr2))"
COL_SPAN_SITE = "(and (>= pc tc1) (<= pc tc2)"
COL_BOUNDARY_SITE = "(and (or (= pc tc1) (= pc tc2))"

PARAMETERS = {
    PARAMETER_NAME: {
        "allowed": list(SETTINGS),
        "default": DEFAULT_SETTING,
        "meaning": (
            "Whether a singleton marker fires from any row/column inside the "
            "solid square's span, or only from its two boundary rows/columns."
        ),
        "invariants": [
            "identify the one solid color-3 square",
            "preserve square, singleton markers, and diagonal decoys",
            "draw each firing marker's color through the gap to the nearest square edge",
        ],
        "input_constraints": (
            "Lawful selected-generator inputs with square side at least 3. "
            "Retained fixtures use side 4 and contain both an interior-aligned "
            "marker and a boundary-aligned firing marker, so both settings are "
            "nontrivial and produce different outputs."
        ),
    }
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def normalized_rule_hash(text: str) -> str:
    return sha256_text(" ".join(text.split()))[:12]


def json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256_bytes(payload)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative plain Python integer")
    return seed


def _validate_setting(alignment_scope: Any) -> str:
    if type(alignment_scope) is not str or alignment_scope not in SETTINGS:
        raise ValueError(f"alignment_scope must be one of {SETTINGS}")
    return alignment_scope


def root_path(root: str | Path | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def load_generator(*, root: str | Path | None = None):
    return load_selected_generator(TASK_ID, root=root_path(root))


def canonical_program(*, root: str | Path | None = None) -> str:
    """Read the one selected canonical program and guard every edit site."""
    programs: list[str] = []
    with canonical_path(root_path(root)).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                programs.append(row["program_solution"])
    programs = list(dict.fromkeys(programs))
    if len(programs) != 1:
        raise ValueError(
            f"expected one selected canonical program for {TASK_ID}, found {len(programs)}"
        )
    source = programs[0]
    expected_counts = {
        ROW_SPAN_SITE: 2,
        COL_SPAN_SITE: 2,
        ROW_BOUNDARY_SITE: 0,
        COL_BOUNDARY_SITE: 0,
    }
    observed = {site: source.count(site) for site in expected_counts}
    if observed != expected_counts:
        raise ValueError(
            "canonical alignment predicates drifted; refusing broad rewrite: "
            f"expected {expected_counts}, observed {observed}"
        )
    return source


def render_program(
    alignment_scope: str = DEFAULT_SETTING,
    *,
    root: str | Path | None = None,
) -> str:
    """Instantiate exact Racket; ``span`` is byte-identical to authority."""
    alignment_scope = _validate_setting(alignment_scope)
    source = canonical_program(root=root)
    if alignment_scope == DEFAULT_SETTING:
        return source
    changed = source.replace(ROW_SPAN_SITE, ROW_BOUNDARY_SITE)
    changed = changed.replace(COL_SPAN_SITE, COL_BOUNDARY_SITE)
    expected = {
        ROW_SPAN_SITE: 0,
        COL_SPAN_SITE: 0,
        ROW_BOUNDARY_SITE: 2,
        COL_BOUNDARY_SITE: 2,
    }
    observed = {site: changed.count(site) for site in expected}
    if changed == source or observed != expected:
        raise AssertionError(
            "failed to instantiate guarded boundary-only alignment rule: "
            f"expected {expected}, observed {observed}"
        )
    return changed


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule exactly once for one complete episode."""
    _validate_seed(seed)
    return {PARAMETER_NAME: SETTINGS[seed % len(SETTINGS)]}


def python_reference(
    grid: list[list[int]],
    alignment_scope: str = DEFAULT_SETTING,
    *,
    root: str | Path | None = None,
) -> list[list[int]]:
    """Task-local mirror used only to cross-check real Racket execution."""
    alignment_scope = _validate_setting(alignment_scope)
    generator, _source, _digest = load_generator(root=root)
    normalized = normalize_grid(grid)
    errors = generator.self_check(normalized)
    if errors:
        raise ValueError("input is outside selected task grammar: " + "; ".join(errors))
    return normalize_grid(
        generator._expected_output(
            normalized, boundary_only=alignment_scope == "boundary"
        )
    )


def fixture_inputs(
    seed: int,
    *,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Build four lawful, setting-independent, separating side-four inputs."""
    _validate_seed(seed)
    generator, _source, _digest = load_generator(root=root)
    rng = random.Random(seed ^ 0xB8D6FABB411E)
    grids: list[list[list[int]]] = []
    diagnostics: list[dict[str, Any]] = []

    for fixture_index, profile in enumerate(_FIXTURE_PROFILES):
        accepted = None
        for attempt in range(4096):
            draw_seed = rng.randrange(1 << 63)
            sample_index = fixture_index * 4096 + attempt
            grid = generator.generate(
                draw_seed,
                sample_index,
                difficulty="hard",
                layout="large_16x18",
                scene_profile=profile,
            )
            analysis = generator._analyze(grid)
            span = generator._expected_output(grid)
            boundary = generator._expected_output(grid, boundary_only=True)
            if (
                not analysis["errors"]
                and analysis["square_side"] == 4
                and analysis["interior_span"]
                and span != boundary
                and boundary != grid
            ):
                accepted = normalize_grid(grid)
                diagnostics.append(
                    {
                        "fixture_index": fixture_index,
                        "profile": profile,
                        "draw_seed": draw_seed,
                        "sample_index": sample_index,
                        "interior_marker_count": len(analysis["interior_span"]),
                    }
                )
                break
        if accepted is None:
            raise RuntimeError(
                f"could not find a separating side-four fixture for {profile!r} "
                "within 4096 deterministic attempts"
            )
        grids.append(accepted)

    if len({json_sha256(grid) for grid in grids}) != len(grids):
        raise RuntimeError(f"fixture construction produced duplicates: {diagnostics}")
    return grids


def fixture_metadata(
    grids: list[list[list[int]]],
    *,
    root: str | Path | None = None,
) -> list[dict[str, Any]]:
    generator, _source, _digest = load_generator(root=root)
    rows = []
    for index, grid in enumerate(grids):
        analysis = generator._analyze(grid)
        span = generator._expected_output(grid)
        boundary = generator._expected_output(grid, boundary_only=True)
        r1, c1, r2, c2 = analysis["square"]
        boundary_markers = [
            [r, c, color, direction]
            for r, c, color, direction in analysis["aligned"]
            if (
                direction in {"left", "right"} and r in {r1, r2}
            ) or (
                direction in {"top", "bottom"} and c in {c1, c2}
            )
        ]
        rows.append(
            {
                "index": index,
                "input_sha256": json_sha256(grid),
                "shape": [len(grid), len(grid[0])],
                "square_bbox": [r1, c1, r2, c2],
                "square_side": analysis["square_side"],
                "scene_profile": generator.observe_overrides(grid)["scene_profile"],
                "interior_aligned_markers": [list(row) for row in analysis["interior_span"]],
                "boundary_aligned_markers": boundary_markers,
                "span_output_sha256": json_sha256(span),
                "boundary_output_sha256": json_sha256(boundary),
                "settings_differ": span != boundary,
                "boundary_nonidentity": boundary != grid,
            }
        )
    return rows


def _racket_datum(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in normalized
    ) + ")"


def _execute_with_bridge(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    function = strip_rule_wrapper(program)
    if not function.lstrip().startswith("(lambda"):
        raise ValueError("expected canonical rule! wrapper around a lambda")
    expression = f"({function} '{_racket_datum(grid)})"
    return normalize_grid(bridge.eval_text(expression))


def racket_outputs(
    grids: list[list[list[int]]],
    *,
    alignment_scope: str = DEFAULT_SETTING,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> list[list[list[int]]]:
    alignment_scope = _validate_setting(alignment_scope)
    program = render_program(alignment_scope, root=root)
    if bridge is not None:
        return [_execute_with_bridge(bridge, program, grid) for grid in grids]
    with RacketBridge() as owned_bridge:
        return [
            _execute_with_bridge(owned_bridge, program, grid)
            for grid in grids
        ]


def racket_outputs_all(
    grids: list[list[list[int]]],
    *,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, list[list[list[int]]]]:
    if bridge is not None:
        return {
            setting: racket_outputs(
                grids,
                alignment_scope=setting,
                root=root,
                bridge=bridge,
            )
            for setting in SETTINGS
        }
    with RacketBridge() as owned_bridge:
        return racket_outputs_all(grids, root=root, bridge=owned_bridge)


def verify_canonical_default(
    *,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Verify all supplied labels and expose the canonical boundary shortcut."""
    root = root_path(root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return verify_canonical_default(root=root, bridge=owned_bridge)

    span_program = render_program("span", root=root)
    boundary_program = render_program("boundary", root=root)
    details = []
    for pair in pairs:
        span = _execute_with_bridge(bridge, span_program, pair["input"])
        boundary = _execute_with_bridge(bridge, boundary_program, pair["input"])
        expected = pair["output"]
        py_span = python_reference(pair["input"], "span", root=root)
        py_boundary = python_reference(pair["input"], "boundary", root=root)
        details.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": json_sha256(pair["input"]),
                "expected_output_sha256": json_sha256(expected),
                "span_matches": span == expected,
                "boundary_shortcut_matches": boundary == expected,
                "span_python_parity": span == py_span,
                "boundary_python_parity": boundary == py_boundary,
            }
        )
    return {
        "pairs_checked": len(details),
        "all_match": bool(details) and all(row["span_matches"] for row in details),
        "python_parity": bool(details) and all(
            row["span_python_parity"] and row["boundary_python_parity"]
            for row in details
        ),
        "boundary_shortcut_fits_all_canonical_pairs": bool(details) and all(
            row["boundary_shortcut_matches"] for row in details
        ),
        "details": details,
    }


def _pair_rows(
    grids: list[list[list[int]]],
    outputs: list[list[list[int]]],
) -> list[dict[str, Any]]:
    return [
        {
            "input": deepcopy(grid),
            "output": deepcopy(output),
            "input_sha256": json_sha256(grid),
            "output_sha256": json_sha256(output),
        }
        for grid, output in zip(grids, outputs)
    ]


def build_episode(
    seed: int,
    bridge: RacketBridge | None = None,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Build one three-demo/one-query private episode from Racket labels."""
    _validate_seed(seed)
    parameters = choose_parameters(seed)
    selected_setting = parameters[PARAMETER_NAME]
    rival_setting = next(setting for setting in SETTINGS if setting != selected_setting)
    grids = fixture_inputs(seed, root=root)
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return build_episode(seed, owned_bridge, root=root)

    outputs = racket_outputs_all(grids, root=root, bridge=bridge)
    for setting in SETTINGS:
        python_outputs = [
            python_reference(grid, setting, root=root) for grid in grids
        ]
        if outputs[setting] != python_outputs:
            raise RuntimeError(f"Racket/Python parity failed for {setting!r}")

    selected = outputs[selected_setting]
    rival = outputs[rival_setting]
    refuting = [index for index in range(N_TRAIN) if selected[index] != rival[index]]
    query_differs = selected[N_TRAIN] != rival[N_TRAIN]
    if not refuting:
        raise RuntimeError("demonstrations fail to identify alignment_scope")
    if not query_differs:
        raise RuntimeError("retained query does not exercise alignment_scope")

    pairs = _pair_rows(grids, selected)
    program = render_program(selected_setting, root=root)
    rival_program = render_program(rival_setting, root=root)
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype_status": "unapproved",
        "seed": seed,
        "parameters": parameters,
        "parameter_choice": "deterministic_once_per_episode",
        "parameter_draw_count": 1,
        "canonical_default": selected_setting == DEFAULT_SETTING,
        "program": program,
        "program_sha256": sha256_text(program),
        "program_normalized_hash_12": normalized_rule_hash(program),
        "fixture_metadata": fixture_metadata(grids, root=root),
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "rival": {
            "parameters": {PARAMETER_NAME: rival_setting},
            "program_sha256": sha256_text(rival_program),
            "program_normalized_hash_12": normalized_rule_hash(rival_program),
            "refuting_demonstration_indices": refuting,
            "query_differs": query_differs,
        },
    }


def public_filename(challenge):
    """Name only visible examples, never settings, seeds or query answers."""
    demos = challenge.get("train", challenge.get("demos"))
    queries = challenge.get("test", challenge.get("query"))
    if isinstance(queries, dict): queries = [queries]
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in demos],
               "test": [{"input": p["input"]} for p in queries]}
    digest = hashlib.sha256(json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return "challenge-" + digest + ".json"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden setting, source, seed, hashes, rivals, and query labels."""
    public = {
        "schema": "arc-parametric-challenge-v1",
        "task_id": episode["task_id"],
        "episode_id": "",
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
    }
    for pair in public["train"] + public["test"]:
        pair.pop("input_sha256", None)
        pair.pop("output_sha256", None)
    for pair in public["test"]:
        pair.pop("output", None)
    public["episode_id"] = public_filename(public).removeprefix("challenge-").removesuffix(".json")
    return public


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _manifest_rows(out_dir: Path, paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(paths):
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(out_dir).as_posix(),
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    return rows


def build_evidence(
    seed: int,
    out_dir: str | Path,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Execute both settings and write a source-bound, self-hashing bundle."""
    _validate_seed(seed)
    out_dir = Path(out_dir).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"output directory is not empty: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    root = root_path(root)
    generator, generator_path, generator_sha = load_generator(root=root)
    canonical = canonical_program(root=root)
    if render_program(DEFAULT_SETTING, root=root) != canonical:
        raise AssertionError("canonical-default source is not byte-identical")
    if normalized_rule_hash(canonical) != generator.RULE_HASH:
        raise AssertionError(
            "canonical program hash no longer matches selected generator RULE_HASH"
        )

    setting_seeds: dict[str, int] = {}
    candidate = seed
    while len(setting_seeds) < len(SETTINGS):
        setting = choose_parameters(candidate)[PARAMETER_NAME]
        setting_seeds.setdefault(setting, candidate)
        candidate += 1

    with RacketBridge() as bridge:
        episodes = {
            setting: build_episode(setting_seed, bridge, root=root)
            for setting, setting_seed in setting_seeds.items()
        }
        canonical_report = verify_canonical_default(root=root, bridge=bridge)
        witness_grid = fixture_inputs(seed, root=root)[0]
        witness_outputs = racket_outputs_all(
            [witness_grid], root=root, bridge=bridge
        )
        witness_outputs = {
            setting: outputs[0] for setting, outputs in witness_outputs.items()
        }

    if not canonical_report["all_match"] or not canonical_report["python_parity"]:
        raise RuntimeError("canonical default verification failed")
    if witness_outputs["span"] == witness_outputs["boundary"]:
        raise RuntimeError("setting-difference witness is not distinguishing")

    created: list[Path] = []
    for setting in SETTINGS:
        rule_path = out_dir / "rules" / f"{setting}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(render_program(setting, root=root), encoding="utf-8")
        created.append(rule_path)

        private_path = out_dir / "private" / f"episode_{setting}.json"
        public_path = out_dir / "public" / public_filename(public_challenge(episodes[setting]))
        _write_json(private_path, episodes[setting])
        _write_json(public_path, public_challenge(episodes[setting]))
        created.extend((private_path, public_path))

    canonical_path_out = out_dir / "canonical_default_report.json"
    _write_json(canonical_path_out, canonical_report)
    created.append(canonical_path_out)

    witness_path = out_dir / "setting_difference_witness.json"
    witness_record = {
        "task_id": TASK_ID,
        "input": witness_grid,
        "input_sha256": json_sha256(witness_grid),
        "outputs": witness_outputs,
        "output_sha256": {
            setting: json_sha256(output)
            for setting, output in witness_outputs.items()
        },
        "program_sha256": {
            setting: sha256_text(render_program(setting, root=root))
            for setting in SETTINGS
        },
        "differing_cells": [
            [r, c, witness_outputs["span"][r][c], witness_outputs["boundary"][r][c]]
            for r in range(len(witness_grid))
            for c in range(len(witness_grid[0]))
            if witness_outputs["span"][r][c]
            != witness_outputs["boundary"][r][c]
        ],
    }
    _write_json(witness_path, witness_record)
    created.append(witness_path)

    source_path = Path(__file__).resolve()
    snapshot_dir = out_dir / "private" / "source_snapshot"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    prototype_snapshot = snapshot_dir / "prototype.py"
    generator_snapshot = snapshot_dir / "generator.py"
    prototype_snapshot.write_bytes(source_path.read_bytes())
    generator_snapshot.write_bytes(generator_path.read_bytes())
    created.extend((prototype_snapshot, generator_snapshot))

    semantic_record = {
        "task_id": TASK_ID,
        "parameter": PARAMETERS,
        "program_sha256": {
            setting: sha256_text(render_program(setting, root=root))
            for setting in SETTINGS
        },
        "episode_seed_by_setting": setting_seeds,
        "episodes": {
            setting: {
                "train": episode["train"],
                "test": episode["test"],
                "rival": episode["rival"],
            }
            for setting, episode in episodes.items()
        },
        "canonical_summary": {
            key: canonical_report[key]
            for key in (
                "pairs_checked",
                "all_match",
                "python_parity",
                "boundary_shortcut_fits_all_canonical_pairs",
            )
        },
        "witness": witness_record,
    }

    report = {
        "schema": "arc-parametric-prototype-report-v1",
        "task_id": TASK_ID,
        "status": "verified_prototype",
        "approval": "unapproved; separate from selected canonical execution",
        "parameter": PARAMETERS,
        "settings_verified": list(SETTINGS),
        "canonical_default_byte_identical": True,
        "canonical_default": canonical_report,
        "episode_seed_by_setting": setting_seeds,
        "n_train": N_TRAIN,
        "n_test": N_TEST,
        "demonstrations_distinguish_rival": {
            setting: bool(
                episodes[setting]["rival"]["refuting_demonstration_indices"]
            )
            for setting in SETTINGS
        },
        "queries_differ_between_settings": {
            setting: episodes[setting]["rival"]["query_differs"]
            for setting in SETTINGS
        },
        "fixture_constraints": {
            "square_side": 4,
            "requires_interior_aligned_marker": True,
            "requires_boundary_aligned_firing_marker": True,
            "settings_differ_on_every_retained_pair": True,
        },
        "label_authority": "bundled real Racket runtime",
        "racket_runtime": racket_runtime_status(),
        "generator_path": generator_path.relative_to(root).as_posix(),
        "generator_sha256": generator_sha,
        "generator_version": generator.VERSION,
        "selected_rule_hash": generator.RULE_HASH,
        "canonical_program_sha256": sha256_text(canonical),
        "canonical_program_normalized_hash_12": normalized_rule_hash(canonical),
        "prototype_path": source_path.relative_to(root).as_posix(),
        "prototype_sha256": sha256_bytes(source_path.read_bytes()),
        "semantic_sha256": json_sha256(semantic_record),
        "limits": [
            "Only two bounded alignment-scope settings were evaluated.",
            "Each episode contains four deterministic side-four fixtures; this is finite evidence, not universal induction.",
            "The boundary setting is intentionally indistinguishable on the supplied side-two canonical pairs and is taught only by larger-square demonstrations.",
            "The alternative is proposed only; it is not selected, reviewed_safe, approved, or admitted for training.",
        ],
    }
    report_path = out_dir / "report.json"
    _write_json(report_path, report)
    created.append(report_path)

    manifest = {
        "schema": "arc-parametric-evidence-manifest-v1",
        "task_id": TASK_ID,
        "semantic_sha256": report["semantic_sha256"],
        "files": _manifest_rows(out_dir, created),
    }
    _write_json(out_dir / "manifest.json", manifest)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_evidence(args.seed, args.out)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
