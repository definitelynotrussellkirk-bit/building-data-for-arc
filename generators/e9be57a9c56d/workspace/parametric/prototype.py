#!/usr/bin/env python3
"""Task-local proposed spacing variant for ARC task e9be57a9c56d.

This module is prototype evidence only. It never changes the production
``generator.py`` or the canonical Racket authority.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "e9be57a9c56d"
CANONICAL_RULE_HASH = "f8100feef807"
EXTRA_COPY_GAPS = (0, 1)
DEFAULT_EXTRA_COPY_GAP = 0
ROOT = find_root(__file__)

_FORWARD_HORIZONTAL = """(+ (second prev) t-w -1
                                                (gap i (- i 1)))"""
_FORWARD_VERTICAL = """(+ (first prev) t-h -1
                                                (gap i (- i 1)))"""
_BACKWARD_HORIZONTAL = """(+ (- (second next)
                                                   (gap (+ i 1) i)
                                                   t-w)
                                                1)"""
_BACKWARD_VERTICAL = """(+ (- (first next)
                                                   (gap (+ i 1) i)
                                                   t-h)
                                                1)"""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def catalog_rule_hash(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode("utf-8")).hexdigest()[:12]


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    return seed


def validate_extra_copy_gap(extra_copy_gap: int) -> int:
    if type(extra_copy_gap) is not int or extra_copy_gap not in EXTRA_COPY_GAPS:
        raise ValueError("extra_copy_gap must be the integer 0 or 1 (not bool)")
    return extra_copy_gap


def choose_extra_copy_gap(seed: int) -> int:
    """Choose one setting deterministically; callers hold it for the episode."""
    return EXTRA_COPY_GAPS[_validate_seed(seed) % len(EXTRA_COPY_GAPS)]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("assigned canonical Racket authority is missing or ambiguous")
    program = programs.pop()
    if catalog_rule_hash(program) != CANONICAL_RULE_HASH:
        raise ValueError("canonical Racket authority drifted; review the new source first")
    return program


def _replace_once(program: str, old: str, new: str) -> str:
    if program.count(old) != 1:
        raise ValueError("expected exactly one canonical semantic edit site")
    return program.replace(old, new)


def materialize_rule(extra_copy_gap: int = DEFAULT_EXTRA_COPY_GAP) -> str:
    """Return canonical bytes for 0; add one cell at all four chain steps for 1."""
    gap = validate_extra_copy_gap(extra_copy_gap)
    program = canonical_program()
    if gap == DEFAULT_EXTRA_COPY_GAP:
        return program

    program = _replace_once(
        program,
        _FORWARD_HORIZONTAL,
        """(+ (second prev) t-w -1
                                                (gap i (- i 1))
                                                1)""",
    )
    program = _replace_once(
        program,
        _FORWARD_VERTICAL,
        """(+ (first prev) t-h -1
                                                (gap i (- i 1))
                                                1)""",
    )
    program = _replace_once(
        program,
        _BACKWARD_HORIZONTAL,
        """(+ (- (second next)
                                                   (gap (+ i 1) i)
                                                   t-w
                                                   1)
                                                1)""",
    )
    program = _replace_once(
        program,
        _BACKWARD_VERTICAL,
        """(+ (- (first next)
                                                   (gap (+ i 1) i)
                                                   t-h
                                                   1)
                                                1)""",
    )
    return program


class RuleOracle:
    """Execute materialized rules through the packet's protected Racket bridge."""

    def __init__(self, *, timeout: float = 20.0):
        self.timeout = timeout
        self.bridge: RacketBridge | None = None
        self._defined: set[str] = set()
        self.execution_count = 0

    def __enter__(self) -> "RuleOracle":
        self.bridge = RacketBridge(timeout=self.timeout)
        self.bridge.eval_text("(define (rule! procedure) procedure)")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if self.bridge is not None:
            self.bridge.close()
            self.bridge = None
        return False

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        if self.bridge is None:
            raise RuntimeError("use RuleOracle as a context manager")
        source = normalize_grid(grid)
        digest = sha256_text(program)
        name = f"extra-copy-gap-rule-{digest}"
        if digest not in self._defined:
            self.bridge.eval_text(f"(define {name} {program})")
            self._defined.add(digest)
        self.bridge.define_grid("extra-copy-gap-input", source)
        output = normalize_grid(self.bridge.eval_text(f"({name} extra-copy-gap-input)"))
        self.execution_count += 1
        if len(output) != len(source) or len(output[0]) != len(source[0]):
            raise ValueError("reference rule changed grid dimensions unexpectedly")
        return output



def _validate_count(name: str, value: int, *, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be an integer in [{minimum}, {maximum}] (not bool)"
        )
    return value


@lru_cache(maxsize=1)
def selected_generator():
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module, source_path, source_sha256


def _derived_seed(seed: int, sample_index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}:extra-copy-gap-v1:{seed}:{sample_index}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _pad_for_extra_gap(
    grid: list[list[int]], orientation: str, n_markers: int
) -> list[list[int]]:
    margin = n_markers - 1
    if orientation == "horizontal":
        padded = [[0] * margin + list(row) + [0] * margin for row in grid]
    elif orientation == "vertical":
        width = len(grid[0])
        padded = (
            [[0] * width for _ in range(margin)]
            + [list(row) for row in grid]
            + [[0] * width for _ in range(margin)]
        )
    else:  # pragma: no cover - internal schedule owns this value
        raise ValueError(f"unknown orientation {orientation!r}")
    if len(padded) > 30 or len(padded[0]) > 30:
        raise ValueError("padded prototype input exceeds ARC's 30x30 limit")
    return padded


def _sample_input(seed: int, sample_index: int) -> tuple[list[list[int]], dict[str, int | str]]:
    generator, _source_path, _source_sha256 = selected_generator()
    orientation = "horizontal" if sample_index % 2 == 0 else "vertical"
    n_markers = 3 if sample_index % 3 else 4
    template_size = 3 + sample_index % 5
    anchor_cycle = (0, 1, n_markers - 1, max(1, n_markers - 2))
    anchor_pos = anchor_cycle[sample_index % len(anchor_cycle)]
    generation_seed = _derived_seed(seed, sample_index)
    base = generator.generate(
        generation_seed,
        sample_index,
        difficulty="easy",
        orientation=orientation,
        n_markers=n_markers,
        template_size=template_size,
        anchor_pos=anchor_pos,
    )
    padded = _pad_for_extra_gap(base, orientation, n_markers)
    diagnostics = generator.self_check(padded)
    if diagnostics:
        raise ValueError(f"sampled input left the production grammar: {diagnostics}")
    return padded, {
        "sample_index": sample_index,
        "generation_seed": generation_seed,
        "orientation": orientation,
        "n_markers": n_markers,
        "template_size": template_size,
        "anchor_pos": anchor_pos,
        "height": len(padded),
        "width": len(padded[0]),
    }


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_episode_with_oracle(
    *,
    seed: int,
    extra_copy_gap: int,
    selection: str,
    demo_count: int,
    query_count: int,
    oracle: RuleOracle,
) -> dict:
    selected_program = materialize_rule(extra_copy_gap)
    opposite_gap = 1 - extra_copy_gap
    opposite_program = materialize_rule(opposite_gap)
    needed = demo_count + query_count
    rows: list[dict] = []
    seen_inputs: set[str] = set()
    candidate_index = 0
    while len(rows) < needed and candidate_index < 256:
        source, metadata = _sample_input(seed, candidate_index)
        candidate_index += 1
        input_digest = _grid_sha256(source)
        if input_digest in seen_inputs:
            continue
        selected_output = oracle.apply(selected_program, source)
        opposite_output = oracle.apply(opposite_program, source)
        if selected_output == opposite_output:
            continue
        seen_inputs.add(input_digest)
        rows.append(
            {
                "input": source,
                "selected_output": selected_output,
                "opposite_output": opposite_output,
                "metadata": metadata,
            }
        )
    if len(rows) != needed:
        raise ValueError(
            f"could construct only {len(rows)} distinct identifying inputs; needed {needed}"
        )

    demonstrations = [
        {"input": row["input"], "output": row["selected_output"]}
        for row in rows[:demo_count]
    ]
    queries = [{"input": row["input"]} for row in rows[demo_count:]]
    query_outputs = [row["selected_output"] for row in rows[demo_count:]]
    refuted_by_demo = [
        index
        for index, row in enumerate(rows[:demo_count])
        if row["opposite_output"] != row["selected_output"]
    ]
    surviving = [] if refuted_by_demo else [f"extra_copy_gap_{opposite_gap}"]
    per_query_checks = [
        {
            "query_index": index,
            "identified_from_demonstrations": not surviving,
            "opposite_changes_query": row["opposite_output"] != row["selected_output"],
            "selected_output_sha256": _grid_sha256(row["selected_output"]),
            "opposite_output_sha256": _grid_sha256(row["opposite_output"]),
        }
        for index, row in enumerate(rows[demo_count:])
    ]
    _generator, source_path, source_sha256 = selected_generator()
    return {
        "public": {"train": demonstrations, "test": queries},
        "private": {
            "schema": "arcpuzzles-parametric-episode-v1",
            "prototype_id": f"{TASK_ID}-extra-copy-gap-v1",
            "task_id": TASK_ID,
            "seed": seed,
            "selection": selection,
            "parameters": {"extra_copy_gap": extra_copy_gap},
            "query_outputs": query_outputs,
            "selected_rule": {
                "sha256": sha256_text(selected_program),
                "catalog_hash": catalog_rule_hash(selected_program),
                "canonical_default": extra_copy_gap == DEFAULT_EXTRA_COPY_GAP,
            },
            "generator_source": {
                "path": str(Path(source_path).relative_to(ROOT)),
                "sha256": source_sha256,
            },
            "rival_fit": {
                "basis": "demonstrations_only",
                "surviving_rivals": surviving,
                "rivals": [
                    {
                        "name": f"extra_copy_gap_{opposite_gap}",
                        "extra_copy_gap": opposite_gap,
                        "rule_sha256": sha256_text(opposite_program),
                        "refuted_by_demo": refuted_by_demo,
                    }
                ],
            },
            "per_query_checks": per_query_checks,
            "input_metadata": [row["metadata"] for row in rows],
        },
    }


def build_episode(
    *,
    seed: int,
    extra_copy_gap: int | None = None,
    demo_count: int = 3,
    query_count: int = 4,
    oracle: RuleOracle | None = None,
) -> dict:
    """Build one deterministic episode with one fixed spacing rule."""
    seed = _validate_seed(seed)
    demo_count = _validate_count("demo_count", demo_count, minimum=3, maximum=8)
    query_count = _validate_count("query_count", query_count, minimum=1, maximum=16)
    if extra_copy_gap is None:
        selected_gap = choose_extra_copy_gap(seed)
        selection = "seeded_once"
    else:
        selected_gap = validate_extra_copy_gap(extra_copy_gap)
        selection = "explicit"
    if oracle is not None:
        return _build_episode_with_oracle(
            seed=seed,
            extra_copy_gap=selected_gap,
            selection=selection,
            demo_count=demo_count,
            query_count=query_count,
            oracle=oracle,
        )
    with RuleOracle() as owned_oracle:
        return _build_episode_with_oracle(
            seed=seed,
            extra_copy_gap=selected_gap,
            selection=selection,
            demo_count=demo_count,
            query_count=query_count,
            oracle=owned_oracle,
        )



def _stable_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _file_record(root: Path, path: Path) -> dict[str, str | int]:
    body = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }


def _safe_evidence_path(root: Path, relative: object, *, label: str) -> Path:
    """Resolve a manifest path only when it is canonical and stays under root."""
    if type(relative) is not str or not relative or "\\" in relative:
        raise ValueError(f"unsafe {label}: {relative!r}")
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.as_posix() != relative
    ):
        raise ValueError(f"unsafe {label}: {relative!r}")
    resolved_root = root.resolve()
    resolved = (resolved_root / Path(*pure.parts)).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"unsafe {label}: {relative!r}")
    return resolved


def _manifest_section(
    manifest: dict[str, object], name: str, errors: list[str]
) -> dict[str, object]:
    value = manifest.get(name)
    if not isinstance(value, dict):
        errors.append(f"missing or invalid manifest section: {name}")
        return {}
    return value


def verify_evidence(output: str | Path) -> dict[str, object]:
    """Recheck source bindings, retained files, and exact public-byte identity."""
    root = Path(output)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    errors: list[str] = []
    try:
        manifest_value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "errors": [f"manifest read failed: {exc}"],
            "episode_count": 0,
            "file_count": 0,
        }
    if not isinstance(manifest_value, dict):
        return {
            "ok": False,
            "errors": ["manifest root must be an object"],
            "episode_count": 0,
            "file_count": 0,
        }
    manifest: dict[str, object] = manifest_value

    if manifest.get("schema") != "arcpuzzles-parametric-evidence-v1":
        errors.append("evidence schema mismatch")
    if manifest.get("task_id") != TASK_ID:
        errors.append("task ID mismatch")
    expected_prototype_id = f"{TASK_ID}-extra-copy-gap-v1"
    if manifest.get("prototype_id") != expected_prototype_id:
        errors.append("prototype ID mismatch")

    canonical_binding = _manifest_section(manifest, "canonical_rule", errors)
    current_canonical = canonical_program()
    if canonical_binding.get("sha256") != sha256_text(current_canonical):
        errors.append("canonical rule hash mismatch")
    if canonical_binding.get("catalog_hash") != catalog_rule_hash(current_canonical):
        errors.append("canonical catalog hash mismatch")

    generator_binding = _manifest_section(manifest, "generator_source", errors)
    current_generator, current_generator_path, _loaded_sha = load_selected_generator(
        TASK_ID, root=ROOT
    )
    del current_generator, _loaded_sha
    current_generator_path = Path(current_generator_path).resolve()
    expected_generator_path = current_generator_path.relative_to(ROOT.resolve()).as_posix()
    current_generator_sha = hashlib.sha256(current_generator_path.read_bytes()).hexdigest()
    if generator_binding.get("path") != expected_generator_path:
        errors.append("generator source path mismatch")
    if generator_binding.get("sha256") != current_generator_sha:
        errors.append("generator source hash mismatch")

    prototype_binding = _manifest_section(manifest, "prototype_source", errors)
    current_prototype_path = Path(__file__).resolve()
    expected_prototype_path = current_prototype_path.relative_to(ROOT.resolve()).as_posix()
    current_prototype_sha = hashlib.sha256(current_prototype_path.read_bytes()).hexdigest()
    if prototype_binding.get("path") != expected_prototype_path:
        errors.append("prototype source path mismatch")
    if prototype_binding.get("sha256") != current_prototype_sha:
        errors.append("prototype source hash mismatch")

    file_records_value = manifest.get("files", [])
    if not isinstance(file_records_value, list):
        errors.append("manifest files must be a list")
        file_records: list[object] = []
    else:
        file_records = file_records_value
    recorded_paths: set[str] = set()
    for index, record_value in enumerate(file_records):
        if not isinstance(record_value, dict):
            errors.append(f"invalid file record at index {index}")
            continue
        relative = record_value.get("path")
        try:
            path = _safe_evidence_path(root, relative, label="file path")
        except ValueError as exc:
            errors.append(str(exc))
            continue
        assert isinstance(relative, str)
        if relative in recorded_paths:
            errors.append(f"duplicate file record: {relative}")
            continue
        recorded_paths.add(relative)
        if not path.is_file():
            errors.append(f"missing file: {relative}")
            continue
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != record_value.get("sha256"):
            errors.append(f"hash mismatch: {relative}")
        expected_bytes = record_value.get("bytes")
        if type(expected_bytes) is not int or expected_bytes != len(body):
            errors.append(f"byte count mismatch: {relative}")

    episode_values = manifest.get("episodes", [])
    if not isinstance(episode_values, list):
        errors.append("manifest episodes must be a list")
        episode_rows: list[object] = []
    else:
        episode_rows = episode_values
    ids: list[str] = []
    manifest_generator_binding = {
        "path": expected_generator_path,
        "sha256": current_generator_sha,
    }
    demo_count = manifest.get("demo_count")
    query_count = manifest.get("query_count")
    for index, row_value in enumerate(episode_rows):
        if not isinstance(row_value, dict):
            errors.append(f"invalid episode row at index {index}")
            continue
        public_relative = row_value.get("public_path")
        private_relative = row_value.get("private_path")
        try:
            public_path = _safe_evidence_path(
                root, public_relative, label="public episode path"
            )
            private_path = _safe_evidence_path(
                root, private_relative, label="private episode path"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        assert isinstance(public_relative, str)
        assert isinstance(private_relative, str)
        if public_relative not in recorded_paths:
            errors.append(f"unrecorded public episode file: {public_relative}")
        if private_relative not in recorded_paths:
            errors.append(f"unrecorded private episode file: {private_relative}")
        try:
            public_bytes = public_path.read_bytes()
            private_bytes = private_path.read_bytes()
            public = json.loads(public_bytes.decode("utf-8"))
            private = json.loads(private_bytes.decode("utf-8"))
        except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"episode read failed: {exc}")
            continue
        if not isinstance(public, dict) or not isinstance(private, dict):
            errors.append(f"episode payload must be an object: row {index}")
            continue
        try:
            actual_id = public_challenge_id(public)
            canonical_public_bytes = public_challenge_bytes(public)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"invalid public challenge at row {index}: {exc}")
            continue
        ids.append(actual_id)
        if actual_id != row_value.get("public_challenge_id"):
            errors.append(f"public ID mismatch: {public_relative}")
        if public_path.name != f"challenge-{actual_id}.json":
            errors.append(f"public filename mismatch: {public_relative}")
        if public_bytes != canonical_public_bytes:
            errors.append(f"public bytes are not canonical: {public_relative}")
        if private.get("public_challenge_id") != actual_id:
            errors.append(f"private/public binding mismatch: {private_relative}")
        if private.get("public_path") != public_relative:
            errors.append(f"private public-path binding mismatch: {private_relative}")

        train = public.get("train")
        test = public.get("test")
        if not isinstance(train, list) or type(demo_count) is not int or len(train) != demo_count:
            errors.append(f"demonstration count mismatch: {public_relative}")
        if not isinstance(test, list) or type(query_count) is not int or len(test) != query_count:
            errors.append(f"query count mismatch: {public_relative}")
        elif any(not isinstance(pair, dict) or set(pair) != {"input"} for pair in test):
            errors.append(f"public query label leak or malformed query: {public_relative}")

        episode_private = private.get("episode_private")
        if not isinstance(episode_private, dict):
            errors.append(f"missing private episode payload: {private_relative}")
            continue
        if episode_private.get("generator_source") != manifest_generator_binding:
            errors.append(f"private generator binding mismatch: {private_relative}")
        query_outputs = episode_private.get("query_outputs")
        if (
            not isinstance(query_outputs, list)
            or type(query_count) is not int
            or len(query_outputs) != query_count
        ):
            errors.append(f"private query output count mismatch: {private_relative}")
        try:
            gap = validate_extra_copy_gap(row_value.get("extra_copy_gap"))
        except ValueError as exc:
            errors.append(f"invalid episode parameter at row {index}: {exc}")
            continue
        parameters = episode_private.get("parameters")
        if parameters != {"extra_copy_gap": gap}:
            errors.append(f"private parameter binding mismatch: {private_relative}")
        selected_rule = episode_private.get("selected_rule")
        if not isinstance(selected_rule, dict):
            errors.append(f"missing selected rule binding: {private_relative}")
        else:
            expected_program = materialize_rule(gap)
            if selected_rule.get("sha256") != sha256_text(expected_program):
                errors.append(f"selected rule hash mismatch: {private_relative}")
            if selected_rule.get("catalog_hash") != catalog_rule_hash(expected_program):
                errors.append(f"selected rule catalog hash mismatch: {private_relative}")

    if len(ids) != len(set(ids)):
        errors.append("duplicate visible payload IDs")
    if ids != sorted(ids):
        errors.append("episode manifest is not sorted by public ID")
    return {
        "ok": not errors,
        "errors": errors,
        "episode_count": len(ids),
        "file_count": len(file_records),
    }


def write_evidence(
    output: str | Path,
    *,
    seeds: list[int] | tuple[int, ...],
    extra_copy_gaps: list[int] | tuple[int, ...] | None = None,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict:
    """Write source-bound public/private prototype evidence, failing closed."""
    root = Path(output)
    if root.exists():
        raise FileExistsError(f"output directory already exists: {root}")
    seeds = list(seeds)
    if not seeds:
        raise ValueError("at least one seed is required")
    seeds = [_validate_seed(seed) for seed in seeds]
    demo_count = _validate_count("demo_count", demo_count, minimum=3, maximum=8)
    query_count = _validate_count("query_count", query_count, minimum=1, maximum=16)

    if extra_copy_gaps is None:
        settings: list[int | None] = [None] * len(seeds)
    else:
        settings = list(extra_copy_gaps)
        if len(settings) != len(seeds):
            raise ValueError("seeds and extra_copy_gaps must have the same length")
        settings = [validate_extra_copy_gap(value) for value in settings]

    prepared: list[dict[str, object]] = []
    canonical_checks: list[dict[str, object]] = []
    with RuleOracle() as oracle:
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            prediction = oracle.apply(materialize_rule(0), pair["input"])
            if prediction != pair["output"]:
                raise ValueError(
                    f"canonical replay failed for variant {pair['variant']} "
                    f"{pair['split']} pair {pair['pair_index']}"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "output_sha256": _grid_sha256(pair["output"]),
                }
            )

        seen_public_ids: set[str] = set()
        for seed, setting in zip(seeds, settings):
            episode = build_episode(
                seed=seed,
                extra_copy_gap=setting,
                demo_count=demo_count,
                query_count=query_count,
                oracle=oracle,
            )
            public = episode["public"]
            identifier = public_challenge_id(public)
            if identifier in seen_public_ids:
                raise ValueError(f"duplicate visible payload: {identifier}")
            seen_public_ids.add(identifier)
            prepared.append(
                {
                    "seed": seed,
                    "extra_copy_gap": episode["private"]["parameters"]["extra_copy_gap"],
                    "public_challenge_id": identifier,
                    "public_bytes": public_challenge_bytes(public),
                    "private": episode["private"],
                }
            )
        racket_grid_executions = oracle.execution_count

    prepared.sort(key=lambda row: row["public_challenge_id"])
    root.mkdir(parents=True)
    public_dir = root / "public"
    episode_dir = root / "private" / "episodes"
    rule_dir = root / "private" / "rules"
    public_dir.mkdir(parents=True)
    episode_dir.mkdir(parents=True)
    rule_dir.mkdir(parents=True)

    written: list[Path] = []
    for gap in EXTRA_COPY_GAPS:
        path = rule_dir / f"extra-copy-gap-{gap}.rkt"
        path.write_text(materialize_rule(gap), encoding="utf-8")
        written.append(path)

    episode_rows: list[dict[str, object]] = []
    for index, row in enumerate(prepared):
        identifier = str(row["public_challenge_id"])
        public_path = public_dir / f"challenge-{identifier}.json"
        private_path = episode_dir / f"episode-{index:03d}.json"
        public_path.write_bytes(row["public_bytes"])
        private_payload = {
            "public_challenge_id": identifier,
            "public_path": public_path.relative_to(root).as_posix(),
            "episode_private": row["private"],
        }
        private_path.write_bytes(_stable_json_bytes(private_payload))
        written.extend((public_path, private_path))
        episode_rows.append(
            {
                "seed": row["seed"],
                "extra_copy_gap": row["extra_copy_gap"],
                "public_challenge_id": identifier,
                "public_path": public_path.relative_to(root).as_posix(),
                "private_path": private_path.relative_to(root).as_posix(),
            }
        )

    generator, source_path, source_sha256 = selected_generator()
    del generator
    prototype_path = Path(__file__).resolve()
    manifest = {
        "schema": "arcpuzzles-parametric-evidence-v1",
        "prototype_id": f"{TASK_ID}-extra-copy-gap-v1",
        "scope": "proposed_unapproved_task_local_prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "extra_copy_gap",
            "values": list(EXTRA_COPY_GAPS),
            "canonical_default": DEFAULT_EXTRA_COPY_GAP,
            "selection": "one fixed value per episode",
        },
        "demo_count": demo_count,
        "query_count": query_count,
        "canonical_rule": {
            "catalog_hash": CANONICAL_RULE_HASH,
            "sha256": sha256_text(canonical_program()),
        },
        "generator_source": {
            "path": str(Path(source_path).relative_to(ROOT)),
            "sha256": source_sha256,
        },
        "prototype_source": {
            "path": str(prototype_path.relative_to(ROOT)),
            "sha256": hashlib.sha256(prototype_path.read_bytes()).hexdigest(),
        },
        "canonical_checks": canonical_checks,
        "racket_grid_executions": racket_grid_executions,
        "episodes": episode_rows,
        "files": sorted(
            (_file_record(root, path) for path in written),
            key=lambda record: record["path"],
        ),
    }
    (root / "manifest.json").write_bytes(_stable_json_bytes(manifest))
    verification = verify_evidence(root)
    if not verification["ok"]:
        raise ValueError(f"written evidence failed verification: {verification['errors']}")
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--extra-copy-gaps", nargs="+", type=int, choices=EXTRA_COPY_GAPS)
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=args.seeds,
        extra_copy_gaps=args.extra_copy_gaps,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(
        json.dumps(
            {
                "out": str(Path(args.out)),
                "episodes": len(manifest["episodes"]),
                "demo_count": manifest["demo_count"],
                "query_count": manifest["query_count"],
                "racket_grid_executions": manifest["racket_grid_executions"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
