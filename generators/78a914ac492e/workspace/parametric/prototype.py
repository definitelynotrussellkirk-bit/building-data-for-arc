"""Task-local scale-basis prototype for ARC generator 78a914ac492e.

The production generator and canonical authority remain unchanged.  A hidden
``scale_basis`` value is chosen once for the complete episode:

``longer_side`` (canonical/default)
    Isotropically scale the template by the larger side of the seed's common
    rectangle.

``shorter_side`` (proposed)
    Use the smaller side instead, preserving template/seed roles and color
    substitution while changing the executed geometry.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "78a914ac492e"
PARAMETER_NAME = "scale_basis"
ALLOWED_SETTINGS = ("longer_side", "shorter_side")
DEFAULT_SETTING = "longer_side"
CANONICAL_RULE_HASH = "9d9305fdca24"
_SCALE_FRAGMENT = "(if (> sh sw) sh sw)"
_SHORTER_FRAGMENT = "(if (< sh sw) sh sw)"


def _validate_setting(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {value!r}"
        )
    return value


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    root = find_root(__file__)
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row["program_solution"]
            digest = _normalized_rule_hash(source)
            if digest != CANONICAL_RULE_HASH:
                raise RuntimeError(
                    f"canonical rule hash drift: {digest} != {CANONICAL_RULE_HASH}"
                )
            return source
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


def program_for(scale_basis: str) -> str:
    """Return exact Racket source for one bounded prototype setting."""
    scale_basis = _validate_setting(scale_basis)
    source = canonical_program()
    if scale_basis == DEFAULT_SETTING:
        return source
    if source.count(_SCALE_FRAGMENT) != 1:
        raise RuntimeError("canonical scale expression changed; prototype needs review")
    return source.replace(_SCALE_FRAGMENT, _SHORTER_FRAGMENT, 1)


def _grid(value: Any) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with integer colors 0..9")
    return [list(row) for row in value]


def _objects_multicolor(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[list[tuple[int, int]]] = []
    directions = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
    )
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in directions:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append(sorted(cells))
    return objects


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_seed(grid: list[list[int]], cells: list[tuple[int, int]]) -> bool:
    colors = sorted({grid[row][col] for row, col in cells})
    if len(colors) > 2:
        return False
    for color in colors:
        colored = [(row, col) for row, col in cells if grid[row][col] == color]
        row0, col0, row1, col1 = _bbox(colored)
        if len(colored) != (row1 - row0 + 1) * (col1 - col0 + 1):
            return False
    return True


def _scale_for(seed_common: list[tuple[int, int]], template_common: list[tuple[int, int]], setting: str) -> int:
    sr0, sc0, sr1, sc1 = _bbox(seed_common)
    tr0, tc0, tr1, tc1 = _bbox(template_common)
    seed_h, seed_w = sr1 - sr0 + 1, sc1 - sc0 + 1
    template_h, template_w = tr1 - tr0 + 1, tc1 - tc0 + 1
    if seed_h % template_h or seed_w % template_w:
        raise ValueError("seed common rectangle is not an integer template scale")
    vertical, horizontal = seed_h // template_h, seed_w // template_w
    scale = max(vertical, horizontal) if setting == "longer_side" else min(vertical, horizontal)
    if scale < 1:
        raise ValueError("scale must be positive")
    return scale


def apply_python(grid: list[list[int]], scale_basis: str) -> list[list[int]]:
    """Independent authoring mirror of both bounded Racket settings."""
    scale_basis = _validate_setting(scale_basis)
    source = _grid(grid)
    height, width = len(source), len(source[0])
    objects = _objects_multicolor(source)
    templates = [cells for cells in objects if not _is_seed(source, cells)]
    seeds = [cells for cells in objects if _is_seed(source, cells)]
    if len(templates) != 1 or not seeds:
        raise ValueError("expected exactly one non-seed template and at least one seed")
    template = templates[0]
    template_colors = {source[row][col] for row, col in template}
    if len(template_colors) != 2:
        raise ValueError("template must contain exactly two colors")
    template_row0, template_col0, _, _ = _bbox(template)
    output = [list(row) for row in source]

    for seed in seeds:
        seed_colors = {source[row][col] for row, col in seed}
        shared = template_colors & seed_colors
        if len(shared) != 1 or len(seed_colors) != 2:
            raise ValueError("each seed must share exactly one template color")
        common = next(iter(shared))
        template_other = next(color for color in template_colors if color != common)
        new_color = next(color for color in seed_colors if color != common)
        seed_common = [(row, col) for row, col in seed if source[row][col] == common]
        template_common = [
            (row, col) for row, col in template if source[row][col] == common
        ]
        scale = _scale_for(seed_common, template_common, scale_basis)
        seed_row0, seed_col0, _, _ = _bbox(seed_common)
        tc_row0, tc_col0, _, _ = _bbox(template_common)
        common_local_row = tc_row0 - template_row0
        common_local_col = tc_col0 - template_col0
        out_row0 = seed_row0 - common_local_row * scale
        out_col0 = seed_col0 - common_local_col * scale

        for row, col in seed:
            output[row][col] = 0
        for row, col in template:
            value = source[row][col]
            painted = new_color if value == template_other else value
            local_row = row - template_row0
            local_col = col - template_col0
            for dr in range(scale):
                for dc in range(scale):
                    nr = out_row0 + local_row * scale + dr
                    nc = out_col0 + local_col * scale + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        output[nr][nc] = painted
    return output


def execute_racket(grid: list[list[int]], scale_basis: str) -> list[list[int]]:
    """Execute one materialized setting through the packet's protected Racket."""
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    clean = _grid(grid)
    callable_rule = wrap_rule(program_for(scale_basis))
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in clean
    ) + ")"
    with RacketBridge(timeout=20) as bridge:
        output = bridge.eval_text(f"({callable_rule} {literal})")
    return _grid(output)


PROTOTYPE_VERSION = "1.0.0"
DEFAULT_DEMOS = 3
QUERY_COUNT = 4

_DEMO_PROFILES = (
    {"name": "demo-small-wide", "size": (14, 16), "template": (0, 12), "seeds": (((2, 3), (5, 1)),)},
    {"name": "demo-small-tall", "size": (16, 18), "template": (1, 1), "seeds": (((3, 2), (7, 11)),)},
    {"name": "demo-two-orientations", "size": (18, 20), "template": (13, 2), "seeds": (((2, 3), (0, 0)), ((3, 2), (9, 13)))},
    {"name": "demo-scale-four", "size": (20, 22), "template": (1, 18), "seeds": (((2, 4), (8, 1)),)},
    {"name": "demo-two-scales", "size": (22, 24), "template": (16, 3), "seeds": (((4, 2), (0, 0)), ((2, 3), (13, 17)))},
    {"name": "demo-large-spread", "size": (24, 26), "template": (15, 3), "seeds": (((2, 4), (0, 0)), ((3, 2), (15, 19)))},
)
_QUERY_PROFILES = (
    {"name": "query-minimum", "size": (15, 17), "template": (0, 14), "seeds": (((2, 3), (6, 0)),)},
    {"name": "query-mixed-scales", "size": (21, 23), "template": (15, 2), "seeds": (((3, 2), (0, 0)), ((2, 4), (9, 15)))},
    {"name": "query-three-seeds", "size": (26, 28), "template": (17, 2), "seeds": (((4, 2), (0, 0)), ((2, 3), (0, 21)), ((3, 2), (17, 21)))},
    {"name": "query-30x30-boundaries", "size": (30, 30), "template": (14, 14), "seeds": (((2, 4), (0, 0)), ((3, 2), (0, 24)), ((2, 2), (24, 26)))},
)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_demos(demos: Any) -> int:
    if type(demos) is not int:
        raise TypeError("demos must be an integer (not bool)")
    if not 2 <= demos <= 6:
        raise ValueError("demos must be in 2..6")
    return demos


def _validate_queries(queries: Any) -> int:
    if type(queries) is not int:
        raise TypeError("queries must be an integer (not bool)")
    if queries != QUERY_COUNT:
        raise ValueError("queries must be exactly 4")
    return queries


def choose_setting(seed: int) -> str:
    seed = _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|{PARAMETER_NAME}|{PROTOTYPE_VERSION}|{seed}".encode()
    ).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def grid_digest(grid: Any) -> str:
    clean = _grid(grid)
    payload = json.dumps(clean, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _profile_colors(seed: int, pair_index: int, count: int) -> list[int]:
    import random

    digest = hashlib.sha256(
        f"{TASK_ID}|input-colors|{seed}|{pair_index}".encode()
    ).digest()
    palette = list(range(1, 10))
    random.Random(digest).shuffle(palette)
    return palette[:count]


def _paint_rect(grid: list[list[int]], row: int, col: int, height: int, width: int, color: int) -> None:
    for rr in range(row, row + height):
        for cc in range(col, col + width):
            if grid[rr][cc] != 0:
                raise RuntimeError("profile objects overlap")
            grid[rr][cc] = color


def _profile_input(seed: int, pair_index: int, profile: dict[str, Any]) -> list[list[int]]:
    height, width = profile["size"]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    colors = _profile_colors(seed, pair_index, 2 + len(profile["seeds"]))
    common, accent, *new_colors = colors
    template_row, template_col = profile["template"]
    grid[template_row][template_col] = common
    grid[template_row][template_col + 1] = accent
    grid[template_row + 1][template_col] = accent
    grid[template_row + 2][template_col] = accent

    for ((common_h, common_w), (row, col)), new_color in zip(
        profile["seeds"], new_colors
    ):
        _paint_rect(grid, row, col, common_h, common_w, common)
        if common_w > common_h:
            _paint_rect(grid, row, col + common_w, common_h, 1, new_color)
        else:
            _paint_rect(grid, row + common_h, col, 1, common_w, new_color)

    objects = _objects_multicolor(grid)
    expected_objects = 1 + len(profile["seeds"])
    if len(objects) != expected_objects:
        raise RuntimeError(
            f"profile {profile['name']} produced {len(objects)} objects; expected {expected_objects}"
        )
    if sum(not _is_seed(grid, cells) for cells in objects) != 1:
        raise RuntimeError(f"profile {profile['name']} must contain one template")
    return grid


def build_inputs(seed: int, demos: int, queries: int = QUERY_COUNT) -> list[dict[str, Any]]:
    seed = _validate_seed(seed)
    demos = _validate_demos(demos)
    _validate_queries(queries)
    profiles = list(_DEMO_PROFILES[:demos]) + list(_QUERY_PROFILES)
    rows = []
    seen: set[str] = set()
    for index, profile in enumerate(profiles):
        grid = _profile_input(seed, index, profile)
        digest = grid_digest(grid)
        if digest in seen:
            raise RuntimeError("profile sampler produced duplicate input")
        seen.add(digest)
        rows.append(
            {
                "input": grid,
                "sampling": {
                    "profile": profile["name"],
                    "pair_index": index,
                    "size": list(profile["size"]),
                    "seed_shapes": [list(shape) for shape, _ in profile["seeds"]],
                },
            }
        )
    return rows


def _racket_outputs(inputs: list[list[list[int]]]) -> dict[str, list[list[list[int]]]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    outputs = {setting: [] for setting in ALLOWED_SETTINGS}
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        names = {}
        for setting in ALLOWED_SETTINGS:
            name = f"__scale_basis_{setting}"
            bridge.eval_text(f"(define {name} {wrap_rule(program_for(setting))})")
            names[setting] = name
        for index, grid in enumerate(inputs):
            grid_name = f"__scale_basis_input_{index}"
            bridge.define_grid(grid_name, _grid(grid))
            for setting in ALLOWED_SETTINGS:
                outputs[setting].append(_grid(bridge.eval_text(f"({names[setting]} {grid_name})")))
    return outputs


def build_episode(
    seed: int,
    *,
    scale_basis: str | None = None,
    demos: int = DEFAULT_DEMOS,
    queries: int = QUERY_COUNT,
) -> dict[str, Any]:
    """Build a fixed-setting episode and execute every label in Racket."""
    seed = _validate_seed(seed)
    demos = _validate_demos(demos)
    queries = _validate_queries(queries)
    selected = choose_setting(seed) if scale_basis is None else _validate_setting(scale_basis)
    rows = build_inputs(seed, demos, queries)
    inputs = [row["input"] for row in rows]
    racket = _racket_outputs(inputs)

    pairs = []
    for index, row in enumerate(rows):
        outputs_by_setting = {
            setting: racket[setting][index] for setting in ALLOWED_SETTINGS
        }
        for setting in ALLOWED_SETTINGS:
            python_output = apply_python(row["input"], setting)
            if outputs_by_setting[setting] != python_output:
                raise RuntimeError(
                    f"Racket/Python mismatch for {row['sampling']['profile']} {setting}"
                )
        if len({grid_digest(value) for value in outputs_by_setting.values()}) != 2:
            raise RuntimeError(
                f"profile {row['sampling']['profile']} does not distinguish scale_basis"
            )
        pairs.append(
            {
                "input": row["input"],
                "output": outputs_by_setting[selected],
                "setting": selected,
                "sampling": row["sampling"],
                "outputs_by_setting": outputs_by_setting,
            }
        )

    from reviewer_support import load_selected_generator

    root = find_root(__file__)
    _, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    episode = {
        "schema": "78a914ac492e-parametric-scale-basis-episode-v1",
        "status": "proposed",
        "training_admitted": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {PARAMETER_NAME: selected},
        "program": program_for(selected),
        "program_sha256": hashlib.sha256(program_for(selected).encode()).hexdigest(),
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "train": pairs[:demos],
        "test": pairs[demos:],
    }
    errors = episode_errors(episode, replay_racket=False)
    if errors:
        raise RuntimeError("constructed invalid episode: " + "; ".join(errors))
    return episode


def episode_errors(episode: Any, *, replay_racket: bool = False) -> list[str]:
    """Validate provenance, fixed setting, labels, uniqueness and teaching."""
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict) or set(parameter) != {PARAMETER_NAME}:
        return [f"episode must declare only parameter {PARAMETER_NAME!r}"]
    try:
        selected = _validate_setting(parameter[PARAMETER_NAME])
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        return ["episode must contain 2..6 demonstrations"]
    if type(test) is not list or len(test) != QUERY_COUNT:
        return ["episode must contain exactly four queries"]
    if episode.get("program") != program_for(selected):
        return ["episode program does not match the selected setting"]

    errors: list[str] = []
    seen: set[str] = set()
    all_pairs = train + test
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict):
                errors.append(f"{split_name}[{index}] must be a mapping")
                continue
            if pair.get("setting") != selected:
                errors.append(f"{split_name}[{index}] setting drift")
            try:
                digest = grid_digest(pair.get("input"))
            except Exception as exc:
                errors.append(f"{split_name}[{index}] invalid input: {exc}")
                continue
            if digest in seen:
                errors.append(f"duplicate input at {split_name}[{index}]")
            seen.add(digest)
            expected_by_setting = {}
            try:
                for setting in ALLOWED_SETTINGS:
                    expected_by_setting[setting] = apply_python(pair["input"], setting)
            except Exception as exc:
                errors.append(f"{split_name}[{index}] outside prototype grammar: {exc}")
                continue
            if pair.get("outputs_by_setting") != expected_by_setting:
                errors.append(f"{split_name}[{index}] setting-output mismatch")
            if pair.get("output") != expected_by_setting[selected]:
                errors.append(f"{split_name}[{index}] label mismatch")
            if expected_by_setting[ALLOWED_SETTINGS[0]] == expected_by_setting[ALLOWED_SETTINGS[1]]:
                errors.append(f"{split_name}[{index}] is not setting-sensitive")
    if len(test) == QUERY_COUNT:
        last = test[-1].get("input") if isinstance(test[-1], dict) else None
        if not isinstance(last, list) or len(last) != 30 or len(last[0]) != 30:
            errors.append("fourth query must exercise a 30x30 input")

    if replay_racket and not errors:
        replay = _racket_outputs([pair["input"] for pair in all_pairs])
        for index, pair in enumerate(all_pairs):
            for setting in ALLOWED_SETTINGS:
                if replay[setting][index] != pair["outputs_by_setting"][setting]:
                    errors.append(f"pair[{index}] Racket replay mismatch for {setting}")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    from copy import deepcopy

    errors = episode_errors(episode, replay_racket=False)
    if errors:
        raise ValueError("invalid episode: " + "; ".join(errors))
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def single_query_challenge(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    from copy import deepcopy

    if type(query_index) is not int or not 0 <= query_index < QUERY_COUNT:
        raise ValueError("query_index must be an integer in 0..3")
    public = public_challenge(episode)
    return {
        "train": deepcopy(public["train"]),
        "test": [deepcopy(public["test"][query_index])],
    }


def public_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Four one-query reveals; no future inputs or total-count hint is embedded."""
    return [single_query_challenge(episode, index) for index in range(QUERY_COUNT)]


def public_identifier(episode: dict[str, Any]) -> str:
    from reviewer_support import public_challenge_id

    return public_challenge_id(public_challenge(episode))


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_artifacts(episode: dict[str, Any], out: Any) -> dict[str, Any]:
    """Atomically write a private episode, standard public view and four turns."""
    from pathlib import Path
    import shutil
    import tempfile
    from reviewer_support import public_challenge_bytes

    errors = episode_errors(episode, replay_racket=False)
    if errors:
        raise ValueError("invalid episode: " + "; ".join(errors))
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)

    public = public_challenge(episode)
    public_payload = public_challenge_bytes(public)
    public_id = _sha256_bytes(public_payload)
    public_path = f"public/{public_id}.json"
    private_path = f"private/{public_id}.json"

    turn_rows = []
    turn_payloads: dict[str, bytes] = {}
    for query_index, turn in enumerate(public_turns(episode)):
        payload = public_challenge_bytes(turn)
        turn_id = _sha256_bytes(payload)
        path = f"controller/public/{turn_id}.json"
        if path in turn_payloads:
            raise ValueError("duplicate visible sequential turn")
        turn_payloads[path] = payload
        turn_rows.append(
            {"query_index": query_index, "public_id": turn_id, "path": path}
        )

    private_payload = _json_bytes(episode)
    files = {
        public_path: _sha256_bytes(public_payload),
        private_path: _sha256_bytes(private_payload),
        **{path: _sha256_bytes(payload) for path, payload in turn_payloads.items()},
    }
    manifest = {
        "schema": "78a914ac492e-parametric-scale-basis-export-v1",
        "status": "proposed",
        "training_admitted": False,
        "task_id": TASK_ID,
        "public_id": public_id,
        "public_path": public_path,
        "private_path": private_path,
        "turns": turn_rows,
        "files": files,
        "public_filename_policy": "sha256 of exact visible bytes",
        "sequential_reveal": {
            "one_query_per_turn": True,
            "future_inputs_withheld": True,
            "total_count_hint_in_payload": False,
            "first_turn_matches_single_query_projection": True,
        },
    }
    manifest_payload = _json_bytes(manifest)

    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".scale-basis-stage-", dir=out.parent))
    try:
        for relative, payload in {
            public_path: public_payload,
            private_path: private_payload,
            **turn_payloads,
            "manifest.json": manifest_payload,
        }.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        if out.exists() or out.is_symlink():
            raise FileExistsError(out)
        stage.rename(out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest


def verify_artifacts(out: Any, *, replay_racket: bool = True) -> dict[str, Any]:
    """Verify exact inventory, public projection, private binding and labels."""
    from pathlib import Path
    from reviewer_support import public_challenge_bytes, load_selected_generator

    out = Path(out)
    if out.is_symlink() or not out.is_dir():
        raise ValueError("export must be a real directory")
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    if (
        manifest.get("schema")
        != "78a914ac492e-parametric-scale-basis-export-v1"
        or manifest.get("task_id") != TASK_ID
        or manifest.get("status") != "proposed"
        or manifest.get("training_admitted") is not False
    ):
        raise ValueError("invalid export manifest")
    files = manifest.get("files")
    turns = manifest.get("turns")
    if type(files) is not dict or type(turns) is not list or len(turns) != QUERY_COUNT:
        raise ValueError("invalid export file or turn inventory")
    expected = {"manifest.json", *files}
    actual = set()
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlinks are not permitted in an export")
        if path.is_file():
            actual.add(path.relative_to(out).as_posix())
    if actual != expected:
        raise ValueError("export inventory does not match manifest")
    for relative, expected_hash in files.items():
        path = out / relative
        actual_hash = _sha256_bytes(path.read_bytes())
        if actual_hash != expected_hash:
            kind = "public" if relative.startswith(("public/", "controller/public/")) else "private"
            raise ValueError(f"{kind} file hash mismatch: {relative}")

    private_path = manifest.get("private_path")
    public_path = manifest.get("public_path")
    public_id = manifest.get("public_id")
    if private_path not in files or public_path not in files:
        raise ValueError("manifest omits public/private episode paths")
    episode = json.loads((out / private_path).read_bytes())
    errors = episode_errors(episode, replay_racket=replay_racket)
    if errors:
        raise ValueError("private episode failed verification: " + "; ".join(errors))

    root = find_root(__file__)
    _, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if (
        episode.get("task_id") != TASK_ID
        or episode.get("status") != "proposed"
        or episode.get("training_admitted") is not False
        or episode.get("generator_source") != str(source_path.relative_to(root))
        or episode.get("generator_sha256") != source_sha256
        or episode.get("program_sha256")
        != hashlib.sha256(episode["program"].encode()).hexdigest()
    ):
        raise ValueError("private source or program binding mismatch")

    expected_public = public_challenge_bytes(public_challenge(episode))
    actual_public = (out / public_path).read_bytes()
    if actual_public != expected_public:
        raise ValueError("public challenge bytes mismatch")
    if _sha256_bytes(actual_public) != public_id:
        raise ValueError("public challenge identifier mismatch")
    if public_path != f"public/{public_id}.json":
        raise ValueError("public challenge filename mismatch")

    for expected_index, row in enumerate(turns):
        if (
            type(row) is not dict
            or row.get("query_index") != expected_index
            or row.get("path") not in files
            or row.get("public_id") is None
        ):
            raise ValueError("invalid sequential turn manifest")
        expected_turn = public_challenge_bytes(
            single_query_challenge(episode, expected_index)
        )
        actual_turn = (out / row["path"]).read_bytes()
        if actual_turn != expected_turn:
            raise ValueError(f"public sequential turn {expected_index} mismatch")
        if _sha256_bytes(actual_turn) != row["public_id"]:
            raise ValueError(f"public sequential turn {expected_index} identifier mismatch")
        if row["path"] != f"controller/public/{row['public_id']}.json":
            raise ValueError(f"public sequential turn {expected_index} filename mismatch")

    return {
        "status": "passed",
        "task_id": TASK_ID,
        "public_id": public_id,
        "demos": len(episode["train"]),
        "queries": len(episode["test"]),
        "turn_count": len(turns),
        "racket_replayed": replay_racket,
        "generator_sha256": source_sha256,
        "program_sha256": episode["program_sha256"],
    }


def _main() -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="materialize one proposed episode")
    build.add_argument("--seed", type=int, required=True)
    build.add_argument("--scale-basis", choices=ALLOWED_SETTINGS)
    build.add_argument("--demos", type=int, default=DEFAULT_DEMOS)
    build.add_argument("--queries", type=int, default=QUERY_COUNT)
    build.add_argument("--out", type=Path, required=True)
    verify = subparsers.add_parser("verify", help="verify a materialized export")
    verify.add_argument("path", type=Path)
    verify.add_argument("--no-racket", action="store_true")
    args = parser.parse_args()

    if args.command == "build":
        episode = build_episode(
            args.seed,
            scale_basis=args.scale_basis,
            demos=args.demos,
            queries=args.queries,
        )
        manifest = write_artifacts(episode, args.out)
        print(
            json.dumps(
                {
                    "status": "written",
                    "parameter": episode["parameter"],
                    "demos": len(episode["train"]),
                    "queries": len(episode["test"]),
                    "public_id": manifest["public_id"],
                    "out": str(args.out),
                },
                indent=2,
            )
        )
        return 0
    report = verify_artifacts(args.path, replay_racket=not args.no_racket)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
