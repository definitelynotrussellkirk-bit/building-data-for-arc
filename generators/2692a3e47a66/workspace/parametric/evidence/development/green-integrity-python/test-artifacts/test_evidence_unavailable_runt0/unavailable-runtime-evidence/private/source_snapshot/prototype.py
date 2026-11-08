#!/usr/bin/env python3
"""Bounded task-local parametric prototype; not a production generator API.

The default Racket program is the exact selected canonical text. Other settings
change only its component-count threshold and its per-object displacement.
All exported labels, including every competing setting, come from RacketBridge.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import uuid
from typing import Any

# Find dependencies only in this file's own library or supported copied runtime.
for _ancestor in Path(__file__).resolve().parents:
    _candidates = (_ancestor / "shared/runtime", _ancestor)
    _runtime = next((p for p in _candidates if (p / "reviewer_support.py").is_file()), None)
    if _runtime is not None:
        if str(_runtime) not in sys.path:
            sys.path.insert(0, str(_runtime))
        break
else:
    raise ImportError("The prototype requires its included reviewer_support runtime")

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

ROOT = find_root(__file__)
TASK_ID = "2692a3e47a66"
VERSION = "0.1.0-prototype"
CANONICAL_RULE_HASH = "f5a9e05539e5"
BACKGROUND = 7
PALETTE = (1, 2, 3, 4, 5, 6, 8, 9)
CORNERS = ("tl", "tr", "bl", "br")
PARAMETER_DOMAIN = {"min_repeat": (2, 3, 4), "step_blocks": (1, 2)}
DEMONSTRATIONS = 6
PAIRS_PER_EPISODE = 7


@dataclass(frozen=True, order=True)
class Settings:
    min_repeat: int = 2
    step_blocks: int = 1

    def __post_init__(self):
        for name, allowed in PARAMETER_DOMAIN.items():
            value = getattr(self, name)
            if type(value) is not int or value not in allowed:
                raise ValueError(f"{name} must be a literal integer in {allowed}, got {value!r}")

    def as_dict(self) -> dict[str, int]:
        return {"min_repeat": self.min_repeat, "step_blocks": self.step_blocks}

    @property
    def key(self) -> str:
        return f"m{self.min_repeat}_s{self.step_blocks}"


DEFAULT_SETTINGS = Settings()
ALL_SETTINGS = tuple(Settings(m, s) for m in PARAMETER_DOMAIN["min_repeat"]
                     for s in PARAMETER_DOMAIN["step_blocks"])


def _check_seed(seed: int) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")


def _rng(seed: int, purpose: str) -> random.Random:
    _check_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:{VERSION}:{seed}:{purpose}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def select_settings(seed: int) -> Settings:
    """Choose one setting deterministically for the entire episode."""
    return _rng(seed, "episode-setting").choice(ALL_SETTINGS)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    return _sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


@lru_cache(maxsize=1)
def canonical_program() -> str:
    """Stream the selected row using the public canonical-path helper."""
    matches = []
    with canonical_path(ROOT).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one canonical record for {TASK_ID}, got {len(matches)}")
    program = matches[0]["program_solution"]
    if not isinstance(program, str):
        raise ValueError("Canonical program_solution is not text")
    normalized_hash = _sha256_bytes(" ".join(program.split()).encode())[:12]
    if normalized_hash != CANONICAL_RULE_HASH:
        raise ValueError(f"Canonical rule changed: {normalized_hash}; review this prototype before use")
    return program


def emit_program(settings: Settings = DEFAULT_SETTINGS) -> str:
    """Emit exact Racket text; the default returns the original bytes as text."""
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a validated Settings instance")
    program = canonical_program()
    if settings == DEFAULT_SETTINGS:
        return program
    marker = "(length objs) 2"
    if program.count(marker) != 1:
        raise ValueError("Canonical threshold location is no longer unambiguous")
    program = program.replace(marker, f"(length objs) {settings.min_repeat}")
    if settings.step_blocks != 1:
        for delta, axis, bound, extent in (
            ("dr", "r", "h", "height"), ("dc", "c", "w", "width")
        ):
            pattern = (
                rf"(\({delta} \(if \(< \(\* 2 \(obj-{axis}1 obj\)\) {bound}\)\s+)"
                rf"{extent}(\s+)\(- {extent}\)"
            )
            replacement = (
                rf"\g<1>(* {settings.step_blocks} {extent})"
                rf"\g<2>(- (* {settings.step_blocks} {extent}))"
            )
            program, count = re.subn(pattern, replacement, program)
            if count != 1:
                raise ValueError(f"Canonical {delta} location is no longer unambiguous")
    return program


def _literal_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("cells must be literal integer ARC colors 0..9")
    return [list(row) for row in grid]


def _components(grid: list[list[int]]) -> dict[int, list[tuple[tuple[int, int], ...]]]:
    height, width = len(grid), len(grid[0])
    by_color = {}
    for color in range(10):
        if color == BACKGROUND:
            continue
        remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
        objects = []
        while remaining:
            start = min(remaining)
            remaining.remove(start)
            queue = deque([start])
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        queue.append(neighbor)
            objects.append(tuple(sorted(cells)))
        if objects:
            by_color[color] = objects
    return by_color


def _bbox(cells):
    return (
        min(r for r, c in cells), min(c for r, c in cells),
        max(r for r, c in cells), max(c for r, c in cells),
    )


def transform_mirror(grid: list[list[int]], settings: Settings = DEFAULT_SETTINGS) -> list[list[int]]:
    """Diagnostic mirror, including canonical clipping and color painter order.

    This accepts smaller grids for canonical parity/overlap diagnostics. Such
    inputs are not admitted by input_errors or sampled into prototype episodes.
    """
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a validated Settings instance")
    original = _literal_grid(grid)
    counts = Counter(cell for row in original for cell in row)
    if counts.get(BACKGROUND, 0) <= max(
        (count for color, count in counts.items() if color != BACKGROUND), default=0
    ):
        raise ValueError("diagnostic input requires unique-modal background 7")
    height, width = len(original), len(original[0])
    output = [row[:] for row in original]
    components = _components(original)
    # Freeze objects from the original grid, then preserve numeric color order
    # and each color's erase-before-paint operation exactly.
    for color in range(10):
        objects = components.get(color, ())
        if color == BACKGROUND or len(objects) < settings.min_repeat:
            continue
        for cells in objects:
            for r, c in cells:
                output[r][c] = BACKGROUND
        for cells in objects:
            r0, c0, r1, c1 = _bbox(cells)
            dr = settings.step_blocks * (r1 - r0 + 1) * (1 if 2 * r0 < height else -1)
            dc = settings.step_blocks * (c1 - c0 + 1) * (1 if 2 * c0 < width else -1)
            for r, c in cells:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = color
    return output


def input_errors(grid: Any) -> list[str]:
    """Validate the narrower 25..30, four-corner, collision-free input subset."""
    try:
        copied = _literal_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    height, width = len(copied), len(copied[0])
    errors = []
    if not 25 <= height <= 30 or not 25 <= width <= 30:
        errors.append("prototype dimensions must both be in 25..30")
    counts = Counter(cell for row in copied for cell in row)
    if counts.get(BACKGROUND, 0) <= max(
        (count for color, count in counts.items() if color != BACKGROUND), default=0
    ):
        errors.append("background 7 must be uniquely modal")
    if any(color not in (*PALETTE, BACKGROUND) for color in counts):
        errors.append("prototype foreground colors must use the declared palette")
    by_color = _components(copied)
    if sum(len(objects) for objects in by_color.values()) != 4:
        errors.append("expected exactly four foreground components")
    corners = []
    for color, objects in by_color.items():
        for cells in objects:
            r0, c0, r1, c1 = _bbox(cells)
            side = r1 - r0 + 1
            if side != c1 - c0 + 1 or not 1 <= side <= 4 or len(cells) != side * side:
                errors.append("each corner object must be a solid square of side 1..4")
            matches = []
            if r0 == 0 and c0 == 0:
                matches.append("tl")
            if r0 == 0 and c1 == width - 1:
                matches.append("tr")
            if r1 == height - 1 and c0 == 0:
                matches.append("bl")
            if r1 == height - 1 and c1 == width - 1:
                matches.append("br")
            if len(matches) != 1:
                errors.append("each object must occupy exactly one grid corner")
            else:
                corners.append(matches[0])
    if sorted(corners) != sorted(CORNERS):
        errors.append("one object is required at each of the four corners")
    if max((len(objects) for objects in by_color.values()), default=0) < 2:
        errors.append("at least one color must occupy multiple components")
    return errors


def sample_input(seed: int, sample_index: int, multiplicity: int) -> list[list[int]]:
    """Draw an input independently of the episode's hidden setting."""
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if type(multiplicity) is not int or multiplicity not in (2, 3, 4):
        raise ValueError("multiplicity must be 2, 3, or 4")
    rng = _rng(seed, f"input:{sample_index}")
    height, width = rng.randint(25, 30), rng.randint(25, 30)
    palette = rng.sample(PALETTE, 3)
    if multiplicity == 2:
        colors = ([palette[0], palette[0], palette[1], palette[1]]
                  if sample_index % 2 else [palette[0], palette[0], palette[1], palette[2]])
    elif multiplicity == 3:
        colors = [palette[0], palette[0], palette[0], palette[1]]
    else:
        colors = [palette[0]] * 4
    rng.shuffle(colors)
    sides = [rng.randint(1, 4) for _ in CORNERS]
    for color, count in Counter(colors).items():
        locations = [i for i, c in enumerate(colors) if c == color]
        if count >= 2:
            sides[locations[0]] = 1
            sides[locations[1]] = rng.randint(2, 4)
        elif multiplicity == 3:
            sides[locations[0]] = rng.randint(2, 4)
    grid = [[BACKGROUND] * width for _ in range(height)]
    for corner, color, side in zip(CORNERS, colors, sides):
        row = 0 if corner.startswith("t") else height - side
        col = 0 if corner.endswith("l") else width - side
        for r in range(row, row + side):
            for c in range(col, col + side):
                grid[r][c] = color
    errors = input_errors(grid)
    if errors:
        raise RuntimeError("sampler produced an invalid prototype input: " + "; ".join(errors))
    return grid


def plan_episode(seed: int, settings: Settings | None = None) -> dict:
    """Choose settings once and make seven distinct, setting-independent inputs."""
    _check_seed(seed)
    chosen = select_settings(seed) if settings is None else settings
    if not isinstance(chosen, Settings):
        raise ValueError("settings must be a validated Settings instance")
    rng = _rng(seed, "episode-layout")
    multiplicities = [2, 2, 3, 3, 4, 4]
    rng.shuffle(multiplicities)
    multiplicities.append(rng.choice((2, 3, 4)))
    draws, seen = [], set()
    next_index = 0
    for multiplicity in multiplicities:
        for _attempt in range(100):
            index = next_index
            next_index += 1
            grid = sample_input(seed, index, multiplicity)
            signature = grid_sha256(grid)
            if signature not in seen:
                break
        else:
            raise RuntimeError("could not produce seven distinct inputs in the bounded draw budget")
        seen.add(signature)
        draws.append({"draw_index": index, "multiplicity": multiplicity, "input": grid})
    return {
        "seed": seed, "settings": chosen.as_dict(),
        "settings_selection": "seeded_once" if settings is None else "explicit_once",
        "draws": draws,
    }


def public_challenge(pairs: list[dict], *, query_index: int = 6) -> dict:
    """Project only train input/output and one test input, using fresh grids."""
    if len(pairs) != PAIRS_PER_EPISODE or type(query_index) is not int or not 0 <= query_index < 7:
        raise ValueError("expected seven pairs and a query_index in 0..6")
    return {
        "train": [{"input": _literal_grid(pair["input"]), "output": _literal_grid(pair["output"])}
                  for i, pair in enumerate(pairs) if i != query_index],
        "test": [{"input": _literal_grid(pairs[query_index]["input"])}],
    }


class RacketLabeler:
    """One included persistent Racket process, using only public bridge methods."""

    def __init__(self):
        self.bridge = None
        self.programs = {}
        self.application_count = 0
        self.attempt_count = 0
        self.trace = []

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=30.0, startup_timeout=60.0)
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.bridge is not None:
            self.bridge.shutdown()
            self.bridge = None
        return False

    def _register(self, settings):
        if settings.key not in self.programs:
            program = emit_program(settings)
            name = f"parametric_{settings.key}"
            # rule! belongs to the authoring controller. A local identity
            # binding evaluates the complete unchanged rule! expression into a
            # callable through the supported low-level Racket bridge.
            command = f"(define {name} (let ((rule! (lambda (f) f))) {program}))"
            self.bridge.eval_text(command)
            self.programs[settings.key] = {
                "name": name, "program": program,
                "sha256": _sha256_bytes(program.encode()), "registration_command": command,
            }
        return self.programs[settings.key]

    def apply(self, grid: list[list[int]], settings: Settings) -> list[list[int]]:
        if self.bridge is None:
            raise RuntimeError("use RacketLabeler as a context manager")
        copied = _literal_grid(grid)
        if not isinstance(settings, Settings):
            raise ValueError("settings must be a validated Settings instance")
        registered = self._register(settings)
        command = f"({registered['name']} parametric_input)"
        trace = {
            "attempt_index": self.attempt_count, "settings": settings.as_dict(),
            "input_sha256": grid_sha256(copied), "rule_sha256": registered["sha256"],
            "define_grid_name": "parametric_input", "eval_text": command, "status": "started",
        }
        self.attempt_count += 1
        self.trace.append(trace)
        try:
            self.bridge.define_grid("parametric_input", copied)
            output = normalize_grid(self.bridge.eval_text(command))
            if (len(output), len(output[0])) != (len(copied), len(copied[0])):
                raise ValueError("Racket changed the grid shape")
        except Exception as exc:
            trace.update(status="error", error=f"{type(exc).__name__}: {exc}")
            raise
        self.application_count += 1
        trace.update(status="completed", output_sha256=grid_sha256(output))
        return output


def audit_predictions(chosen: Settings, pairs: list[dict], predictions: dict[str, list]) -> dict:
    """Check the same six executed setting candidates at all seven holdouts."""
    if set(predictions) != {setting.key for setting in ALL_SETTINGS}:
        raise ValueError("predictions must contain every one of the six declared settings")
    if len(pairs) != 7 or any(len(outputs) != 7 for outputs in predictions.values()):
        raise ValueError("every setting must have exactly seven complete predictions")
    pairwise = []
    for i, left in enumerate(ALL_SETTINGS):
        for right in ALL_SETTINGS[i + 1:]:
            different = [j for j in range(7) if predictions[left.key][j] != predictions[right.key][j]]
            pairwise.append({
                "left": left.as_dict(), "right": right.as_dict(),
                "different_pair_indexes": different, "difference_count": len(different),
            })
    placements = []
    for query_index in range(7):
        candidates, surviving = [], []
        for candidate in ALL_SETTINGS:
            mismatches = [i for i in range(7) if i != query_index
                          and predictions[candidate.key][i] != pairs[i]["output"]]
            if candidate != chosen and not mismatches:
                surviving.append(candidate.as_dict())
            candidates.append({
                "settings": candidate.as_dict(), "is_selected": candidate == chosen,
                "demonstrations_checked": 6, "demo_mismatch_pair_indexes": mismatches,
                "fits_demonstrations": not mismatches,
                "query_differs": predictions[candidate.key][query_index] != pairs[query_index]["output"],
            })
        selected_consistent = all(
            predictions[chosen.key][i] == pairs[i]["output"] for i in range(7)
        )
        placements.append({
            "query_index": query_index,
            "role": "production" if query_index == 6 else "rotated_holdout",
            "candidates": candidates, "selected_consistent": selected_consistent,
            "surviving_alternatives": surviving,
            "status": ("identified_within_declared_settings"
                       if selected_consistent and not surviving else "ambiguous_or_inconsistent"),
        })
    return {
        "candidate_count": 6, "alternative_count": 5, "inputs_per_candidate": 7,
        "rule_applications": 42, "query_placements": placements,
        "candidate_rotation_evaluations": 42, "alternative_rotation_evaluations": 35,
        "rotation_policy": "reuse each actual setting/input Racket result for every single-query holdout",
        "pairwise_separation": pairwise,
        "all_pairs_have_two_witnesses": all(x["difference_count"] >= 2 for x in pairwise),
        "status": ("identified_within_declared_settings"
                   if all(x["status"] == "identified_within_declared_settings" for x in placements)
                   else "ambiguous_or_inconsistent"),
    }


def generate_episode(seed: int, settings: Settings | None = None, *, labeler: RacketLabeler | None = None) -> dict:
    """Build one full episode and execute all six setting candidates."""
    plan = plan_episode(seed, settings)
    if labeler is None:
        with RacketLabeler() as owned:
            return _execute_episode(plan, owned)
    return _execute_episode(plan, labeler)


def _execute_episode(plan: dict, labeler: RacketLabeler) -> dict:
    """Execute a previously fixed plan; preserve private diagnostics on rejection."""
    if not isinstance(labeler, RacketLabeler):
        raise ValueError("episode labels require the actual included RacketLabeler")
    chosen = Settings(**plan["settings"])
    predictions = {}
    start_count = labeler.application_count
    parity_failures = []
    for candidate in ALL_SETTINGS:
        outputs = []
        for i, draw in enumerate(plan["draws"]):
            output = labeler.apply(draw["input"], candidate)
            outputs.append(output)
            if output != transform_mirror(draw["input"], candidate):
                parity_failures.append({"settings": candidate.as_dict(), "pair_index": i})
        predictions[candidate.key] = outputs
    pairs = [{"input": draw["input"], "output": predictions[chosen.key][i]}
             for i, draw in enumerate(plan["draws"])]
    audit = audit_predictions(chosen, pairs, predictions)
    actual_count = labeler.application_count - start_count
    if actual_count != 42:
        raise RuntimeError(f"expected 42 actual Racket applications, observed {actual_count}")
    audit["rule_applications"] = actual_count
    audit["mirror_parity"] = {"checked": 42, "matched": 42 - len(parity_failures),
                              "failures": parity_failures}
    private = {
        "task_id": TASK_ID, "version": VERSION, "status": "prototype",
        **plan, "pairs": pairs, "predictions": predictions, "audit": audit,
        "label_source": "included arc_repl.racket_bridge.RacketBridge",
        "rules": {candidate.key: {
            "settings": candidate.as_dict(),
            "program_sha256": _sha256_bytes(emit_program(candidate).encode()),
        } for candidate in ALL_SETTINGS},
    }
    private["accepted"] = (
        audit["status"] == "identified_within_declared_settings"
        and audit["all_pairs_have_two_witnesses"]
        and not audit["mirror_parity"]["failures"]
    )
    return {"public": public_challenge(pairs) if private["accepted"] else None,
            "private": private}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


def _source_identity() -> dict:
    task_home = ROOT / "generators" / TASK_ID
    files = {
        "prototype.py": Path(__file__).resolve(),
        "README.md": Path(__file__).resolve().with_name("README.md"),
        "test_parametric_2692a3e47a66.py": task_home / "tests/test_parametric_2692a3e47a66.py",
        "canonical_generator.py": task_home / "generator.py",
    }
    return {name: {"path": str(path.relative_to(ROOT)),
                   "sha256": _sha256_bytes(path.read_bytes())}
            for name, path in files.items()}


def _difference_cells(left, right) -> int:
    return sum(a != b for lr, rr in zip(left, right) for a, b in zip(lr, rr))


def build_evidence(out: Path, *, seed: int, episodes_per_setting: int = 1) -> dict:
    """Write new evidence; retain failures and publish only accepted episodes."""
    _check_seed(seed)
    if type(episodes_per_setting) is not int or not 1 <= episodes_per_setting <= 3:
        raise ValueError("episodes_per_setting must be a literal integer in 1..3")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    private = out / "private"
    execution = {
        "argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "TMPDIR": os.environ.get("TMPDIR"), "RACKET_PATH": os.environ.get("RACKET_PATH"),
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    report = {
        "task_id": TASK_ID, "version": VERSION, "status": "running_prototype_evidence",
        "request": {"seed": seed, "episodes_per_setting": episodes_per_setting},
        "parameter_domain": PARAMETER_DOMAIN, "default": DEFAULT_SETTINGS.as_dict(),
        "execution": execution, "canonical_rule_hash": CANONICAL_RULE_HASH,
        "episodes": [], "plans": [], "complete_episodes": 0,
        "attempted_episode_count": 0,
        "public_export_order": "randomized_independently_of_settings",
        "public_identifiers": "random_uuid4_independent_of_seed_and_settings",
        "limitations": [
            "Separate task-local prototype; no canonical source, runtime contract, approval, or training-admission change.",
            "Sampler supports only 25..30 grids, unique-modal background 7, four exact corner squares of sides 1..4, and the declared nonzero foreground palette.",
            "Canonical parity includes smaller/overlapping cases; those cases are outside the prototype sampler's support.",
            "Identifiability is finite evidence for six declared settings and the recorded seeds, not for arbitrary alternative algorithms.",
            "Query rotations reuse the 42 setting/input executions per episode; they are comparisons, not new samples or extra Racket executions.",
            "Episode content is reproducible by recorded seed/setting; public identifiers and export order intentionally use independent fresh randomness.",
        ],
    }
    labeler = None
    all_signatures = set()
    witnesses = []
    try:
        private.mkdir()
        # Persist invocation arguments before source lookup or runtime startup.
        _write_json(private / "request.json", {
            "task_id": TASK_ID, "request": report["request"], "execution": execution,
        })
        source_identity = _source_identity()
        report["source_identity"] = source_identity
        report["canonical_program_sha256"] = _sha256_bytes(canonical_program().encode())
        for name, info in source_identity.items():
            if name == "canonical_generator.py":
                continue
            target = private / "source_snapshot" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / info["path"]).read_bytes())
        for setting in ALL_SETTINGS:
            path = private / "rules" / f"{setting.key}.rkt"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                stream.write(emit_program(setting))
        planned = [
            plan_episode(seed + repetition * 6 + index, setting)
            for repetition in range(episodes_per_setting)
            for index, setting in enumerate(ALL_SETTINGS)
        ]
        planned.append(plan_episode(seed + episodes_per_setting * 6))
        # IDs and physical export order must not encode the exhaustive setting
        # enumeration. This randomness never changes a seed's puzzle content.
        random.SystemRandom().shuffle(planned)
        for episode_index, plan in enumerate(planned):
            filename = f"episode_{episode_index:03d}.json"
            _write_json(private / "plans" / filename, plan)
            report["plans"].append({
                "index": episode_index, "seed": plan["seed"],
                "settings": plan["settings"], "settings_selection": plan["settings_selection"],
                "private": f"private/plans/{filename}",
            })
        # A hard kill from here onward still leaves every seed, setting and input.
        _write_json(private / "plan_manifest.json", {
            "request": report["request"], "source_identity": source_identity,
            "plans": report["plans"], "public_export_order": report["public_export_order"],
        })
        with RacketLabeler() as labeler:
            canonical = canonical_pairs(TASK_ID, root=ROOT)
            canonical_checks = []
            for pair in canonical:
                actual = labeler.apply(pair["input"], DEFAULT_SETTINGS)
                canonical_checks.append({
                    **pair, "actual": actual, "matches": actual == pair["output"],
                    "difference_cells": _difference_cells(actual, pair["output"]),
                })
            _write_json(private / "canonical_default.json", {
                "program_sha256": report["canonical_program_sha256"],
                "default_is_exact_canonical_text": emit_program() == canonical_program(),
                "pairs_checked": len(canonical_checks), "pairs": canonical_checks,
            })
            if len(canonical_checks) != 5 or not all(x["matches"] for x in canonical_checks):
                raise RuntimeError("default Racket program did not match the complete five-pair canonical set")
            for episode_index, plan in enumerate(planned):
                report["attempted_episode_count"] += 1
                episode = _execute_episode(plan, labeler)
                evidence = episode["private"]
                evidence["source_identity"] = source_identity
                filename = f"episode_{episode_index:03d}.json"
                _write_json(private / "episodes" / filename, evidence)
                audit = evidence["audit"]
                entry = {
                    "index": episode_index, "seed": plan["seed"],
                    "settings": evidence["settings"],
                    "settings_selection": evidence["settings_selection"],
                    "private": f"private/episodes/{filename}", "public": None,
                    "status": audit["status"], "rule_applications": audit["rule_applications"],
                    "query_placements_checked": len(audit["query_placements"]),
                }
                report["episodes"].append(entry)
                signatures = {grid_sha256(x["input"]) for x in evidence["pairs"]}
                if len(signatures) != 7 or signatures & all_signatures:
                    raise RuntimeError("duplicate grid would inflate the retained episode coverage")
                if not evidence["accepted"] or episode["public"] is None:
                    raise RuntimeError(f"episode {episode_index} has ambiguity or a mirror/Racket disagreement")
                # Publish only after every acceptance check. The UUID contains
                # neither an enumeration index nor a seed/parameter-derived ID.
                public_filename = f"challenge_{uuid.uuid4().hex}.json"
                _write_json(out / "public" / public_filename, episode["public"])
                entry["public"] = f"public/{public_filename}"
                all_signatures.update(signatures)
                report["complete_episodes"] += 1
                if not witnesses:
                    for description, left, right in (
                        ("component threshold", Settings(2, 1), Settings(3, 1)),
                        ("own-block displacement multiplier", Settings(2, 1), Settings(2, 2)),
                    ):
                        index = next(i for i in range(7)
                                     if evidence["predictions"][left.key][i] != evidence["predictions"][right.key][i])
                        lhs = evidence["predictions"][left.key][index]
                        rhs = evidence["predictions"][right.key][index]
                        witnesses.append({
                            "axis": description, "episode_index": episode_index, "pair_index": index,
                            "seed": plan["seed"], "input": evidence["pairs"][index]["input"],
                            "left_settings": left.as_dict(), "right_settings": right.as_dict(),
                            "left_rule_sha256": evidence["rules"][left.key]["program_sha256"],
                            "right_rule_sha256": evidence["rules"][right.key]["program_sha256"],
                            "left_output": lhs, "right_output": rhs,
                            "different_cells": _difference_cells(lhs, rhs),
                            "input_errors": input_errors(evidence["pairs"][index]["input"]),
                        })
            _write_json(private / "witnesses.json", witnesses)
            report.update(
                status="bounded_prototype_evidence_passed",
                distinct_episode_inputs=len(all_signatures),
                canonical_pairs_checked=len(canonical_checks),
                completed_racket_applications=labeler.application_count,
                attempted_racket_applications=labeler.attempt_count,
                labels_derived_by_racket=True,
                settings_executed=len(labeler.programs),
                query_placements_checked=7 * report["complete_episodes"],
                candidate_rotation_evaluations=42 * report["complete_episodes"],
                alternative_rotation_evaluations=35 * report["complete_episodes"],
                rules=labeler.programs,
            )
    except Exception as exc:
        report.update(status="failed_or_incomplete_prototype_evidence",
                      error=f"{type(exc).__name__}: {exc}")
        if labeler is not None:
            report.update(completed_racket_applications=labeler.application_count,
                          attempted_racket_applications=labeler.attempt_count)
        report["execution"]["finished_utc"] = datetime.now(timezone.utc).isoformat()
        _write_json(private / "failure.json", report)
        raise
    finally:
        if labeler is not None:
            with (private / "racket_trace.jsonl").open("x", encoding="utf-8") as stream:
                for entry in labeler.trace:
                    stream.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
    report["execution"]["finished_utc"] = datetime.now(timezone.utc).isoformat()
    _write_json(private / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--episodes-per-setting", type=int, default=1,
                        help="1..3 explicit episodes per setting, followed by one automatically selected episode")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; must not already exist")
    args = parser.parse_args(argv)
    report = build_evidence(args.out, seed=args.seed, episodes_per_setting=args.episodes_per_setting)
    print(json.dumps({key: report[key] for key in (
        "status", "complete_episodes", "distinct_episode_inputs",
        "canonical_pairs_checked", "settings_executed",
        "completed_racket_applications", "query_placements_checked",
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
