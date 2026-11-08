"""Bounded, Racket-labelled enclosed-area rule episodes; never a production API."""

from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys
import traceback
from typing import Any

from arc_repl.racket_bridge import RacketBridge
import reviewer_support
from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid


TASK_ID = "33275a4aae3e"
PROTOTYPE_VERSION = "1.1.0"
PARAMETER_VALUES = (1, 32, 40)
DEFAULT_MIN_ENCLOSED_AREA = 1
CANONICAL_RACKET = (
    "(rule! (lambda (g) (let* ((h (rows g)) (w (cols g))) "
    "(let ((g2 (fill-all-enclosed g 2))) (recolor g2 0 3)))))"
)
EXECUTION_ADAPTER = "(let ((rule! (lambda (f) f))) ({program} parametric-input))"
EPISODE_ROLES = ("threshold_witness", "connectivity_witness") * 2
THRESHOLD_BANDS = frozenset({"below32", "32_to39"})


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_json(value: Any) -> str:
    """Hashes use UTF-8, sorted keys and compact JSON, without a trailing newline."""
    return hash_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise ValueError("seed must be an integer, excluding bool")
    return seed


def _validate_parameter(value: int) -> int:
    if type(value) is not int or value not in PARAMETER_VALUES:
        raise ValueError(f"min_enclosed_area must be an integer in {PARAMETER_VALUES}")
    return value


def select_parameter(seed: int, min_enclosed_area: int | None = None) -> int:
    """Choose the episode rule once; explicit settings take precedence."""
    _validate_seed(seed)
    if min_enclosed_area is not None:
        return _validate_parameter(min_enclosed_area)
    key = f"{TASK_ID}|parametric-{PROTOTYPE_VERSION}|min_enclosed_area|{seed}"
    return PARAMETER_VALUES[int(hash_text(key), 16) % len(PARAMETER_VALUES)]


def materialize_racket(min_enclosed_area: int = DEFAULT_MIN_ENCLOSED_AREA) -> str:
    """Materialize exact executable lambda-form source for one bounded setting."""
    threshold = _validate_parameter(min_enclosed_area)
    if threshold == DEFAULT_MIN_ENCLOSED_AREA:
        return CANONICAL_RACKET
    return f"""(rule!
  (lambda (g)
    (let* ((filled (fill-all-enclosed g 2))
           (enclosed-mask
             (map-grid g
               (lambda (r c value)
                 (if (and (= value 0) (= (cell-at filled r c) 2)) 1 0))))
           (eligible
             (filter (lambda (region) (>= (obj-size region) {threshold}))
                     (objects enclosed-mask 0))))
      (paint-objects (recolor g 0 3) eligible 2))))"""


def _zero_components(grid: list[list[int]], *, connectivity: int = 4
                     ) -> list[tuple[list[tuple[int, int]], bool]]:
    """Independent Python geometry for controls and input selection, not labels."""
    height, width = len(grid), len(grid[0])
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        deltas += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack, cells, boundary = [start], [], False
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            boundary = boundary or row in (0, height - 1) or col in (0, width - 1)
            for dr, dc in deltas:
                neighbor = (row + dr, col + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        components.append((cells, boundary))
    return components


def solve_python(grid: list[list[int]], min_enclosed_area: int = 1) -> list[list[int]]:
    """Independent assertion oracle only; exported labels always come from Racket."""
    threshold = _validate_parameter(min_enclosed_area)
    original = normalize_grid(grid)
    output = copy.deepcopy(original)
    for cells, boundary in _zero_components(original):
        color = 2 if not boundary and len(cells) >= threshold else 3
        for row, col in cells:
            output[row][col] = color
    return output


def enclosed_areas(grid: list[list[int]]) -> list[int]:
    return sorted(len(cells) for cells, boundary in _zero_components(grid) if not boundary)


def semantic_rival_predictions(generator, grid: list[list[int]], threshold: int) -> dict:
    """Python diagnostic rivals; these never supply reference labels.

    The rectangle rival uses the selected source's declared rectangle mask,
    filtered by the area of each original four-connected zero component. The
    diagonal rival changes both component finding and boundary reachability to
    eight-neighbor connectivity, preserving the same numeric threshold.
    """
    threshold = _validate_parameter(threshold)
    rectangle_mask = generator.CANONICAL_SHORTCUTS["complete_rectangle_fill"](grid)
    eligible = {
        cell for cells, _ in _zero_components(grid) if len(cells) >= threshold
        for cell in cells
    }
    rectangle_output = [
        [value if value else (2 if rectangle_mask[row][col] == 2
                              and (row, col) in eligible else 3)
         for col, value in enumerate(values)]
        for row, values in enumerate(grid)
    ]
    diagonal_output = copy.deepcopy(grid)
    for cells, boundary in _zero_components(grid, connectivity=8):
        color = 2 if not boundary and len(cells) >= threshold else 3
        for row, col in cells:
            diagonal_output[row][col] = color
    return {"complete_rectangle_fill_at_threshold": rectangle_output,
            "eight_connected_enclosure_at_threshold": diagonal_output}


class RacketEvaluator:
    """Public protected bridge, exact lambda source, content-addressed label cache."""

    def __init__(self) -> None:
        self.bridge = RacketBridge(timeout=10.0)
        self.cache: dict[tuple[str, str], list[list[int]]] = {}
        self.evaluation_requests = 0
        self.executed_evaluations = 0

    @property
    def runtime_identity(self) -> dict:
        return copy.deepcopy(self.bridge.runtime_identity)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.bridge.shutdown()
        return False

    def evaluate(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        normalized = normalize_grid(grid)
        # Only this prototype's declared materialized programs may use the adapter.
        if program not in {materialize_racket(value) for value in PARAMETER_VALUES}:
            raise ValueError("evaluator accepts only declared materialized programs")
        self.evaluation_requests += 1
        key = (hash_text(program), hash_json(normalized))
        if key not in self.cache:
            self.bridge.define_grid("parametric-input", normalized)
            expression = EXECUTION_ADAPTER.format(program=program)
            actual = normalize_grid(self.bridge.eval_text(expression))
            if len(actual) != len(normalized) or len(actual[0]) != len(normalized[0]):
                raise ValueError("Racket changed the grid dimensions")
            self.cache[key] = actual
            self.executed_evaluations += 1
        return copy.deepcopy(self.cache[key])


class EpisodeSelectionError(RuntimeError):
    def __init__(self, receipt: dict) -> None:
        self.receipt = receipt
        super().__init__(json.dumps(receipt, sort_keys=True))


class PrototypeValidationError(RuntimeError):
    def __init__(self, receipt: dict) -> None:
        self.receipt = receipt
        super().__init__(json.dumps(receipt, sort_keys=True))


def _sample_inputs(generator, seed: int, max_draws: int) -> tuple[list[dict], dict]:
    if type(max_draws) is not int or max_draws < 1:
        raise ValueError("max_draws must be a positive integer")
    accepted, rejected, seen = [], [], set()
    connectivity_profiles = set(generator.CONNECTIVITY_PROFILES)
    for sample_index in range(max_draws):
        try:
            grid = normalize_grid(generator.generate(seed, sample_index))
            failures = generator.self_check(grid)
            if failures:
                raise ValueError(f"selected generator self_check: {failures}")
        except Exception as exc:
            raise EpisodeSelectionError({
                "status": "generator_error", "seed": seed,
                "sample_index": sample_index, "error": repr(exc),
                "attempted_candidates": sample_index + 1,
                "accepted_pairs": len(accepted), "rejected": rejected,
            }) from exc
        digest = hash_json(grid)
        areas = enclosed_areas(grid)
        coverage = {
            "below32" if area < 32 else "32_to39" if area < 40 else "at_least40"
            for area in areas
        }
        role = EPISODE_ROLES[len(accepted)]
        profile = generator.observe_overrides(grid).get("scene_profile")
        if digest in seen:
            reason = "duplicate_accepted_input"
        elif (role == "connectivity_witness") != (profile in connectivity_profiles):
            reason = "wrong_episode_role"
        elif role == "threshold_witness" and not THRESHOLD_BANDS <= coverage:
            reason = "missing_area_band"
        elif role == "connectivity_witness" and not all(
            generator.SEMANTIC_WITNESSES[name](grid)
            for name in ("nonrectangular_enclosure", "diagonal_seal")
        ):
            reason = "missing_connectivity_witness"
        elif role == "connectivity_witness" and (
            semantic_rival_predictions(generator, grid, 40)["complete_rectangle_fill_at_threshold"]
            == solve_python(grid, 40)
        ):
            reason = "no_large_nonrectangular_witness"
        else:
            seen.add(digest)
            accepted.append({"input": grid, "input_sha256": digest,
                             "sample_index": sample_index, "enclosed_areas": areas,
                             "role": role, "scene_profile": profile})
            if len(accepted) == len(EPISODE_ROLES):
                return accepted, {
                    "seed": seed, "difficulty": None, "max_draws": max_draws,
                    "attempted_candidates": sample_index + 1,
                    "accepted_sample_indices": [row["sample_index"] for row in accepted],
                    "accepted_input_sha256": [row["input_sha256"] for row in accepted],
                    "rejection_counts": dict(Counter(row["reason"] for row in rejected)),
                    "rejected": rejected,
                    "input_selection_independent_of_parameter": True,
                    "roles": list(EPISODE_ROLES),
                    "threshold_witness_bands": sorted(THRESHOLD_BANDS),
                    "connectivity_profile_pool": sorted(connectivity_profiles),
                    "connectivity_witness_requires_rectangle_refutation_at_40": True,
                }
            continue
        rejected.append({"sample_index": sample_index, "reason": reason,
                         "enclosed_areas": areas, "input_sha256": digest})
    raise EpisodeSelectionError({
        "status": "selection_budget_exhausted", "seed": seed,
        "max_draws": max_draws, "attempted_candidates": max_draws,
        "accepted_pairs": len(accepted), "accepted": accepted, "rejected": rejected,
        "next_required_role": EPISODE_ROLES[len(accepted)],
    })


def _difference(first: list[list[int]], second: list[list[int]]) -> dict:
    changed = [(r, c) for r in range(len(first)) for c in range(len(first[0]))
               if first[r][c] != second[r][c]]
    return {"changed_cells": len(changed),
            "first_changed_cell": list(changed[0]) if changed else None}


def _rival_check(threshold: int, predictions: dict, train: list[int], query: list[int]) -> dict:
    selected = predictions[str(threshold)]
    rivals = []
    for rival in PARAMETER_VALUES:
        if rival == threshold:
            continue
        alternate = predictions[str(rival)]
        refuting = [index for index in train if alternate[index] != selected[index]]
        query_disagreements = [index for index in query if alternate[index] != selected[index]]
        status = ("refuted_by_demonstration" if refuting else
                  "ambiguous" if query_disagreements else "survived_all")
        first = refuting[0] if refuting else None
        rivals.append({
            "parameters": {"min_enclosed_area": rival},
            "program_sha256": hash_text(materialize_racket(rival)),
            "status": status, "refuting_demonstration_indices": refuting,
            "query_disagreement_indices": query_disagreements,
            "first_refutation": ({"pair_index": first,
                                   **_difference(selected[first], alternate[first])}
                                  if first is not None else None),
        })
    return {"demonstration_indices": train, "query_indices": query,
            "all_declared_rivals_refuted": all(
                row["status"] == "refuted_by_demonstration" for row in rivals),
            "ambiguous": any(row["status"] == "ambiguous" for row in rivals),
            "rivals": rivals}


def _semantic_rival_check(selected: list, predictions: dict,
                          train: list[int], query: list[int]) -> dict:
    rivals = []
    for name, alternate in predictions.items():
        refuting = [index for index in train if alternate[index] != selected[index]]
        query_disagreements = [index for index in query if alternate[index] != selected[index]]
        status = ("refuted_by_demonstration" if refuting else
                  "ambiguous" if query_disagreements else "survived_all")
        first = refuting[0] if refuting else None
        rivals.append({
            "name": name, "prediction_backend": "python-diagnostic-rival",
            "status": status, "refuting_demonstration_indices": refuting,
            "query_disagreement_indices": query_disagreements,
            "first_refutation": ({"pair_index": first,
                                   **_difference(selected[first], alternate[first])}
                                  if first is not None else None),
        })
    return {"demonstration_indices": train, "query_indices": query,
            "ambiguous": any(row["status"] == "ambiguous" for row in rivals),
            "rivals": rivals}


def build_episode(seed: int, *, min_enclosed_area: int | None = None,
                  evaluator: RacketEvaluator | None = None, root: Path | None = None,
                  max_draws: int = 512) -> dict:
    """Three demonstrations and one query under one seed-selected or explicit rule."""
    threshold = select_parameter(seed, min_enclosed_area)
    root = Path(root).resolve() if root is not None else find_root(__file__)
    if evaluator is None:
        with RacketEvaluator() as owned:
            return build_episode(seed, min_enclosed_area=min_enclosed_area,
                                 evaluator=owned, root=root, max_draws=max_draws)
    generator, source, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    sampled, sampling = _sample_inputs(generator, seed, max_draws)
    predictions = {}
    for setting in PARAMETER_VALUES:
        program = materialize_racket(setting)
        outputs = []
        for pair in sampled:
            actual = evaluator.evaluate(program, pair["input"])
            expected = solve_python(pair["input"], setting)
            if actual != expected:
                raise PrototypeValidationError({
                    "status": "racket_python_disagreement", "seed": seed,
                    "parameters": {"min_enclosed_area": setting},
                    "sample_index": pair["sample_index"], "input": pair["input"],
                    "racket_output": actual, "python_output": expected,
                    "program": program, "program_sha256": hash_text(program),
                })
            outputs.append(actual)
        predictions[str(setting)] = outputs
    pairs = []
    for index, sampled_pair in enumerate(sampled):
        output = predictions[str(threshold)][index]
        pairs.append({**sampled_pair, "split": "train" if index < 3 else "test",
                      "pair_index": index if index < 3 else 0,
                      "output": copy.deepcopy(output), "output_sha256": hash_json(output)})
    rival_check = _rival_check(threshold, predictions, [0, 1, 2], [3])
    rotations = [
        _rival_check(threshold, predictions, [i for i in range(4) if i != held], [held])
        for held in range(4)
    ]
    semantic_predictions: dict[str, list] = {}
    for pair in sampled:
        for name, output in semantic_rival_predictions(generator, pair["input"], threshold).items():
            semantic_predictions.setdefault(name, []).append(output)
    semantic_check = _semantic_rival_check(
        predictions[str(threshold)], semantic_predictions, [0, 1, 2], [3]
    )
    semantic_rotations = [
        _semantic_rival_check(predictions[str(threshold)], semantic_predictions,
                              [i for i in range(4) if i != held], [held])
        for held in range(4)
    ]
    if not rival_check["all_declared_rivals_refuted"] or not all(
        row["all_declared_rivals_refuted"] for row in rotations
    ):
        raise PrototypeValidationError({"status": "unidentifiable_episode", "seed": seed,
                                        "rival_check": rival_check, "query_rotations": rotations})
    program = materialize_racket(threshold)
    return {
        "schema": "33275a4aae3e-parametric-episode-v1", "status": "prototype",
        "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION, "seed": seed,
        "parameter_selection": "seed" if min_enclosed_area is None else "explicit",
        "parameters": {"min_enclosed_area": threshold},
        "generator_source": source.relative_to(root).as_posix(),
        "generator_sha256": generator_sha256,
        "program": program, "program_sha256": hash_text(program),
        "pairs": pairs, "sampling": sampling, "rival_check": rival_check,
        "query_rotations": rotations,
        "semantic_rival_check": semantic_check,
        "semantic_query_rotations": semantic_rotations,
        "semantic_rival_predictions": {
            name: [{"output": output, "output_sha256": hash_json(output)}
                   for output in outputs]
            for name, outputs in semantic_predictions.items()
        },
        "racket_predictions": {
            setting: [{"output": output, "output_sha256": hash_json(output)}
                      for output in outputs]
            for setting, outputs in predictions.items()
        },
        "python_agreement_checks": len(PARAMETER_VALUES) * len(pairs),
    }


def public_challenge(episode: dict) -> dict:
    """No rule, parameter, source, sampling metadata, or query output crosses here."""
    return {
        "train": [copy.deepcopy({"input": row["input"], "output": row["output"]})
                  for row in episode["pairs"] if row["split"] == "train"],
        "test": [copy.deepcopy({"input": row["input"]})
                 for row in episode["pairs"] if row["split"] == "test"],
    }


def _source_manifest(root: Path) -> list[dict]:
    _, generator_source, _ = load_selected_generator(TASK_ID, root=root)
    source_files = [
        Path(__file__).resolve(), Path(__file__).resolve().with_name("README.md"),
        root / "generators" / TASK_ID / "tests" / "test_parametric_33275a4aae3e.py",
        generator_source, Path(reviewer_support.__file__).resolve(),
    ]
    for relative in (
        "shared/data/base/solutions/training/7b6016b9__33275a4aae3e.json",
        "data/base/solutions/training/7b6016b9__33275a4aae3e.json",
        "shared/runtime/puzzle_generators/base.py",
        "shared/runtime/puzzle_generators/helpers/grid.py",
        "puzzle_generators/base.py", "puzzle_generators/helpers/grid.py",
    ):
        candidate = root / relative
        if candidate.is_file():
            source_files.append(candidate)
    rows = []
    for path in sorted(set(source_files)):
        body = path.read_bytes()
        rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(body),
                     "sha256": hashlib.sha256(body).hexdigest()})
    return rows


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8")


def export_evidence(destination: Path, *, seeds: list[int], root: Path | None = None,
                    evaluator: RacketEvaluator | None = None,
                    min_enclosed_area: int | None = None, seed_selected: bool = False,
                    max_draws: int = 512) -> dict:
    """Write a bounded all-settings or selected-settings authoring evidence bundle."""
    destination = Path(destination).resolve()
    root = Path(root).resolve() if root is not None else find_root(__file__)
    # Claim a new directory before runtime startup; no failure can overwrite a
    # previous run. Every partial result is private and explicitly incomplete.
    destination.mkdir(parents=True, exist_ok=False)
    private_path = destination / "private_evidence.json"
    progress = {
        "schema": "33275a4aae3e-parametric-evidence-v1", "status": "in_progress",
        "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION, "episodes": [],
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "requested_seeds": seeds, "explicit_min_enclosed_area": min_enclosed_area,
        "seed_selected": seed_selected, "max_draws": max_draws,
    }
    _write_json(private_path, progress)
    try:
        progress["sources"] = _source_manifest(root)
        _write_json(private_path, progress)
        if evaluator is None:
            with RacketEvaluator() as owned:
                return _export_owned_directory(
                    destination, seeds=seeds, root=root, evaluator=owned,
                    min_enclosed_area=min_enclosed_area,
                    seed_selected=seed_selected, max_draws=max_draws,
                )
        return _export_owned_directory(
            destination, seeds=seeds, root=root, evaluator=evaluator,
            min_enclosed_area=min_enclosed_area,
            seed_selected=seed_selected, max_draws=max_draws,
        )
    except Exception as exc:
        progress = json.loads(private_path.read_text(encoding="utf-8"))
        failure = {
            "status": "fail", "error_type": type(exc).__name__, "error": str(exc),
            "detail": getattr(exc, "receipt", None), "traceback": traceback.format_exc(),
            "invocation": progress["invocation"],
            "private_provenance": "private_evidence.json",
            "completed_episodes": len(progress["episodes"]),
        }
        progress["status"] = "fail"
        progress["failure"] = failure
        _write_json(private_path, progress)
        _write_json(destination / "failure.json", failure)
        raise


def _export_owned_directory(destination: Path, *, seeds: list[int], root: Path,
                            evaluator: RacketEvaluator,
                            min_enclosed_area: int | None, seed_selected: bool,
                            max_draws: int) -> dict:
    """Complete only a directory already claimed by export_evidence."""
    if not seeds:
        raise ValueError("at least one seed is required")
    for seed in seeds:
        _validate_seed(seed)
    if seed_selected and min_enclosed_area is not None:
        raise ValueError("seed_selected and explicit min_enclosed_area are mutually exclusive")
    settings = ([None] if seed_selected else [_validate_parameter(min_enclosed_area)]
                if min_enclosed_area is not None else list(PARAMETER_VALUES))
    (destination / "public").mkdir()
    (destination / "programs").mkdir()
    private_path = destination / "private_evidence.json"
    progress = json.loads(private_path.read_text(encoding="utf-8"))
    sources = progress["sources"]
    programs = []
    for setting in PARAMETER_VALUES:
        program = materialize_racket(setting)
        relative = f"programs/min-area-{setting}.rkt"
        (destination / relative).write_text(program, encoding="utf-8")
        programs.append({"parameters": {"min_enclosed_area": setting}, "program": program,
                         "program_sha256": hash_text(program), "path": relative})
    before_requests = evaluator.evaluation_requests
    before_executions = evaluator.executed_evaluations
    episodes = []
    progress.update({"runtime": evaluator.runtime_identity, "programs": programs,
                     "execution_adapter": EXECUTION_ADAPTER, "episodes": episodes})
    _write_json(private_path, progress)
    for seed in seeds:
        for setting in settings:
            episode = build_episode(seed, min_enclosed_area=setting, evaluator=evaluator,
                                    root=root, max_draws=max_draws)
            public_path = f"public/episode-{len(episodes):04d}.challenge.json"
            challenge = public_challenge(episode)
            _write_json(destination / public_path, challenge)
            episode["public_challenge_path"] = public_path
            episode["public_challenge_sha256"] = hash_json(challenge)
            episodes.append(episode)
            _write_json(private_path, progress)
    controls = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        actual = evaluator.evaluate(materialize_racket(), pair["input"])
        controls.append({
            "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
            "input_sha256": hash_json(pair["input"]), "output_sha256": hash_json(actual),
            "expected_output_sha256": hash_json(pair["output"]),
            "passed": actual == pair["output"] == solve_python(pair["input"]),
        })
    progress["canonical_controls"] = controls
    profile_controls = []
    progress["profile_controls"] = profile_controls
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    for profile in generator.SCENE_PROFILES:
        grid = normalize_grid(generator.generate(seeds[0], 0, scene_profile=profile))
        failures = generator.self_check(grid)
        if failures:
            raise PrototypeValidationError({"status": "invalid_profile_control",
                                            "scene_profile": profile, "errors": failures})
        checked = []
        for setting in PARAMETER_VALUES:
            actual = evaluator.evaluate(materialize_racket(setting), grid)
            checked.append({
                "parameters": {"min_enclosed_area": setting},
                "program_sha256": hash_text(materialize_racket(setting)),
                "output": actual, "output_sha256": hash_json(actual),
                "passed": actual == solve_python(grid, setting),
            })
        profile_controls.append({
            "scene_profile": profile, "seed": seeds[0], "sample_index": 0,
            "input": grid, "input_sha256": hash_json(grid),
            "enclosed_areas": enclosed_areas(grid), "parameter_checks": checked,
        })
        _write_json(private_path, progress)
    if _source_manifest(root) != sources:
        raise PrototypeValidationError({"status": "source_changed_during_export"})
    report = {
        "schema": "33275a4aae3e-parametric-evidence-v1",
        "status": "pass" if (all(row["passed"] for row in controls) and all(
            checked["passed"] for profile in profile_controls
            for checked in profile["parameter_checks"]) and all(
            not ep["semantic_rival_check"]["ambiguous"] and all(
                not row["ambiguous"] for row in ep["semantic_query_rotations"])
            for ep in episodes)) else "fail",
        "admission": "proposed prototype only; no production or training approval",
        "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION,
        "parameter": {"name": "min_enclosed_area", "allowed_values": list(PARAMETER_VALUES),
                      "canonical_default": DEFAULT_MIN_ENCLOSED_AREA,
                      "comparison": "enclosed four-connected zero-component area >= threshold"},
        "sources": sources, "runtime": evaluator.runtime_identity,
        "execution_adapter": EXECUTION_ADAPTER,
        "hash_format": "SHA-256 of UTF-8; JSON sorted keys, compact separators, no newline",
        "programs": programs, "episodes": episodes, "canonical_controls": controls,
        "profile_controls": profile_controls,
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "reproduction": {
            "cwd": "WORK", "seeds": seeds, "explicit_min_enclosed_area": min_enclosed_area,
            "seed_selected": seed_selected, "max_draws": max_draws,
            "payload": "generators/33275a4aae3e/workspace/parametric/prototype.py",
            "wrapper": "python3 run_with_racket.py ABSOLUTE_PYTHON PAYLOAD ARGS",
        },
        "counts": {
            "episodes": len(episodes), "labelled_pairs": 4 * len(episodes),
            "unique_input_grids": len({pair["input_sha256"] for ep in episodes for pair in ep["pairs"]}),
            "unique_seed_input_sequences": len(set(seeds)),
            "parameter_rival_checks": 2 * len(episodes),
            "query_rotations": 4 * len(episodes), "rotation_rival_checks": 8 * len(episodes),
            "ambiguous_episodes": sum(ep["rival_check"]["ambiguous"] for ep in episodes),
            "ambiguous_rotations": sum(row["ambiguous"] for ep in episodes for row in ep["query_rotations"]),
            "semantic_rival_checks": 2 * len(episodes),
            "semantic_rotation_rival_checks": 8 * len(episodes),
            "semantic_ambiguous_episodes": sum(ep["semantic_rival_check"]["ambiguous"] for ep in episodes),
            "semantic_ambiguous_rotations": sum(
                row["ambiguous"] for ep in episodes for row in ep["semantic_query_rotations"]),
            "semantic_survived_all": sum(
                row["status"] == "survived_all" for ep in episodes
                for row in ep["semantic_rival_check"]["rivals"]),
            "rectangle_rival_refutations": sum(
                row["status"] == "refuted_by_demonstration" for ep in episodes
                for row in ep["semantic_rival_check"]["rivals"]
                if row["name"] == "complete_rectangle_fill_at_threshold"),
            "eight_neighbor_rival_refutations": sum(
                row["status"] == "refuted_by_demonstration" for ep in episodes
                for row in ep["semantic_rival_check"]["rivals"]
                if row["name"] == "eight_connected_enclosure_at_threshold"),
            "canonical_controls": len(controls),
            "canonical_controls_passed": sum(row["passed"] for row in controls),
            "profile_inputs": len(profile_controls),
            "profile_parameter_checks": 3 * len(profile_controls),
            "profile_parameter_checks_passed": sum(
                checked["passed"] for profile in profile_controls
                for checked in profile["parameter_checks"]),
            "python_agreement_checks": sum(ep["python_agreement_checks"] for ep in episodes),
            "racket_evaluation_requests": evaluator.evaluation_requests - before_requests,
            "racket_unique_executions_this_export": evaluator.executed_evaluations - before_executions,
            "cache_entries_available_after_export": len(evaluator.cache),
        },
        "limitations": [
            "Finite checks only against the two other declared parameter values per episode.",
            "Area-band selection narrows the episode distribution; no claim of unconstrained support.",
            "Balanced threshold/connectivity roles retain both kinds after every one-query holdout; not every individual pair distinguishes all parameters.",
            "The extra rectangle and eight-neighbor controls are Python diagnostic rivals scored against Racket labels, not alternative reference programs.",
            "At thresholds 32/40, the sampled diagonal pockets are subthreshold: the eight-neighbor rival survives all pairs. Four-vs-eight connectivity is only demonstrated at canonical threshold 1 here.",
            "All selected scene profiles are checked separately at all three thresholds; these controls are not episodes or evidence of their teachability.",
            "Same-seed explicit settings reuse the same inputs; episode count is not an independent-grid count.",
            "Canonical controls include available selected-task variants; duplicate grids may occur.",
            "The plain lexical rule! adapter supports these explicit callable-lambda programs only.",
            "Public challenge files alone are model-visible; the rest of this bundle contains answers.",
            "No production parametric API, approval update, or training admission is supplied.",
        ],
    }
    _write_json(destination / "private_evidence.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="17,29,41", help="comma-separated integer seeds")
    parser.add_argument("--out", type=Path, required=True, help="new authoring-evidence directory")
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--min-enclosed-area", type=int, choices=PARAMETER_VALUES)
    options.add_argument("--seed-selected", action="store_true")
    parser.add_argument("--max-draws", type=int, default=512)
    args = parser.parse_args(argv)
    try:
        seeds = [int(value) for value in args.seeds.split(",")]
    except ValueError:
        parser.error("--seeds must be comma-separated integers")
    try:
        report = export_evidence(args.out, seeds=seeds, min_enclosed_area=args.min_enclosed_area,
                                 seed_selected=args.seed_selected, max_draws=args.max_draws)
    except FileExistsError:
        print(f"Refusing to overwrite existing evidence: {args.out}", file=sys.stderr)
        return 2
    except Exception as exc:
        failure_path = args.out / "failure.json"
        message = {"status": "fail", "error": repr(exc)}
        if failure_path.is_file():
            message["failure"] = str(failure_path)
        print(json.dumps(message), file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "private_evidence": str(args.out / "private_evidence.json")}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
