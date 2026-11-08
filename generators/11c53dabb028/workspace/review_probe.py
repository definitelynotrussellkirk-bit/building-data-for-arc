"""Finite semantic and joint-axis review for 11c53dabb028.

This file is reviewer tooling, never a source of production labels.  The small
Python complement-and-concatenation calculation is a diagnostic mirror.  With
``--racket`` (the default), actual lessons and parity checks use the production
runner and the selected canonical Racket authority in a copied runtime.

The report retains aggregates, replay recipes, hashes, one failure per category,
and a smallest observed counterexample for each declared rival.  It does not
claim universal induction or support outside the tested finite populations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any


TASK = "11c53dabb028"
BANDS = ("easy", "medium", "hard")
DECLARATIONS = ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")
PROBE_FILE = Path(__file__).resolve()


def _find_tree(start: Path) -> Path:
    for candidate in (start.parent, *start.parents):
        if ((candidate / "shared/data/canonical/puzzles.jsonl").is_file()
                or (candidate / "data/canonical/puzzles.jsonl").is_file()):
            return candidate
    raise FileNotFoundError("Cannot locate this probe's own canonical data tree")


ROOT = _find_tree(PROBE_FILE)
IS_RUNTIME = (ROOT / "data/canonical/puzzles.jsonl").is_file()
for dependency in (ROOT if IS_RUNTIME else ROOT / "shared/runtime", ROOT / "src"):
    if dependency.is_dir() and str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

from reviewer_support import canonical_pairs as _canonical_pairs, normalize_grid


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generator_path() -> Path:
    relative = (f"puzzle_generators/per_puzzle/{TASK}/generator.py" if IS_RUNTIME
                else f"generators/{TASK}/generator.py")
    return ROOT / relative


def load_generator(path: Path | str | None = None):
    selected = Path(path).resolve() if path else generator_path()
    name = "_semantic_review_generator_" + TASK
    spec = importlib.util.spec_from_file_location(name, selected)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import generator {selected}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK, root=ROOT)


def mirror_output(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic calculation: complement one tile, then concatenate copies.

    Deliberately uses row concatenation, rather than the authority's modulo
    indexing.  This still requires Racket parity; it is not an independent
    specification or a replacement authority.
    """
    grid = normalize_grid(grid)
    first = next(value for row in grid for value in row if value != 0)
    tile = [[first if value == 0 else 0 for value in row] for row in grid]
    horizontal = [row + row for row in tile]
    return [row[:] for row in horizontal] + [row[:] for row in horizontal]


def decisive_inputs() -> list[list[list[int]]]:
    """Small fixed middle/minimum/maximum selector controls, not templates."""
    return [
        [[0, 5, 1, 9], [9, 0, 5, 9]],
        [[0, 1, 5, 9], [9, 0, 1, 9]],
        [[0, 9, 1, 5], [5, 0, 9, 5]],
        [[0, 5], [9, 0], [1, 5], [9, 9]],
    ]


def observed(grid: list[list[int]]) -> dict[str, Any]:
    values = [value for row in grid for value in row if value != 0]
    colors = sorted(set(values))
    first = values[0]
    h, w = len(grid), len(grid[0])
    role = ("mono" if len(colors) == 1 else "minimum" if first == colors[0]
            else "maximum" if first == colors[-1] else "middle")
    return {
        "grid_h": h, "grid_w": w, "fg_color": first,
        "multi_color": len(colors) > 1, "occupied_cells": len(values),
        "realized_density": len(values) / (h * w), "selector_role": role,
        "palette_size": len(colors) + int(any(0 in row for row in grid)),
    }


def declared_rivals(gen) -> dict[str, Any]:
    """Preserve all declaration namespaces; colliding names are not dropped."""
    result = {}
    for attribute in DECLARATIONS:
        declaration = getattr(gen, attribute, {})
        if not isinstance(declaration, dict):
            raise TypeError(f"{attribute} must be dict[str, grid -> grid]")
        for name, fn in declaration.items():
            if not isinstance(name, str) or not name or not callable(fn):
                raise TypeError(f"Invalid rival declaration {attribute}:{name!r}")
            result[f"{attribute}:{name}"] = fn
    if not result:
        raise ValueError("No declared executable rivals; identifiability is unmeasured")
    return result


def rival_predictions(rivals: dict, pairs: list[dict]) -> dict[str, list]:
    by_callable = {}
    result = {}
    for name, fn in rivals.items():
        identity = id(fn)
        if identity not in by_callable:
            by_callable[identity] = [normalize_grid(fn(deepcopy(pair["input"]))) for pair in pairs]
        result[name] = by_callable[identity]
    return result


def score_query_rotation(gen, rivals: dict, pairs: list[dict], query_index: int,
                         predictions: dict | None = None) -> dict:
    """Move each pair into the query position, preserving cyclic demo order."""
    predictions = predictions if predictions is not None else rival_predictions(rivals, pairs)
    order = list(range(query_index + 1, len(pairs))) + list(range(query_index + 1))
    demos = [pairs[i] for i in order[:-1]]
    query = pairs[query_index]
    states = {}
    for name, outputs in predictions.items():
        fits = all(outputs[i] == pairs[i]["output"] for i in order[:-1])
        agrees = outputs[query_index] == query["output"]
        states[name] = "refuted" if not fits else "survived_all" if agrees else "ambiguous"
    hook = getattr(gen, "lesson_identifiable", None)
    if not callable(hook):
        raise TypeError("lesson_identifiable must be a callable reasons hook")
    reasons = hook(deepcopy(demos), deepcopy(query))
    if not isinstance(reasons, (list, tuple)) or any(not isinstance(item, str) for item in reasons):
        raise TypeError("lesson_identifiable must return list[str]")
    return {"rivals": states, "ambiguous": [name for name, state in states.items() if state == "ambiguous"],
            "hook_reasons": list(reasons)}


def requested_count(area: int, density: float) -> int:
    return min(area - 1, max(1, round(area * density)))


def joint_cases(full: bool = True):
    shapes = [(h, w) for h in range(1, 16) for w in range(1, 16)] if full else [
        (1, 1), (1, 2), (2, 1), (1, 15), (15, 1), (2, 2), (2, 3), (3, 2), (15, 15),
    ]
    for band in (None, *BANDS):
        for h, w in shapes:
            for density_index, density in enumerate((0.0, 0.5, 1.0)):
                for multi in (False, True):
                    options = {"grid_h": h, "grid_w": w,
                               "fg_color": 1 + ((h + 2 * w + density_index) % 9),
                               "fg_density": density, "multi_color": multi}
                    count = requested_count(h * w, density)
                    feasible = h * w >= 2 and (not multi or count >= 2)
                    yield band, options, feasible


def check_joint_case(gen, band, options: dict, feasible: bool, *, index: int = 0):
    """Validate only advertised general controls, not default witness roles."""
    seed = 880301 + index
    try:
        grid = gen.generate(seed, 21000 + index, difficulty=band, **options)
    except ValueError:
        if feasible:
            raise
        return None
    if not feasible:
        raise AssertionError(f"Infeasible exact tuple was accepted: {options}")
    grid = normalize_grid(grid)
    errors = gen.self_check(deepcopy(grid), difficulty=band)
    if errors:
        raise AssertionError(f"self_check rejected joint tuple: {errors}")
    actual = observed(grid)
    for key in ("grid_h", "grid_w", "fg_color", "multi_color"):
        if actual[key] != options[key]:
            raise AssertionError(f"{key}: requested {options[key]!r}, observed {actual[key]!r}")
    area = options["grid_h"] * options["grid_w"]
    if actual["occupied_cells"] != requested_count(area, options["fg_density"]):
        raise AssertionError(f"Requested density did not realize documented rounded count: {actual}")
    observer = getattr(gen, "observe_overrides", None)
    if not callable(observer):
        raise TypeError("observe_overrides is missing")
    claimed = observer(deepcopy(grid))
    for key in ("grid_h", "grid_w", "fg_color", "multi_color", "occupied_cells", "realized_density"):
        if claimed.get(key) != actual[key]:
            raise AssertionError(f"Observer {key!r} disagrees with independently counted pixels")
    return grid


@contextmanager
def racket_session():
    if not IS_RUNTIME:
        raise RuntimeError("Racket execution requires the copied runtime; use run_probe")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators import runner
    from puzzle_generators.rule_wrap import wrap_rule
    from scripts.canonical_profile_gate import canonical_rule_source, normalized_rule_hash
    canonical_source = canonical_rule_source(TASK)
    rule_hash = normalized_rule_hash(canonical_source)
    generator = load_generator()
    if getattr(generator, "RULE_HASH", None) != rule_hash:
        raise RuntimeError("Generator RULE_HASH is not pinned to the selected canonical authority")
    # Public runner data class and public bridge operations.  Do not call the
    # runner's private loading, bridge-opening, or rule-application helpers.
    bundle = runner.GeneratorBundle(
        task_id=TASK, rule_task_id=TASK, rule_source=canonical_source,
        rule_callable_text=wrap_rule(canonical_source),
        rule_file=f"data/canonical/puzzles.jsonl:{TASK}", generator_module=generator,
    )
    bridge, name = RacketBridge(), "__semantic_review_rule"
    try:
        bridge.eval_text(f"(define {name} {bundle.rule_callable_text})")
        yield runner, bundle, bridge, name, rule_hash
    finally:
        bridge.shutdown()


def _verified_census(path: Path, gen, per_band: int, canonical_source: str):
    """Read existing production lessons only after checking their source binding."""
    census = json.loads(path.read_text())
    if census.get("schema") != "arcpuzzles-lesson-census-v1" or census.get("task_id") != TASK:
        raise ValueError("Lesson census has the wrong schema or task")
    if census.get("status") != "no_declared_ambiguity":
        raise ValueError(f"Lesson census is not complete and clean: {census.get('status')!r}")
    if census.get("generator_sha256") != file_digest(Path(gen.__file__)):
        raise ValueError("Lesson census generator bytes differ from the generator under review")
    if census.get("declared_rule_hash") != gen.RULE_HASH:
        raise ValueError("Lesson census RULE_HASH differs from the current generator")
    canonical_sha = hashlib.sha256(canonical_source.encode()).hexdigest()
    if census.get("rule_source_sha256") != canonical_sha:
        raise ValueError("Lesson census rule bytes differ from the selected canonical source")
    if set(census.get("rivals", [])) != set(declared_rivals(gen)):
        raise ValueError("Lesson census did not score the current complete rival declarations")
    sampler = census.get("sampler", {})
    if sampler.get("n_demos") != 5 or sampler.get("n_queries") != 1:
        raise ValueError("Lesson census does not contain five-demo, one-query lessons")
    by_band = {band: [] for band in BANDS}
    for row in census.get("lessons", []):
        if row.get("band") not in by_band:
            continue
        instance = row.get("instance")
        if not isinstance(instance, dict) or digest(instance) != row.get("instance_sha256"):
            raise ValueError("Lesson census contains a missing or hash-mismatched instance")
        if row.get("errors") or row.get("ambiguous") or row.get("warnings"):
            raise ValueError("Lesson census contains a failed, ambiguous, or warned lesson")
        if len(instance.get("train", [])) != 5 or len(instance.get("test", [])) != 1:
            raise ValueError("Lesson census instance has an unexpected pair count")
        by_band[row["band"]].append(row)
    if any(len(rows) < per_band for rows in by_band.values()):
        raise ValueError("Lesson census does not contain the requested completed count in every band")
    return census, by_band


def _seed(kind: str, band: str, index: int) -> int:
    return int(hashlib.sha256(f"review-probe:v1:{TASK}:{kind}:{band}:{index}".encode()).hexdigest()[:8], 16)


def _blank_report(gen, per_band: int, full_joint: bool, racket: bool) -> dict:
    return {
        "schema": "11c53dabb028-semantic-review-v1", "task_id": TASK,
        "status": "incomplete", "racket_required": racket,
        "source_hashes": {"generator": file_digest(Path(gen.__file__)), "probe": file_digest(PROBE_FILE)},
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "sampler": {"lessons_per_band": per_band, "bands": list(BANDS),
                    "train": getattr(gen, "EXAMPLES_NEEDED", 3), "test": 1,
                    "seed_recipe": "uint32 sha256('review-probe:v1:TASK:KIND:BAND:INDEX')[:8]",
                    "lesson_index_recipe": "9000 + lesson index; every requested residue modulo 6",
                    "default_draw_index_recipe": "15000 + draw index; 180 draws per band",
                    "joint_shape_domain": "all h,w in 1..15" if full_joint else "nine boundary shapes",
                    "joint_density_values": [0.0, 0.5, 1.0], "joint_multi_values": [False, True],
                    "joint_bands": [None, *BANDS]},
        "error_count": 0, "first_failures": {}, "canonical": {}, "default_draws": {},
        "lessons": {}, "joint_axes": {}, "smallest_observed_witnesses": {},
        "racket_parity": {"checked": 0, "mismatches": 0},
        "limits": [
            "Finite named-rival evidence; no universal identifiability claim.",
            "Default schedules and exact-override populations are assessed separately.",
            "Requested starts describe runner inputs; invalid or duplicate pairs can advance accepted indices.",
            "Every materialized six-pair lesson is rotated into all six query positions.",
            "Smallest observed witnesses are finite-sample minima, not proved globally minimal.",
            "The Python mirror is diagnostic; production labels and Racket parity use canonical authority.",
        ],
    }


def _failure(report: dict, kind: str, error: Any, **context) -> None:
    report["error_count"] += 1
    report["first_failures"].setdefault(kind, {"error": str(error), **context})


def _record_witness(report: dict, name: str, pair: dict, rival_output: list, authority: str) -> None:
    if pair["output"] == rival_output:
        return
    current = report["smallest_observed_witnesses"].get(name)
    grid = pair["input"]
    key = (len(grid) * len(grid[0]), len(grid), len(grid[0]), json.dumps(grid, separators=(",", ":")))
    if current is not None:
        previous = current["input"]
        old_key = (len(previous) * len(previous[0]), len(previous), len(previous[0]),
                   json.dumps(previous, separators=(",", ":")))
        if old_key <= key:
            return
    report["smallest_observed_witnesses"][name] = {
        "input": deepcopy(grid), "output": deepcopy(pair["output"]),
        "rival_output": deepcopy(rival_output), "output_authority": authority,
    }


def _run_evidence(gen, report: dict, *, per_band: int, full_joint: bool,
                  session=None, checkpoint=None, lesson_census: Path | None = None) -> dict:
    rivals = declared_rivals(gen)
    report["rivals"] = sorted(rivals)
    if getattr(gen, "EXAMPLES_NEEDED", None) != 5:
        _failure(report, "contract", "This six-position review requires EXAMPLES_NEEDED=5")
    if session:
        runner, bundle, bridge, function_name, rule_hash = session
        report["executed_rule_hash"] = rule_hash
        report["source_hashes"]["canonical_rule_source"] = hashlib.sha256(bundle.rule_source.encode()).hexdigest()
    census_rows = None
    if lesson_census is not None:
        if not session:
            raise ValueError("Census reuse requires canonical Racket source verification")
        census, census_rows = _verified_census(lesson_census, gen, per_band, bundle.rule_source)
        report["lesson_census"] = {"input_sha256": file_digest(lesson_census),
                                   "status": census["status"], "sampler": census["sampler"],
                                   "runtime_manifest_sha256": census.get("runtime_manifest_sha256")}
        report["sampler"]["lesson_index_recipe"] = "Source-bound shared census instances, with their recorded starts"
        report["sampler"]["seed_recipe"] = "Shared census recipe retained in lesson_census.sampler; local draw recipe unchanged"

    def output(grid):
        mirror = mirror_output(grid)
        if not session:
            return mirror
        bridge.define_grid("__semantic_review_input", deepcopy(grid))
        authoritative = normalize_grid(bridge.eval_text(f"({function_name} __semantic_review_input)"))
        report["racket_parity"]["checked"] += 1
        if authoritative != mirror:
            report["racket_parity"]["mismatches"] += 1
            _failure(report, "racket_parity", "Racket disagrees with diagnostic mirror",
                     input=grid, racket=authoritative, mirror=mirror)
        return authoritative

    canon = canonical_pairs()
    report["canonical"] = {"pairs": len(canon), "mirror_matches": 0, "accepted": 0,
                           "rival_fit": {name: {"fits": 0, "pairs": len(canon)} for name in rivals}}
    for index, pair in enumerate(canon):
        try:
            if mirror_output(pair["input"]) == pair["output"]:
                report["canonical"]["mirror_matches"] += 1
            else:
                _failure(report, "canonical_mirror", "Diagnostic mirror disagrees with stored canonical pair", pair_index=index)
            if output(pair["input"]) != pair["output"]:
                _failure(report, "canonical_authority", "Executed output disagrees with stored canonical pair", pair_index=index)
            reasons = gen.self_check(deepcopy(pair["input"]))
            if reasons:
                _failure(report, "canonical_acceptance", reasons, pair_index=index)
            else:
                report["canonical"]["accepted"] += 1
            predictions = rival_predictions(rivals, [pair])
            for name, values in predictions.items():
                report["canonical"]["rival_fit"][name]["fits"] += int(values[0] == pair["output"])
        except Exception as exc:
            _failure(report, "canonical_execution", f"{type(exc).__name__}: {exc}", pair_index=index)
    for name, counts in report["canonical"]["rival_fit"].items():
        if name.startswith("CANONICAL_SHORTCUTS:") and counts["fits"] != len(canon):
            _failure(report, "canonical_shortcut", "Declared canonical shortcut does not fit every canonical pair", rival=name)

    for index, grid in enumerate(decisive_inputs()):
        try:
            pair = {"input": grid, "output": output(grid)}
            for name, values in rival_predictions(rivals, [pair]).items():
                _record_witness(report, name, pair, values[0], "canonical Racket" if session else "diagnostic mirror only")
        except Exception as exc:
            _failure(report, "decisive_input", f"{type(exc).__name__}: {exc}", input_index=index)

    for band in BANDS:
        counts, roles, first_colors, shapes, unique = Counter(), Counter(), set(), set(), set()
        for index in range(180):
            seed = _seed("draw", band, index)
            try:
                grid = gen.generate(seed, 15000 + index, difficulty=band)
                normalize_grid(grid)
                reasons = gen.self_check(deepcopy(grid), difficulty=band)
                if reasons:
                    raise AssertionError(f"self_check: {reasons}")
                if grid != gen.generate(seed, 15000 + index, difficulty=band):
                    raise AssertionError("Exact replay changed input pixels")
                obs = observed(grid)
                if obs["multi_color"]:
                    values = [value for row in grid for value in row if value]
                    frequencies = Counter(values)
                    column_first = next(grid[r][c] for c in range(len(grid[0])) for r in range(len(grid)) if grid[r][c])
                    if column_first == values[0]:
                        raise AssertionError("Default multicolor witness failed row-major/column-major contrast")
                    if values[-1] == values[0]:
                        raise AssertionError("Default multicolor witness failed first/last contrast")
                    first_count = frequencies[values[0]]
                    others = [count for color, count in frequencies.items() if color != values[0]]
                    if obs["selector_role"] == "middle":
                        if first_count >= max(others):
                            raise AssertionError("Middle witness must distinguish first from the dominant color")
                        counts["middle_first_is_minority"] += 1
                    else:
                        if first_count <= max(others):
                            raise AssertionError("Extreme witness must make the first color uniquely dominant")
                        counts["extreme_first_is_unique_majority"] += 1
                roles[obs["selector_role"]] += 1
                shapes.add((obs["grid_h"], obs["grid_w"]))
                unique.add(digest(grid))
                if obs["multi_color"]:
                    first_colors.add(obs["fg_color"])
                counts["valid"] += 1
                strict = gen.strict_canonical_like(deepcopy(grid))
                counts["strict"] += int(strict if isinstance(strict, bool) else not strict)
            except Exception as exc:
                _failure(report, "default_draw", f"{type(exc).__name__}: {exc}", band=band, seed=seed, sample_index=15000 + index)
        report["default_draws"][band] = {"requested": 180, **dict(counts), "roles": dict(roles),
                                          "multicolor_first_colors": sorted(first_colors),
                                          "unique_inputs": len(unique), "shapes": [list(shape) for shape in sorted(shapes)]}

        counts, residues, unique = Counter(), Counter(), set()
        states = {name: Counter() for name in rivals}
        for index in range(per_band):
            seed = _seed("lesson", band, index)
            start = 9000 + index
            saved = census_rows[band][index] if census_rows else None
            if saved:
                seed, start = saved["seed"], saved["sample_index"]
            counts["requested"] += 1
            try:
                if session:
                    lesson = deepcopy(saved["instance"]) if saved else runner.run_one(
                        TASK, seed=seed, sample_index=start, n_train=5, n_test=1,
                        bundle=bundle, bridge=bridge, fn_name=function_name, difficulty=band)
                    pairs = lesson["train"] + lesson["test"]
                    for pair in pairs:
                        if saved:
                            report["racket_parity"]["census_pairs_reused"] = report["racket_parity"].get("census_pairs_reused", 0) + 1
                        else:
                            report["racket_parity"]["checked"] += 1
                        if pair["output"] != mirror_output(pair["input"]):
                            report["racket_parity"]["mismatches"] += 1
                            raise AssertionError("Production pair differs from diagnostic mirror")
                else:
                    grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(6)]
                    pairs = [{"input": grid, "output": mirror_output(grid)} for grid in grids]
                if len(pairs) != 6:
                    raise AssertionError(f"Expected six pairs; received {len(pairs)}")
                for pair in pairs:
                    normalize_grid(pair["input"])
                    if gen.self_check(deepcopy(pair["input"]), difficulty=band):
                        raise AssertionError("Materialized input failed self_check")
                    unique.add(digest(pair["input"]))
                if len({digest(pair["input"]) for pair in pairs}) != 6:
                    raise AssertionError("Lesson contains duplicate inputs")
                predictions = rival_predictions(rivals, pairs)
                for name, outputs in predictions.items():
                    for pair, alternative in zip(pairs, outputs):
                        _record_witness(report, name, pair, alternative, "canonical Racket" if session else "diagnostic mirror only")
                counts["materialized"] += 1
                residues[start % 6] += 1
                for query_index in range(6):
                    scored = score_query_rotation(gen, rivals, pairs, query_index, predictions)
                    counts["query_rotations"] += 1
                    for name, state in scored["rivals"].items():
                        states[name][state] += 1
                    if scored["ambiguous"]:
                        counts["ambiguous_rotations"] += 1
                        _failure(report, "lesson_ambiguity", scored["ambiguous"], band=band,
                                 seed=seed, sample_index=start, query_index=query_index, pairs=pairs)
                    if scored["hook_reasons"]:
                        counts["hook_rejected_rotations"] += 1
                        _failure(report, "lesson_hook", scored["hook_reasons"], band=band,
                                 seed=seed, sample_index=start, query_index=query_index, pairs=pairs)
            except Exception as exc:
                counts["execution_errors"] += 1
                _failure(report, "lesson_execution", f"{type(exc).__name__}: {exc}", band=band, seed=seed, sample_index=start)
            report["lessons"][band] = {**dict(counts), "unique_inputs": len(unique),
                                        "requested_start_residues": {str(i): residues[i] for i in range(6)},
                                        "rivals": {name: dict(counter) for name, counter in states.items()}}
            if checkpoint and index % 20 == 19:
                checkpoint(report)
        if checkpoint:
            checkpoint(report)
        print(f"{band}: {counts['materialized']}/{per_band} lessons, {counts['query_rotations']} query rotations", flush=True)

    joint = {}
    for index, (band, options, feasible) in enumerate(joint_cases(full_joint)):
        band_name = "default" if band is None else band
        counts = joint.setdefault(band_name, Counter())
        counts["requested"] += 1
        try:
            grid = check_joint_case(gen, band, options, feasible, index=index)
            if grid is None:
                counts["declared_infeasible_rejected"] += 1
            else:
                counts["accepted"] += 1
                counts["one_dimensional"] += int(len(grid) == 1 or len(grid[0]) == 1)
                counts["multicolor"] += int(options["multi_color"])
                output(grid)
        except Exception as exc:
            counts["errors"] += 1
            _failure(report, "joint_axes", f"{type(exc).__name__}: {exc}", band=band, options=options,
                     expected_feasible=feasible, case_index=index)
        report["joint_axes"] = {name: dict(value) for name, value in joint.items()}
        if checkpoint and index % 250 == 249:
            checkpoint(report)
    report["status"] = "failed" if report["error_count"] else "passed" if session else "diagnostic_only"
    if checkpoint:
        checkpoint(report)
    return report


def execute_probe(*, per_band: int = 100, full_joint: bool = True, racket: bool = True,
                  checkpoint=None, lesson_census: Path | str | None = None) -> dict:
    gen = load_generator()
    report = _blank_report(gen, per_band, full_joint, racket)
    if checkpoint:
        checkpoint(report)
    try:
        if racket:
            with racket_session() as session:
                return _run_evidence(gen, report, per_band=per_band, full_joint=full_joint,
                                     session=session, checkpoint=checkpoint,
                                     lesson_census=Path(lesson_census) if lesson_census else None)
        return _run_evidence(gen, report, per_band=per_band, full_joint=full_joint, checkpoint=checkpoint,
                             lesson_census=Path(lesson_census) if lesson_census else None)
    except Exception as exc:
        _failure(report, "probe_execution", f"{type(exc).__name__}: {exc}")
        report["status"] = "error"
        if checkpoint:
            checkpoint(report)
        return report


def run_probe(*, per_band: int = 100, full_joint: bool = True, racket: bool = True,
              timeout: float = 900, lesson_census: Path | str | None = None) -> dict:
    """Public reviewer entry; source checkouts use the supported copied runtime."""
    if type(per_band) is not int or per_band < 6:
        raise ValueError("per_band must be >=6 to cover every requested cyclic start")
    if IS_RUNTIME or not racket:
        return execute_probe(per_band=per_band, full_joint=full_joint, racket=racket, lesson_census=lesson_census)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-semantic-review-") as temporary:
        stage = Path(temporary)
        manifest = prepare_runtime(Catalog(ROOT), stage, TASK)
        shutil.copy2(PROBE_FILE, stage / "review_probe.py")
        request = {"per_band": per_band, "full_joint": full_joint, "racket": True}
        if lesson_census is not None:
            shutil.copy2(Path(lesson_census), stage / "source_lesson_census.json")
            request["lesson_census"] = "source_lesson_census.json"
        (stage / "review_request.json").write_text(json.dumps(request))
        execution = run_process([sys.executable, "-B", "review_probe.py", "--worker-request",
                                 "review_request.json", "--out", "review_report.json"], stage, timeout=timeout)
        result_path = stage / "review_report.json"
        report = json.loads(result_path.read_text()) if result_path.is_file() else {
            "schema": "11c53dabb028-semantic-review-v1", "task_id": TASK, "status": "error",
            "error_count": 1, "first_failures": {"worker": {"error": "Worker produced no report"}},
        }
        if execution["timed_out"] or execution["exit_code"] != 0:
            report["status"] = "error"
            _failure(report, "worker_execution", "Worker failed or timed out; partial evidence retained")
        report["runtime_manifest"] = manifest
        report["runtime_manifest_sha256"] = file_digest(stage / "RUNTIME_MANIFEST.json")
        report["execution"] = execution
        if lesson_census is not None:
            report.setdefault("lesson_census", {})["supplied_path"] = str(lesson_census)
        return report


def _checkpoint(path: Path, report: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(path)


def verify_saved_counterexample(path: Path, *, timeout: float = 120) -> dict:
    """Anchor a retained mirror-only failure with one public Catalog.apply call."""
    if IS_RUNTIME:
        raise RuntimeError("Saved-counterexample verification uses Catalog.apply from the source checkout")
    from arcpuzzles import Catalog
    retained = json.loads(path.read_text())["raw_mirror_probe"]["first_failure"]
    if retained is None:
        raise ValueError("The supplied record contains no retained counterexample")
    grids = [pair["input"] for pair in retained["pairs"]]
    query_index = retained["query"]
    applied = Catalog(ROOT).apply(TASK, grids, reference="canonical", timeout=timeout)
    if not applied["rule_hash_matches_catalog"]:
        raise AssertionError("Applied canonical source does not match the catalog")
    outputs = [normalize_grid(result["output"]) for result in applied["results"]]

    def column_major(grid):
        h, w = len(grid), len(grid[0])
        color = next(grid[r][c] for c in range(w) for r in range(h) if grid[r][c])
        tile = [[color if value == 0 else 0 for value in row] for row in grid]
        return [row + row for row in tile] + [row + row for row in tile]

    alternatives = [column_major(grid) for grid in grids]
    demo_matches = sum(alternatives[i] == outputs[i] for i in range(len(grids)) if i != query_index)
    query_disagrees = alternatives[query_index] != outputs[query_index]
    mirror_matches = sum(mirror_output(grid) == output for grid, output in zip(grids, outputs))
    canonical = canonical_pairs()
    canonical_fit = sum(column_major(pair["input"]) == pair["output"] for pair in canonical)
    passed = demo_matches == len(grids) - 1 and query_disagrees and mirror_matches == len(grids)
    return {
        "schema": "11c53dabb028-cyclic-counterexample-reference-v1", "task_id": TASK,
        "status": "verified_ambiguity" if passed else "failed",
        "input_record": {"path": str(path), "sha256": file_digest(path),
                         "band": retained["band"], "seed": retained["seed"],
                         "sample_index": retained["start"], "query_index": query_index},
        "input_generation_source_hash": None,
        "input_generation_source_note": "Original raw-probe generator hash was not captured; inputs were retained verbatim before the column-major repair.",
        "reference": applied,
        "column_major": {"canonical_fits": canonical_fit, "canonical_pairs": len(canonical),
                         "demo_matches": demo_matches, "demos": len(grids) - 1,
                         "query_disagrees": query_disagrees, "outputs": alternatives},
        "saved_mirror_matches_reference": mirror_matches,
        "probe_sha256": file_digest(PROBE_FILE),
        "limits": ["Reference generator hash records current Catalog.apply provenance, not the earlier producer of these retained inputs.",
                   "One reproduced finite cyclic ambiguity; it does not measure the frequency of all possible failures."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--quick-joint", action="store_true", help="Use nine boundary shapes instead of all 225")
    parser.add_argument("--racket", action="store_true", help="Explicitly require Racket (the default)")
    parser.add_argument("--python-only", action="store_true", help="Diagnostic mirror only; never a Racket pass")
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--lesson-census", type=Path,
                        help="Reuse a completed source-bound shared census and rotate every materialized query")
    parser.add_argument("--verify-counterexample", type=Path,
                        help="Verify a retained initial cyclic failure with one public Catalog.apply batch")
    parser.add_argument("--worker-request", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.per_band < 6:
        parser.error("--per-band must be >=6")
    if args.racket and args.python_only:
        parser.error("--racket and --python-only are mutually exclusive")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.verify_counterexample:
        report = verify_saved_counterexample(args.verify_counterexample, timeout=args.timeout)
    elif args.worker_request:
        request = json.loads(args.worker_request.read_text())
        report = execute_probe(**request, checkpoint=lambda value: _checkpoint(args.out, value))
    else:
        report = run_probe(per_band=args.per_band, full_joint=not args.quick_joint,
                           racket=not args.python_only, timeout=args.timeout, lesson_census=args.lesson_census)
    _checkpoint(args.out, report)
    print(json.dumps({"status": report["status"], "error_count": report.get("error_count"),
                      "racket_parity": report.get("racket_parity"),
                      "first_failures": report.get("first_failures")}, indent=2))
    return 0 if report["status"] in {"passed", "diagnostic_only", "verified_ambiguity"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
