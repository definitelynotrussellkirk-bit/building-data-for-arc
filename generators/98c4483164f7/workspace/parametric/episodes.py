"""Bounded proposed episodes and demonstrations-only finite-rival certificates."""
from __future__ import annotations
from copy import deepcopy
import json
from core import (enumerate_settings, normalize_params, params_dict, transform,
                  materialize_program, sample_input, _parse_grid)
from reviewer_support import public_challenge_bytes

SIZE_SCHEDULE = ((9, 9), (12, 16), (20, 24), (6, 6), (30, 30), (6, 30), (30, 6), (18, 25))
RIVAL_MODES = ("no_rays", "all_directions", "marker_origins", "first_marker", "one_step")

class SamplingError(ValueError):
    """Requested distinct, identifiable episode was not found within the budget."""


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rival(grid, settings, mode):
    selected = normalize_params(settings)
    h, w, cells, markers, top, left, color = _parse_grid(grid)
    directions = [(-1 if row == top else 1, -1 if col == left else 1) for row, col in markers]
    if mode == "first_marker": directions = directions[:1]
    if mode == "all_directions": directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    if mode == "no_rays": directions = []
    for _ in range(selected.quarter_turns): directions = [(dc, -dr) for dr, dc in directions]
    origins = markers if mode == "marker_origins" else cells
    out = [list(row) for row in grid]
    for row, col in cells: out[row][col] = color
    distances = (selected.stride,) if mode == "one_step" else range(selected.stride, max(h, w), selected.stride)
    for row, col in origins:
        for dr, dc in directions:
            for distance in distances:
                nr, nc = row + dr * distance, col + dc * distance
                if 0 <= nr < h and 0 <= nc < w: out[nr][nc] = color
    return out


def lesson_certificate(demos, query_inputs):
    """Fit 8 settings and 40 named shortcuts using demonstrations only.

    Query inputs are used solely to ask whether surviving rules disagree.
    No query output, selected setting, or hidden seed is accepted by this API.
    Exceptions from a hypothesis propagate; they never count as refutations.
    """
    public_challenge_bytes({"train": demos, "test": [{"input": g} for g in query_inputs]})
    hypotheses = [("setting", s) for s in enumerate_settings()]
    hypotheses += [(mode, s) for mode in RIVAL_MODES for s in enumerate_settings()]
    survivors, eliminated = [], []
    for mode, setting in hypotheses:
        witness = next((i for i, pair in enumerate(demos)
                        if (transform(pair["input"], setting) if mode == "setting"
                            else _rival(pair["input"], setting, mode)) != pair["output"]), None)
        row = {"kind": mode, "settings": setting}
        if witness is None: survivors.append(row)
        else: eliminated.append({**row, "witness_demo": witness})
    query_checks = []
    for index, grid in enumerate(query_inputs):
        predictions = set()
        for row in survivors:
            output = (transform(grid, row["settings"]) if row["kind"] == "setting"
                      else _rival(grid, row["settings"], row["kind"]))
            predictions.add(json.dumps(output, separators=(",", ":")))
        query_checks.append({"query_index": index, "prediction_classes": len(predictions),
                             "identifiable": len(predictions) == 1})
    setting_survivors = [row["settings"] for row in survivors if row["kind"] == "setting"]
    return {"schema": "marker-rays-finite-certificate-v1", "fit_basis": "demonstrations_only",
            "hypothesis_count": len(hypotheses), "setting_survivors": setting_survivors,
            "survivors": survivors, "eliminated": eliminated, "queries": query_checks,
            "identifiable": bool(setting_survivors) and all(q["identifiable"] for q in query_checks)}


def generate_episode(seed, settings=None, demos=3, queries=4, *, grid_h=None, grid_w=None, max_attempts=256):
    """Claim labels in Python; build.py independently executes protected Racket.

    Exact dimensions override a meaningful small/large/boundary shape schedule.
    Counts never silently shrink or grow. Each attempted input consumes budget;
    duplicates are skipped, and a rolling distinct window retries weak lessons.
    """
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 3, 8, "demos"); _integer(queries, 1, 8, "queries")
    _integer(max_attempts, 1, 4096, "max_attempts")
    for name, value in (("grid_h", grid_h), ("grid_w", grid_w)):
        if value is not None: _integer(value, 6, 30, name)
    chosen = params_dict(enumerate_settings()[seed % 8] if settings is None else settings)
    window, seen = [], set()
    for index in range(max_attempts):
        h, width = SIZE_SCHEDULE[index % len(SIZE_SCHEDULE)]
        grid = sample_input(seed, index, grid_h=h if grid_h is None else grid_h,
                            grid_w=width if grid_w is None else grid_w)
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen: continue
        seen.add(key)
        window.append({"input": grid, "output": transform(grid, chosen)})
        if len(window) < demos + queries: continue
        window = window[-(demos + queries):]
        train, test = window[:demos], window[demos:]
        certificate = lesson_certificate(train, [pair["input"] for pair in test])
        if certificate["setting_survivors"] == [chosen] and certificate["identifiable"]:
            return {"train": deepcopy(train), "test": deepcopy(test), "settings": chosen,
                    "seed": seed, "program_solution": materialize_program(chosen),
                    "certificate": certificate, "sampling_attempts": index + 1,
                    "status": "proposed_parametric_prototype"}
    raise SamplingError(f"no {demos}-demo/{queries}-query identifiable episode within {max_attempts} attempts")
