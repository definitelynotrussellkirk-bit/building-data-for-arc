"""Task-local parametric paint-semantics prototype for 3f533a120cf5.

This module does not modify the selected production generator or its canonical
Racket authority.  It materializes only four declared rule variants at the
canonical paint-expression site.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "3f533a120cf5"
STATUS = "prototype"
PROTOTYPE_VERSION = "1.0.0"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

KEY_TARGETS = ("gray_cells", "bbox_holes")
KEY_ORDERS = ("forward", "reverse")
DEFAULT_PARAMETERS = {"key_target": "gray_cells", "key_order": "forward"}
SETTINGS = tuple(
    (key_target, key_order)
    for key_target in KEY_TARGETS
    for key_order in KEY_ORDERS
)

CANONICAL_RACKET_SHA256 = (
    "f6264cbb3adf5c325cc07efd5c4497420ad999965faecd3f55d883ffdcee8a02"
)
CANONICAL_NORMALIZED_RULE_HASH = "df7e059f3faa"
_COUNT_LIMIT = 12

_CANONICAL_PAINT_EXPRESSION = """                       (if (= (at g (+ sr1 r) (+ sc1 c)) 5)
                           (at g key-row (+ kc1 c))
                           sep-color)"""


def sha256(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_parameters(key_target: str, key_order: str) -> tuple[str, str]:
    if type(key_target) is not str:
        raise TypeError("key_target must be a plain string")
    if key_target not in KEY_TARGETS:
        raise ValueError(f"key_target must be one of {KEY_TARGETS}")
    if type(key_order) is not str:
        raise TypeError("key_order must be a plain string")
    if key_order not in KEY_ORDERS:
        raise ValueError(f"key_order must be one of {KEY_ORDERS}")
    return key_target, key_order


def canonical_rule(*, root: Path | str | None = None) -> str:
    """Load and hash-pin the selected task's exact canonical Racket source."""
    selected_root = ROOT if root is None else Path(root).resolve()
    matches: list[str] = []
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError("prototype requires exactly one selected canonical rule")
    source = matches[0]
    actual_raw = sha256(source)
    if actual_raw != CANONICAL_RACKET_SHA256:
        raise ValueError(
            "canonical Racket hash changed: "
            f"expected {CANONICAL_RACKET_SHA256}, got {actual_raw}"
        )
    normalized = " ".join(source.split())
    actual_normalized = sha256(normalized)[:12]
    if actual_normalized != CANONICAL_NORMALIZED_RULE_HASH:
        raise ValueError(
            "canonical normalized rule hash changed: "
            f"expected {CANONICAL_NORMALIZED_RULE_HASH}, got {actual_normalized}"
        )
    if source.count(_CANONICAL_PAINT_EXPRESSION) != 1:
        raise ValueError("canonical paint expression changed; reassess the prototype")
    return source


def _paint_expression(key_target: str, key_order: str) -> str:
    validate_parameters(key_target, key_order)
    if key_order == "forward":
        key_expression = "(at g key-row (+ kc1 c))"
    else:
        key_expression = "(at g key-row (+ kc1 (- (- sw 1) c)))"

    if key_target == "gray_cells":
        gray_expression, hole_expression = key_expression, "sep-color"
    else:
        gray_expression, hole_expression = "sep-color", key_expression

    return (
        "                       (if (= (at g (+ sr1 r) (+ sc1 c)) 5)\n"
        f"                           {gray_expression}\n"
        f"                           {hole_expression})"
    )


def instantiate_rule(
    key_target: str = DEFAULT_PARAMETERS["key_target"],
    key_order: str = DEFAULT_PARAMETERS["key_order"],
    *,
    root: Path | str | None = None,
) -> str:
    """Return the exact canonical/default or one declared Racket variant."""
    validate_parameters(key_target, key_order)
    source = canonical_rule(root=root)
    replacement = _paint_expression(key_target, key_order)
    if replacement == _CANONICAL_PAINT_EXPRESSION:
        return source
    variant = source.replace(_CANONICAL_PAINT_EXPRESSION, replacement, 1)
    if variant == source:
        raise ValueError("declared paint variant did not alter the canonical program")
    return variant


def restore_canonical(program: str, *, root: Path | str | None = None) -> str:
    """Accept only the four exact declared programs and return canonical source."""
    if type(program) is not str:
        raise TypeError("program must be Racket source text")
    canonical = canonical_rule(root=root)
    declared = {
        instantiate_rule(key_target, key_order, root=root)
        for key_target, key_order in SETTINGS
    }
    if program not in declared:
        raise ValueError("program is not an exact declared paint-semantics variant")
    return canonical


def _extract_rule_parts(grid: Any) -> dict[str, Any]:
    normalized = normalize_grid(grid)
    height, width = len(normalized), len(normalized[0])
    gray = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if normalized[row][column] == 5
    ]
    if not gray:
        raise ValueError("input has no gray cells")
    row_min = min(row for row, _ in gray)
    row_max = max(row for row, _ in gray)
    column_min = min(column for _, column in gray)
    column_max = max(column for _, column in gray)

    separator_row = next(
        (
            row
            for row in range(height)
            if not row_min <= row <= row_max
            and len([value for value in normalized[row] if value != 0]) > 1
            and len({value for value in normalized[row] if value != 0}) == 1
        ),
        None,
    )
    if separator_row is None:
        raise ValueError("input has no separator row")
    separator_color = next(
        (value for value in normalized[separator_row] if value != 0), None
    )
    if separator_color is None:
        raise ValueError("separator row is empty")

    above_signal = separator_row > 0 and any(
        value != 0 and value != separator_color
        for value in normalized[separator_row - 1]
    )
    key_row = separator_row - 1 if above_signal else separator_row + 1
    if not 0 <= key_row < height:
        raise ValueError("input has no adjacent key row")
    key_columns = [
        column
        for column, value in enumerate(normalized[key_row])
        if value != 0
    ]
    if not key_columns:
        raise ValueError("key row is empty")

    return {
        "grid": normalized,
        "row_min": row_min,
        "row_max": row_max,
        "column_min": column_min,
        "column_max": column_max,
        "separator_color": separator_color,
        "key_row": key_row,
        "key_left": min(key_columns),
    }


def python_transform(
    grid: Any,
    key_target: str = DEFAULT_PARAMETERS["key_target"],
    key_order: str = DEFAULT_PARAMETERS["key_order"],
) -> list[list[int]]:
    """Independent Python assertion for the four declared semantics."""
    validate_parameters(key_target, key_order)
    parts = _extract_rule_parts(grid)
    normalized = parts["grid"]
    row_min, row_max = parts["row_min"], parts["row_max"]
    column_min, column_max = parts["column_min"], parts["column_max"]
    output_width = column_max - column_min + 1

    result: list[list[int]] = []
    for row in range(row_min, row_max + 1):
        output_row: list[int] = []
        for relative_column, column in enumerate(range(column_min, column_max + 1)):
            key_offset = (
                relative_column
                if key_order == "forward"
                else output_width - 1 - relative_column
            )
            key_color = normalized[parts["key_row"]][parts["key_left"] + key_offset]
            is_gray = normalized[row][column] == 5
            key_applies = is_gray if key_target == "gray_cells" else not is_gray
            output_row.append(key_color if key_applies else parts["separator_color"])
        result.append(output_row)
    return result


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


def _setting_outputs_are_distinct(grid: Any) -> bool:
    outputs = {
        json.dumps(
            python_transform(
                grid,
                key_target=key_target,
                key_order=key_order,
            ),
            separators=(",", ":"),
        )
        for key_target, key_order in SETTINGS
    }
    return len(outputs) == len(SETTINGS)


def generate_inputs(
    seed: int, *, demo_count: int = 2, query_count: int = 4
) -> list[list[list[int]]]:
    """Generate distinct lawful inputs that expose all declared settings."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    total = demo_count + query_count
    generation_seed = 3_533_120 + seed * 10_007
    bands = ("easy", "medium", "hard", "medium")
    result: list[list[list[int]]] = []
    seen: set[str] = set()
    candidate_index = 0
    max_attempts = max(128, total * 64)
    while len(result) < total and candidate_index < max_attempts:
        grid = GEN.generate(
            generation_seed,
            candidate_index,
            difficulty=bands[candidate_index % len(bands)],
        )
        errors = GEN.self_check(grid)
        if errors:
            raise RuntimeError(
                "selected generator returned an unlawful input: " + "; ".join(errors)
            )
        identity = json.dumps(grid, separators=(",", ":"))
        if identity not in seen and _setting_outputs_are_distinct(grid):
            seen.add(identity)
            result.append(grid)
        candidate_index += 1
    if len(result) != total:
        raise RuntimeError(
            f"could not obtain {total} distinct four-way-observable inputs "
            f"within {max_attempts} attempts"
        )
    return result


def setting_id(key_target: str, key_order: str) -> str:
    validate_parameters(key_target, key_order)
    return f"{key_target}--{key_order}"


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose one declared setting once for the whole episode."""
    _validate_seed(seed)
    key_target, key_order = SETTINGS[seed % len(SETTINGS)]
    return {"key_target": key_target, "key_order": key_order}


def _normalize_parameter_mapping(parameters: dict[str, Any]) -> dict[str, str]:
    if type(parameters) is not dict or set(parameters) != {"key_target", "key_order"}:
        raise ValueError("parameters must contain exactly key_target and key_order")
    key_target, key_order = validate_parameters(
        parameters["key_target"], parameters["key_order"]
    )
    return {"key_target": key_target, "key_order": key_order}


def evaluate(
    bridge: RacketBridge, program: str, grid: Any
) -> list[list[int]]:
    """Execute one exact declared rule through the packet Racket authority."""
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's native Racket lambda")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def _compatible_settings_from_demos(
    bridge: RacketBridge, demonstrations: list[dict[str, Any]]
) -> list[str]:
    compatible: list[str] = []
    for key_target, key_order in SETTINGS:
        program = instantiate_rule(key_target, key_order)
        if all(
            evaluate(bridge, program, pair["input"]) == pair["output"]
            for pair in demonstrations
        ):
            compatible.append(setting_id(key_target, key_order))
    return compatible


def make_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    parameters: dict[str, Any] | None = None,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private episode with all labels executed in exact Racket."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    chosen = (
        choose_parameters(seed)
        if parameters is None
        else _normalize_parameter_mapping(parameters)
    )
    inputs = generate_inputs(seed, demo_count=demo_count, query_count=query_count)
    program = instantiate_rule(**chosen)

    pairs: list[dict[str, Any]] = []
    for grid in inputs:
        output = evaluate(bridge, program, grid)
        python_output = python_transform(grid, **chosen)
        if output != python_output:
            raise RuntimeError("Racket output disagrees with the independent Python assertion")
        pairs.append({"input": grid, "output": output})

    train = pairs[:demo_count]
    test = pairs[demo_count:]
    compatible = _compatible_settings_from_demos(bridge, train)
    selected = setting_id(**chosen)
    if compatible != [selected]:
        raise RuntimeError(
            "demonstrations do not uniquely identify the selected declared setting: "
            f"selected={selected}, compatible={compatible}"
        )

    return {
        "schema": "arcpuzzles-parametric-paint-semantics-private-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": chosen,
        "setting_id": selected,
        "demo_count": demo_count,
        "query_count": query_count,
        "generator_sha256": GENERATOR_SHA256,
        "canonical_racket_sha256": CANONICAL_RACKET_SHA256,
        "racket_sha256": sha256(program),
        "train": train,
        "test": test,
        "analysis": {
            "demo_compatible_settings": compatible,
            "demos_refute_all_rivals": compatible == [selected],
            "query_identifiability": [
                {
                    "query_index": index,
                    "compatible_settings_from_demos": list(compatible),
                    "identified": compatible == [selected],
                }
                for index in range(query_count)
            ],
        },
    }


_PUBLIC_NAME_RE = re.compile(r"challenge-[0-9a-f]{64}\.json\Z")


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project one private episode to demos plus unlabeled query inputs."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a mapping")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in test],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _safe_child(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe evidence path: {relative}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"evidence path escapes root: {relative}")
    return resolved


def materialize(
    output_root: Path | str,
    *,
    seed_start: int,
    episode_count: int = 4,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Write private Racket-backed episodes and opaque public projections."""
    _validate_seed(seed_start)
    _validate_count("episode_count", episode_count)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"output directory must be new or empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    private_dir = root / "private"
    public_dir = root / "public"
    rules_dir = private_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    rule_rows: list[dict[str, str]] = []
    rule_by_setting: dict[str, tuple[str, str]] = {}
    for key_target, key_order in SETTINGS:
        identifier = setting_id(key_target, key_order)
        source = instantiate_rule(key_target, key_order)
        restore_canonical(source)
        relative = f"private/rules/{identifier}.rkt"
        path = _safe_child(root, relative)
        path.write_text(source, encoding="utf-8")
        digest = sha256(source)
        rule_by_setting[identifier] = (relative, source)
        rule_rows.append(
            {
                "setting_id": identifier,
                "relative_path": relative,
                "sha256": digest,
            }
        )

    staged: list[tuple[str, dict[str, Any], bytes]] = []
    seen_public_ids: set[str] = set()
    with RacketBridge(timeout=30) as bridge:
        runtime_identity = bridge.runtime_identity
        for offset in range(episode_count):
            seed = seed_start + offset
            episode = make_episode(
                bridge,
                seed,
                demo_count=demo_count,
                query_count=query_count,
            )
            visible = public_challenge(episode)
            visible_bytes = public_challenge_bytes(visible)
            identifier = public_challenge_id(visible)
            if identifier in seen_public_ids:
                raise ValueError(f"duplicate visible challenge payload: {identifier}")
            seen_public_ids.add(identifier)
            episode["public_id"] = identifier
            episode["rule_relative_path"] = rule_by_setting[episode["setting_id"]][0]
            staged.append((identifier, episode, visible_bytes))

    episode_rows: list[dict[str, Any]] = []
    for ordinal, (identifier, episode, visible_bytes) in enumerate(
        sorted(staged, key=lambda item: item[0]), start=1
    ):
        public_relative = f"public/challenge-{identifier}.json"
        private_relative = f"private/episode-{ordinal:03d}.json"
        public_path = _safe_child(root, public_relative)
        private_path = _safe_child(root, private_relative)
        public_path.write_bytes(visible_bytes)
        _write_json(private_path, episode)
        episode_rows.append(
            {
                "public_id": identifier,
                "public_path": public_relative,
                "private_path": private_relative,
                "seed": episode["seed"],
                "setting_id": episode["setting_id"],
                "racket_sha256": episode["racket_sha256"],
            }
        )

    report: dict[str, Any] = {
        "schema": "arcpuzzles-parametric-paint-semantics-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed_start": seed_start,
        "episode_count": episode_count,
        "demo_count": demo_count,
        "query_count": query_count,
        "parameters": {
            "key_target": {
                "allowed": list(KEY_TARGETS),
                "default": DEFAULT_PARAMETERS["key_target"],
            },
            "key_order": {
                "allowed": list(KEY_ORDERS),
                "default": DEFAULT_PARAMETERS["key_order"],
            },
        },
        "source": {
            "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
            "generator_sha256": GENERATOR_SHA256,
            "canonical_racket_sha256": CANONICAL_RACKET_SHA256,
            "canonical_normalized_rule_hash": CANONICAL_NORMALIZED_RULE_HASH,
        },
        "runtime_identity": runtime_identity,
        "rules": sorted(rule_rows, key=lambda row: row["setting_id"]),
        "episodes": episode_rows,
        "limits": [
            "finite declared-rival check only",
            "prototype is not production approval or training admission",
        ],
    }
    _write_json(root / "report.json", report)
    return report


def verify_materialized(output_root: Path | str) -> dict[str, Any]:
    """Replay a materialized batch and verify labels, rivals, and projection."""
    root = Path(output_root).resolve()
    report_path = root / "report.json"
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schema") != "arcpuzzles-parametric-paint-semantics-evidence-v1":
        raise ValueError("unexpected evidence schema")
    if report.get("task_id") != TASK_ID or report.get("status") != STATUS:
        raise ValueError("evidence is not this task's prototype")
    if report.get("source", {}).get("generator_sha256") != GENERATOR_SHA256:
        raise ValueError("selected generator source hash changed")
    if report.get("source", {}).get("canonical_racket_sha256") != CANONICAL_RACKET_SHA256:
        raise ValueError("canonical Racket identity changed")

    episode_count = report.get("episode_count")
    demo_count = report.get("demo_count")
    query_count = report.get("query_count")
    _validate_count("episode_count", episode_count)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    rows = report.get("episodes")
    if type(rows) is not list or len(rows) != episode_count:
        raise ValueError("episode manifest count mismatch")
    public_ids = [row.get("public_id") for row in rows]
    if public_ids != sorted(public_ids) or len(set(public_ids)) != len(public_ids):
        raise ValueError("public episode IDs must be unique and sorted")

    rule_sources: dict[str, str] = {}
    for row in report.get("rules", []):
        identifier = row.get("setting_id")
        path = _safe_child(root, row.get("relative_path", ""))
        source = path.read_text(encoding="utf-8")
        if sha256(source) != row.get("sha256"):
            raise ValueError(f"rule hash mismatch: {identifier}")
        restore_canonical(source)
        rule_sources[identifier] = source
    expected_settings = {
        setting_id(key_target, key_order)
        for key_target, key_order in SETTINGS
    }
    if set(rule_sources) != expected_settings:
        raise ValueError("rule manifest does not contain exactly the declared settings")

    covered: set[str] = set()
    with RacketBridge(timeout=30) as bridge:
        for row in rows:
            identifier = row["public_id"]
            expected_name = f"challenge-{identifier}.json"
            public_path = _safe_child(root, row["public_path"])
            private_path = _safe_child(root, row["private_path"])
            if public_path.name != expected_name or not _PUBLIC_NAME_RE.fullmatch(public_path.name):
                raise ValueError(f"invalid public filename: {public_path.name}")
            episode = json.loads(private_path.read_text(encoding="utf-8"))
            if episode.get("public_id") != identifier:
                raise ValueError("private/public ID mismatch")
            if episode.get("demo_count") != demo_count or episode.get("query_count") != query_count:
                raise ValueError("episode pair-count metadata mismatch")
            if len(episode.get("train", [])) != demo_count or len(episode.get("test", [])) != query_count:
                raise ValueError("episode pair count mismatch")
            parameters = _normalize_parameter_mapping(episode.get("parameters"))
            selected = setting_id(**parameters)
            if episode.get("setting_id") != selected or row.get("setting_id") != selected:
                raise ValueError("episode setting identity mismatch")
            covered.add(selected)
            program = rule_sources[selected]
            if sha256(program) != episode.get("racket_sha256"):
                raise ValueError("episode Racket hash mismatch")
            if row.get("racket_sha256") != episode.get("racket_sha256"):
                raise ValueError("manifest/episode Racket hash mismatch")

            pairs = [*episode["train"], *episode["test"]]
            inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
            if len(set(inputs)) != len(inputs):
                raise ValueError("episode inputs are not distinct")
            for pair in pairs:
                racket_output = evaluate(bridge, program, pair["input"])
                if racket_output != pair["output"]:
                    raise ValueError("retained label does not match exact Racket")
                if python_transform(pair["input"], **parameters) != pair["output"]:
                    raise ValueError("retained label disagrees with Python assertion")

            compatible = _compatible_settings_from_demos(bridge, episode["train"])
            if compatible != [selected]:
                raise ValueError("demonstrations do not uniquely identify the setting")
            expected_query_analysis = [
                {
                    "query_index": index,
                    "compatible_settings_from_demos": [selected],
                    "identified": True,
                }
                for index in range(query_count)
            ]
            if episode.get("analysis", {}).get("query_identifiability") != expected_query_analysis:
                raise ValueError("query identifiability record mismatch")

            expected_public = public_challenge(episode)
            expected_bytes = public_challenge_bytes(expected_public)
            actual_bytes = public_path.read_bytes()
            if actual_bytes != expected_bytes:
                raise ValueError("public projection bytes mismatch")
            if public_challenge_id(expected_public) != identifier:
                raise ValueError("public content ID mismatch")
            public_value = json.loads(actual_bytes)
            if set(public_value) != {"train", "test"}:
                raise ValueError("public projection contains extra top-level fields")
            if any(set(pair) != {"input", "output"} for pair in public_value["train"]):
                raise ValueError("public demonstration shape mismatch")
            if any(set(pair) != {"input"} for pair in public_value["test"]):
                raise ValueError("public query leaked an answer or metadata")

    return {
        "status": "verified",
        "episode_count": episode_count,
        "demo_count": demo_count,
        "query_count": query_count,
        "all_settings_covered": covered == expected_settings,
        "all_labels_match_racket": True,
        "all_queries_identified_from_demos": True,
        "public_projection_valid": True,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    materialize_parser = commands.add_parser("materialize")
    materialize_parser.add_argument("--out", required=True, type=Path)
    materialize_parser.add_argument("--seed", required=True, type=int)
    materialize_parser.add_argument("--episode-count", type=int, default=4)
    materialize_parser.add_argument("--demo-count", type=int, default=2)
    materialize_parser.add_argument("--query-count", type=int, default=4)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--out", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize(
            args.out,
            seed_start=args.seed,
            episode_count=args.episode_count,
            demo_count=args.demo_count,
            query_count=args.query_count,
        )
    else:
        result = verify_materialized(args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
