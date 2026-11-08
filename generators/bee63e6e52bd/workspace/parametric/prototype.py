"""Task-local, unapproved spout-reach prototype with protected replay.

The canonical program is preserved byte-for-byte for ``full``. Other settings
only add a distance guard to its two diagonal paint sites. Retained evidence
executes labels in Racket; native candidate generation emits independently
checked Python claims for portable qualification. See README.md.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import random
import sys
from contextlib import nullcontext
from functools import lru_cache
from pathlib import Path

TASK_ID = "bee63e6e52bd"
VERSION = "spout-reach-prototype-2"
ALLOWED_REACHES = ("full", 0, 2)
DEFAULT_REACH = "full"
CANONICAL_SHA256 = "8a119729a8cfa7e439377928fd01a88ca9dd9ba1d2b570f5a82bba7839c2fe0c"
HERE = Path(__file__).resolve().parent
DEMO_SHAPES = ((12, 14), (14, 12), (16, 18), (18, 16), (20, 24), (24, 20))
QUERY_SHAPES = ((12, 18), (18, 12), (24, 24), (30, 30))
DEFAULT_SHAPES = DEMO_SHAPES + QUERY_SHAPES

for candidate in (HERE, *HERE.parents):
    for support in (
        candidate / "reviewer_support.py",
        candidate / "shared/runtime/reviewer_support.py",
    ):
        if support.is_file():
            if str(support.parent) not in sys.path:
                sys.path.insert(0, str(support.parent))
            break
    else:
        continue
    break
else:
    raise ImportError("cannot locate portable reviewer_support.py")

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

ROOT = find_root(__file__)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _exact_int(value, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}] (not bool)")
    return value


def settings(spout_reach=DEFAULT_REACH) -> dict:
    program_source(spout_reach)
    return {"spout_reach": spout_reach}


def program_source(spout_reach=DEFAULT_REACH) -> str:
    """Instantiate one exact rule; reach counts steps beyond outside tip anchors."""
    if not (
        (type(spout_reach) is str and spout_reach == "full")
        or (type(spout_reach) is int and spout_reach in (0, 2))
    ):
        raise ValueError("spout_reach must be 'full', 0, or 2 (not bool)")
    source = (HERE / "canonical-full.rkt").read_text(encoding="utf-8")
    if sha256(source.encode()) != CANONICAL_SHA256:
        raise ValueError("canonical-full.rkt differs from the retained canonical authority")
    if spout_reach == "full":
        return source
    anchor = "(if (and (>= yc 0) (< yc ww) (zero? (at grid r yc)))"
    if source.count(anchor) != 2:
        raise ValueError("canonical diagonal paint sites changed")
    # Keep the outer <tt and >bt branches intact. A failed distance guard must
    # return the unchanged row, never fall through to the mouth-flood branch.
    source = source.replace(
        anchor,
        f"(if (and (<= (- tt r) {spout_reach}) (>= yc 0) (< yc ww) (zero? (at grid r yc)))",
        1,
    )
    source = source.replace(
        anchor,
        f"(if (and (<= (- r bt) {spout_reach}) (>= yc 0) (< yc ww) (zero? (at grid r yc)))",
        1,
    )
    return source


class RacketRunner:
    """Execute exact instantiated source using the included protected bridge."""

    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=20.0, startup_timeout=60.0)
        # rule! is the ARC registration form. Binding it to identity lets the
        # exact retained source evaluate to the same callable in this bridge.
        self.bridge.eval_text("(define (rule! transformation) transformation)")
        self.bindings = {}
        self.grid_executions = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.bridge.shutdown()

    def apply(self, program: str, inputs: list) -> list:
        digest = sha256(program.encode())
        name = self.bindings.get(digest)
        if name is None:
            name = "parametric-rule-" + digest[:16]
            self.bridge.eval_text(f"(define {name} {program})")
            self.bindings[digest] = name
        outputs = []
        for grid in inputs:
            self.bridge.define_grid("parametric-input", normalize_grid(grid))
            output = self.bridge.eval_text(f"({name} parametric-input)")
            outputs.append(normalize_grid(output))
            self.grid_executions += 1
        return outputs


@lru_cache(maxsize=1)
def _reference_probe():
    path = HERE.parent / "reference_probe.py"
    spec = importlib.util.spec_from_file_location(
        "bee63e6e52bd_parametric_geometry", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ray_runways(grid) -> tuple[int, int]:
    """Count visible diagonal positions beyond each actual outside tip anchor."""
    facts = _reference_probe().shape_facts(grid)
    r0, c0, r1, c1 = facts["bbox"]
    h, w = facts["height"], facts["width"]
    before, after = facts["arm_before"], facts["arm_after"]
    side = facts["open_side"]
    if side in ("left", "right"):
        outward = c0 - 1 if side == "left" else w - c1 - 2
        return min(r0 + before - 1, outward), min(
            h - r1 + after - 2, outward
        )
    outward = r0 - 1 if side == "top" else h - r1 - 2
    return min(c0 + before - 1, outward), min(w - c1 + after - 2, outward)


def _rng(seed: int, purpose: str) -> random.Random:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    if type(purpose) is not str or not purpose:
        raise ValueError("purpose must be a nonempty string")
    return random.Random(sha256(f"{VERSION}:{seed}:{purpose}".encode()))


def choose_reach(seed: int):
    """Draw once for the episode, independently from every input draw."""
    return _rng(seed, "episode-rule").choice(ALLOWED_REACHES)


def _orient_left(grid, side: str):
    if side == "left":
        return [row[:] for row in grid]
    if side == "right":
        return [row[::-1] for row in grid]
    transposed = [list(row) for row in zip(*grid)]
    if side == "top":
        return transposed
    if side == "bottom":
        return transposed[::-1]
    raise ValueError(side)


def input_draw(
    seed: int,
    index: int,
    *,
    height: int | None = None,
    width: int | None = None,
    stream: str = "general",
) -> list:
    """Draw an exact-size lawful frame with four available steps on both rays.

    Exact dimensions are a separate parametric teaching grammar, intentionally
    larger than the canonical production profile. Both dimensions must be 12..30.
    """
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(index, "index", 0, 10**9)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    if (height is None) != (width is None):
        raise ValueError("height and width must be supplied together")
    if height is None:
        height, width = DEFAULT_SHAPES[index % len(DEFAULT_SHAPES)]
    else:
        _exact_int(height, "height", 12, 30)
        _exact_int(width, "width", 12, 30)

    sides = ["left", "right", "top", "bottom"]
    _rng(seed, f"{stream}:orientation-order").shuffle(sides)
    side = sides[index % len(sides)]
    before, after = ((1, 1), (1, 3), (3, 1), (2, 2))[index % 4]
    rng = _rng(seed, f"{stream}:input-{index}:{height}x{width}")

    # Construct a left-open frame, then rotate/refelect it. For top/bottom the
    # base dimensions are swapped so the final canvas remains exactly requested.
    base_h, base_w = (
        (height, width) if side in ("left", "right") else (width, height)
    )
    runway = 4
    r0 = runway - before + 1
    r1 = base_h + after - runway - 2
    c0, c1 = runway + 1, base_w - 1
    if r1 - r0 + 1 < before + after + 1 or c1 - c0 + 1 < 3:
        raise ValueError("requested dimensions cannot support the teaching geometry")

    color = rng.choice((1, 2, 3, 5, 6, 7, 8, 9))
    grid = [[0] * base_w for _ in range(base_h)]
    for c in range(c0, c1 + 1):
        grid[r0][c] = grid[r1][c] = color
    for r in range(r0, r1 + 1):
        grid[r][c1] = color
        if r < r0 + before or r > r1 - after:
            grid[r][c0] = color

    result = _orient_left(grid, side)
    if (len(result), len(result[0])) != (height, width):
        raise AssertionError("orientation changed the requested exact dimensions")
    facts = _reference_probe().shape_facts(result)
    if facts["open_side"] != side:
        raise AssertionError("orientation did not preserve the requested open side")
    if min(ray_runways(result)) < runway:
        raise AssertionError("prototype teaching draw lacks a four-step ray runway")
    return result


def _paint_zero(
    source: list[list[int]], out: list[list[int]], row: int, column: int
) -> None:
    """Paint one canonical yellow cell without overwriting source colors."""
    if (
        0 <= row < len(source)
        and 0 <= column < len(source[0])
        and source[row][column] == 0
    ):
        out[row][column] = 4


def predict(grid, *, spout_reach=DEFAULT_REACH) -> list[list[int]]:
    """Independent Python claim mirror used only by the native adapter.

    The protected qualification worker still executes ``program_source`` in
    Racket and rejects any disagreement.  Keeping this path subprocess-free
    makes candidate generation portable and prevents nested Racket bridges.
    """
    selected = settings(spout_reach)["spout_reach"]
    source = normalize_grid(grid)
    facts = _reference_probe().shape_facts(source)
    out = [row[:] for row in source]
    height, width = facts["height"], facts["width"]
    r0, c0, r1, c1 = facts["bbox"]
    before, after = facts["arm_before"], facts["arm_after"]
    side = facts["open_side"]
    reach = max(height, width) if selected == "full" else selected

    if side in ("left", "right"):
        top_tip = r0 + before - 1
        bottom_tip = r1 - after + 1
        mouth_c = c0 - 1 if side == "left" else c1 + 1
        for row in range(top_tip + 1, bottom_tip):
            columns = range(0, c1 + 1) if side == "left" else range(c0, width)
            for column in columns:
                _paint_zero(source, out, row, column)
        for row in (top_tip, bottom_tip):
            _paint_zero(source, out, row, mouth_c)
            interior = (
                range(c0 + 1, c1 + 1)
                if side == "left"
                else range(c0, c1)
            )
            for column in interior:
                _paint_zero(source, out, row, column)
        outward = -1 if side == "left" else 1
        for distance in range(1, reach + 1):
            _paint_zero(
                source,
                out,
                top_tip - distance,
                mouth_c + outward * distance,
            )
            _paint_zero(
                source,
                out,
                bottom_tip + distance,
                mouth_c + outward * distance,
            )
    else:
        left_tip = c0 + before - 1
        right_tip = c1 - after + 1
        mouth_r = r0 - 1 if side == "top" else r1 + 1
        for column in range(left_tip + 1, right_tip):
            rows = range(0, r1 + 1) if side == "top" else range(r0, height)
            for row in rows:
                _paint_zero(source, out, row, column)
        for column in (left_tip, right_tip):
            _paint_zero(source, out, mouth_r, column)
            interior = (
                range(r0 + 1, r1 + 1)
                if side == "top"
                else range(r0, r1)
            )
            for row in interior:
                _paint_zero(source, out, row, column)
        outward = -1 if side == "top" else 1
        for distance in range(1, reach + 1):
            _paint_zero(
                source,
                out,
                mouth_r + outward * distance,
                left_tip - distance,
            )
            _paint_zero(
                source,
                out,
                mouth_r + outward * distance,
                right_tip + distance,
            )
    return out


def _validate_request(seed, spout_reach, n_train, n_test) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(n_train, "n_train", 2, 6)
    _exact_int(n_test, "n_test", 1, 4)
    if spout_reach is not None:
        settings(spout_reach)


def sample_episode(
    seed: int,
    *,
    spout_reach=None,
    n_train=3,
    n_test=4,
) -> dict:
    """Create Python label claims; protected qualification independently replays Racket."""
    _validate_request(seed, spout_reach, n_train, n_test)
    reach = choose_reach(seed) if spout_reach is None else spout_reach
    source = program_source(reach)
    demos = [
        input_draw(seed, index, height=h, width=w, stream="demo")
        for index, (h, w) in enumerate(DEMO_SHAPES[:n_train])
    ]
    queries = [
        input_draw(seed, index, height=h, width=w, stream="query")
        for index, (h, w) in enumerate(QUERY_SHAPES[:n_test])
    ]
    inputs = demos + queries
    if len({json_bytes(grid) for grid in inputs}) != len(inputs):
        raise RuntimeError("duplicate input; no partial episode")
    outputs = [predict(grid, spout_reach=reach) for grid in inputs]
    pairs = [
        {"input": grid, "output": output} for grid, output in zip(inputs, outputs)
    ]
    return {
        "schema": "bee63e6e52bd-parametric-episode-prototype-v2",
        "seed": seed,
        "parameters": {"spout_reach": reach},
        "program": source,
        "program_solution": source,
        "program_sha256": sha256(source.encode()),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def generate_episode(
    seed: int,
    *,
    spout_reach=None,
    n_train=3,
    n_test=4,
    runner=None,
) -> dict:
    """Create a private episode whose retained labels are protected Racket results."""
    episode = sample_episode(
        seed,
        spout_reach=spout_reach,
        n_train=n_train,
        n_test=n_test,
    )
    pairs = episode["train"] + episode["test"]
    with nullcontext(runner) if runner is not None else RacketRunner() as active:
        outputs = active.apply(episode["program"], [pair["input"] for pair in pairs])
    claims = [pair["output"] for pair in pairs]
    if outputs != claims:
        raise ValueError("Python claim mirror disagrees with protected Racket")
    for pair, output in zip(pairs, outputs):
        pair["output"] = output
    return episode


def assess_identifiability(episode: dict, *, runner=None) -> dict:
    """Execute both declared rival settings on demonstrations and queries."""
    selected = episode["parameters"]["spout_reach"]
    pairs = episode["train"] + episode["test"]
    n_train = len(episode["train"])
    rivals = []
    with nullcontext(runner) if runner is not None else RacketRunner() as active:
        for rival in ALLOWED_REACHES:
            if rival == selected:
                continue
            source = program_source(rival)
            outputs = active.apply(source, [pair["input"] for pair in pairs])
            matches = [
                output == pair["output"] for output, pair in zip(outputs, pairs)
            ]
            rivals.append(
                {
                    "parameters": {"spout_reach": rival},
                    "program_sha256": sha256(source.encode()),
                    "demo_matches": matches[:n_train],
                    "query_matches": matches[n_train:],
                    "demos_distinguish": not all(matches[:n_train]),
                    "outputs": outputs,
                }
            )
    ambiguous = [
        row["parameters"] for row in rivals if not row["demos_distinguish"]
    ]
    return {
        "status": "pass" if not ambiguous else "ambiguous",
        "ambiguous_rivals": ambiguous,
        "rivals": rivals,
    }


def public_filename(episode: dict) -> str:
    """Name exports from the exact visible challenge bytes only."""
    return f"challenge-{public_challenge_id(episode)}.json"


def public_challenge(episode: dict) -> dict:
    return json.loads(public_challenge_bytes(episode))


def first_turn(episode: dict) -> dict:
    """Visible demonstrations plus query 1, with no future-query metadata."""
    return json.loads(
        public_challenge_bytes(
            {"train": episode["train"], "test": episode["test"][:1]}
        )
    )


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _canonical_source() -> str:
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("expected one unambiguous canonical program")
    return sources.pop()


def _source_hashes() -> dict[str, str]:
    _, selected_path, generator_hash = load_selected_generator(TASK_ID, root=ROOT)
    source_files = [
        Path(__file__),
        HERE / "adapter.py",
        HERE / "canonical-full.rkt",
        HERE / "promotion.json",
        HERE / "README.md",
        HERE.parent / "reference_probe.py",
        HERE.parent.parent / "tests/test_parametric.py",
        HERE.parent.parent / "tests/test_parametric_public_names.py",
    ]
    result = {
        str(path.relative_to(ROOT)): sha256(path.read_bytes())
        for path in source_files
        if path.is_file()
    }
    result[str(selected_path.relative_to(ROOT))] = generator_hash
    return result


def write_evidence(
    output: Path, *, base_seed=26023, per_setting=2, runner=None
) -> dict:
    """Write bounded reproducible evidence and exact-byte public challenges."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    _exact_int(base_seed, "base_seed", 0, 2**63 - 1)
    _exact_int(per_setting, "per_setting", 1, 8)
    if base_seed + per_setting - 1 > 2**63 - 1:
        raise ValueError("base_seed plus per_setting exceeds the supported seed range")
    output.mkdir(parents=True)
    canonical = _canonical_source()
    if canonical != program_source():
        raise ValueError("prototype default differs from the selected canonical source")

    programs = {}
    for reach in ALLOWED_REACHES:
        relative = f"private/programs/reach-{reach}.rkt"
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        source = program_source(reach)
        path.write_text(source, encoding="utf-8")
        programs[str(reach)] = {"file": relative, "sha256": sha256(source.encode())}

    source_hashes = _source_hashes()
    failures = []
    episodes = []
    with nullcontext(runner) if runner is not None else RacketRunner() as active:
        execution_start = active.grid_executions
        labeled = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        actual = active.apply(program_source(), [pair["input"] for pair in labeled])
        canonical_rows = [
            {**pair, "racket_output": result, "matches": result == pair["output"]}
            for pair, result in zip(labeled, actual)
        ]
        parity = {
            "pairs": len(labeled),
            "matches": sum(row["matches"] for row in canonical_rows),
            "program_sha256": CANONICAL_SHA256,
            "rows": canonical_rows,
        }
        if parity["pairs"] != 4 or parity["matches"] != 4:
            failures.append("default failed a canonical label or canonical coverage changed")
        _json(output / "private/canonical-parity.json", parity)

        witnesses = []
        for index, (height, width) in enumerate(QUERY_SHAPES):
            grid = input_draw(
                base_seed,
                index,
                height=height,
                width=width,
                stream="witness",
            )
            outputs = {
                str(reach): active.apply(program_source(reach), [grid])[0]
                for reach in ALLOWED_REACHES
            }
            distinct = len({json_bytes(value) for value in outputs.values()})
            facts = _reference_probe().shape_facts(grid)
            witnesses.append(
                {
                    "input": grid,
                    "facts": facts,
                    "ray_runways": ray_runways(grid),
                    "racket_outputs": outputs,
                    "distinct_outputs": distinct,
                }
            )
            if distinct != len(ALLOWED_REACHES):
                failures.append(f"witness {index} does not distinguish every reach")
        _json(output / "private/long-ray-witnesses.json", witnesses)

        for reach in ALLOWED_REACHES:
            for offset in range(per_setting):
                episode = generate_episode(
                    base_seed + offset,
                    spout_reach=reach,
                    n_train=3,
                    n_test=4,
                    runner=active,
                )
                episode["program_file"] = programs[str(reach)]["file"]
                episode["identifiability"] = assess_identifiability(
                    episode, runner=active
                )
                episode["source_sha256"] = source_hashes
                episode["public_file"] = f"public/{public_filename(episode)}"
                if episode["identifiability"]["status"] != "pass":
                    failures.append(
                        f"episode {len(episodes)} has an ambiguous declared rival"
                    )
                public_path = output / episode["public_file"]
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(public_challenge_bytes(episode))
                episodes.append(episode)
        runtime_identity = active.bridge.runtime_identity
        executions = active.grid_executions - execution_start

    private_path = output / "private/episodes.jsonl"
    private_path.write_text(
        "".join(
            json.dumps(episode, separators=(",", ":")) + "\n"
            for episode in episodes
        ),
        encoding="utf-8",
    )
    files = {
        path.relative_to(output).as_posix(): sha256(path.read_bytes())
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    report = {
        "schema": "bee63e6e52bd-parametric-prototype-evidence-v2",
        "status": "pass" if not failures else "fail",
        "scope": "proposed task-local prototype; no production or training approval",
        "version": VERSION,
        "parameter": {
            "name": "spout_reach",
            "allowed": list(ALLOWED_REACHES),
            "default": DEFAULT_REACH,
            "unit": "diagonal steps beyond the preserved outside arm-tip anchor",
        },
        "request_limits": {"demos": [2, 6], "queries": [1, 4]},
        "base_seed": base_seed,
        "per_setting": per_setting,
        "episodes": len(episodes),
        "demonstrations": sum(len(e["train"]) for e in episodes),
        "queries": sum(len(e["test"]) for e in episodes),
        "canonical_parity": {
            key: value for key, value in parity.items() if key != "rows"
        },
        "witnesses": len(witnesses),
        "max_shape": [30, 30],
        "racket_grid_executions": executions,
        "programs": programs,
        "source_sha256": source_hashes,
        "runtime_identity": runtime_identity,
        "files_sha256": files,
        "failures": failures,
        "limitations": [
            "Only the three declared reach settings and recorded seeds are evidenced.",
            "Identifiability is checked against the two other declared reaches, not every possible rule.",
            "Dedicated 12..30 canvases exceed canonical size profiles to expose at least four ray steps.",
            "Zero reach removes only diagonal continuations; outside tip anchors and canonical mouth flooding remain.",
            "This prototype changes no canonical production rule, runtime interface or approval hash.",
        ],
    }
    _json(output / "manifest.json", report)
    return report


def verify_evidence(output: Path, *, runner=None) -> dict:
    """Rebind a retained export to current sources and replay all private labels."""
    output = Path(output)
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("missing evidence manifest")
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest.get("schema")
        != "bee63e6e52bd-parametric-prototype-evidence-v2"
        or manifest.get("status") != "pass"
        or manifest.get("version") != VERSION
    ):
        raise ValueError("stale or failing evidence manifest")

    expected_files = manifest.get("files_sha256")
    if type(expected_files) is not dict or any(
        type(path) is not str or type(digest) is not str
        for path, digest in expected_files.items()
    ):
        raise ValueError("invalid evidence inventory")
    actual_files = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual_files != set(expected_files):
        raise ValueError("evidence inventory differs from manifest")
    for relative, digest in expected_files.items():
        path = output / relative
        if sha256(path.read_bytes()) != digest:
            raise ValueError(f"evidence file hash changed: {relative}")

    if _canonical_source() != program_source():
        raise ValueError("current default differs from canonical authority")
    current_sources = _source_hashes()
    if manifest.get("source_sha256") != current_sources:
        raise ValueError("prototype source binding differs from current files")

    episodes_path = output / "private/episodes.jsonl"
    episodes = [
        json.loads(line)
        for line in episodes_path.read_text().splitlines()
        if line.strip()
    ]
    if len(episodes) != manifest.get("episodes"):
        raise ValueError("private episode count differs from manifest")

    expected_public = set()
    query_count = 0
    pair_count = 0
    with nullcontext(runner) if runner is not None else RacketRunner() as active:
        if manifest.get("runtime_identity") != active.bridge.runtime_identity:
            raise ValueError("stored Racket runtime identity differs from current backend")
        for episode in episodes:
            reach = episode.get("parameters", {}).get("spout_reach")
            _validate_request(
                episode.get("seed"), reach, len(episode.get("train", [])), len(episode.get("test", []))
            )
            program = program_source(reach)
            if (
                episode.get("program") != program
                or episode.get("program_solution") != program
                or episode.get("program_sha256") != sha256(program.encode())
                or episode.get("source_sha256") != current_sources
            ):
                raise ValueError("private program or source binding differs")
            public_file = episode.get("public_file")
            expected_name = f"public/{public_filename(episode)}"
            if public_file != expected_name:
                raise ValueError("public filename is not the visible-byte content ID")
            expected_public.add(public_file)
            raw = (output / public_file).read_bytes()
            if raw != public_challenge_bytes(episode):
                raise ValueError("public challenge bytes differ from private projection")

            pairs = episode["train"] + episode["test"]
            for pair in pairs:
                normalize_grid(pair["input"])
                normalize_grid(pair["output"])
            if len({json_bytes(pair["input"]) for pair in pairs}) != len(pairs):
                raise ValueError("duplicate input in retained episode")
            actual = active.apply(program, [pair["input"] for pair in pairs])
            if actual != [pair["output"] for pair in pairs]:
                raise ValueError("private label does not replay through current Racket program")
            current_identifiability = assess_identifiability(episode, runner=active)
            if (
                current_identifiability.get("status") != "pass"
                or episode.get("identifiability") != current_identifiability
            ):
                raise ValueError("stored demonstration-only rival check differs")
            query_count += len(episode["test"])
            pair_count += len(pairs)

    actual_public = {
        path.relative_to(output).as_posix()
        for path in (output / "public").glob("*.json")
    }
    if actual_public != expected_public:
        raise ValueError("public inventory differs from private episode bindings")
    if query_count != manifest.get("queries"):
        raise ValueError("query count differs from manifest")
    return {
        "status": "pass",
        "episodes": len(episodes),
        "labeled_pairs": pair_count,
        "queries": query_count,
        "max_shape": manifest.get("max_shape"),
        "training_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=26023)
    parser.add_argument("--per-setting", type=int, default=2)
    parser.add_argument(
        "--verify", action="store_true", help="verify an existing --out directory"
    )
    args = parser.parse_args()
    if args.verify:
        report = verify_evidence(args.out)
    else:
        report = write_evidence(
            args.out, base_seed=args.seed, per_setting=args.per_setting
        )
    keys = (
        "status",
        "episodes",
        "demonstrations",
        "queries",
        "canonical_parity",
        "witnesses",
        "racket_grid_executions",
        "programs",
        "failures",
        "labeled_pairs",
        "max_shape",
    )
    print(json.dumps({key: report[key] for key in keys if key in report}, indent=2))
    return int(report["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
