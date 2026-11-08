"""Task-local, unapproved spout-reach prototype; labels execute in Racket.

The canonical program is preserved byte-for-byte for ``full``. Other settings
only add a distance guard to its two diagonal paint sites. See README.md.
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
VERSION = "spout-reach-prototype-1"
ALLOWED_REACHES = ("full", 0, 2)
DEFAULT_REACH = "full"
CANONICAL_SHA256 = "8a119729a8cfa7e439377928fd01a88ca9dd9ba1d2b570f5a82bba7839c2fe0c"
HERE = Path(__file__).resolve().parent

for candidate in (HERE, *HERE.parents):
    for support in (candidate / "reviewer_support.py", candidate / "shared/runtime/reviewer_support.py"):
        if support.is_file():
            if str(support.parent) not in sys.path:
                sys.path.insert(0, str(support.parent))
            break
    else:
        continue
    break
else:
    raise ImportError("cannot locate portable reviewer_support.py")

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

ROOT = find_root(__file__)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def program_source(spout_reach=DEFAULT_REACH) -> str:
    """Instantiate one exact rule; reach counts steps beyond outside tip anchors."""
    if not ((type(spout_reach) is str and spout_reach == "full") or
            (type(spout_reach) is int and spout_reach in (0, 2))):
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
    source = source.replace(anchor, f"(if (and (<= (- tt r) {spout_reach}) (>= yc 0) (< yc ww) (zero? (at grid r yc)))", 1)
    source = source.replace(anchor, f"(if (and (<= (- r bt) {spout_reach}) (>= yc 0) (< yc ww) (zero? (at grid r yc)))", 1)
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
    spec = importlib.util.spec_from_file_location("bee63e6e52bd_parametric_geometry", path)
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
        return min(r0 + before - 1, outward), min(h - r1 + after - 2, outward)
    outward = r0 - 1 if side == "top" else h - r1 - 2
    return min(c0 + before - 1, outward), min(w - c1 + after - 2, outward)


def _rng(seed: int, purpose: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
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


def input_draw(seed: int, index: int) -> list:
    """Draw a lawful frame with at least four available steps on both rays."""
    rng = _rng(seed, f"input-{index}")
    sides = ["left", "right", "top", "bottom"]
    _rng(seed, "orientation-order").shuffle(sides)
    side = sides[index % len(sides)]
    before, after = ((1, 1), (1, 3), (3, 1), (2, 2))[index % 4]
    frame_height = max(5, before + after + rng.randint(1, 4))
    frame_width = rng.randint(3, 7)
    r0, c0 = rng.randint(4, 6), rng.randint(5, 7)
    r1, c1 = r0 + frame_height - 1, c0 + frame_width - 1
    h, w = r1 + 1 + rng.randint(4, 6), c1 + 1 + rng.randint(0, 3)
    color = rng.choice((1, 2, 3, 5, 6, 7, 8, 9))
    grid = [[0] * w for _ in range(h)]
    for c in range(c0, c1 + 1):
        grid[r0][c] = grid[r1][c] = color
    for r in range(r0, r1 + 1):
        grid[r][c1] = color
        if r < r0 + before or r > r1 - after:
            grid[r][c0] = color
    result = _orient_left(grid, side)
    if min(ray_runways(result)) < 4:
        raise AssertionError("prototype teaching draw lacks a distinguishing ray runway")
    return result


def generate_episode(seed: int, *, spout_reach=None, n_train=3, n_test=1, runner=None) -> dict:
    """Create a complete private episode; parameter selection precedes all pairs."""
    if type(n_train) is not int or n_train < 1 or type(n_test) is not int or n_test < 1:
        raise ValueError("n_train and n_test must be positive integers")
    reach = choose_reach(seed) if spout_reach is None else spout_reach
    source = program_source(reach)
    inputs = [input_draw(seed, index) for index in range(n_train + n_test)]
    with nullcontext(runner) if runner is not None else RacketRunner() as active:
        outputs = active.apply(source, inputs)
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, outputs)]
    return {
        "schema": "bee63e6e52bd-parametric-episode-prototype-v1",
        "seed": seed,
        "parameters": {"spout_reach": reach},
        "program": source,
        "program_sha256": sha256(source.encode()),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def assess_identifiability(episode: dict, *, runner=None) -> dict:
    """Execute both declared rival settings on every demonstration and query."""
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
            matches = [output == pair["output"] for output, pair in zip(outputs, pairs)]
            rivals.append({
                "parameters": {"spout_reach": rival},
                "program_sha256": sha256(source.encode()),
                "demo_matches": matches[:n_train],
                "query_matches": matches[n_train:],
                "demos_distinguish": not all(matches[:n_train]),
                "outputs": outputs,
            })
    ambiguous = [row["parameters"] for row in rivals if not row["demos_distinguish"]]
    return {"status": "pass" if not ambiguous else "ambiguous", "ambiguous_rivals": ambiguous, "rivals": rivals}


def public_challenge(episode: dict) -> dict:
    return {"train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]]}


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


def write_evidence(output: Path, *, base_seed=26023, per_setting=2, runner=None) -> dict:
    """Write bounded reproducible evidence and clean public challenges; refuse overwrite."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    if type(per_setting) is not int or per_setting < 1:
        raise ValueError("per_setting must be a positive integer")
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

    _, selected_path, generator_hash = load_selected_generator(TASK_ID, root=ROOT)
    source_files = [Path(__file__), HERE / "canonical-full.rkt", HERE / "README.md",
                    HERE.parent / "reference_probe.py", HERE.parent.parent / "tests/test_parametric.py"]
    source_hashes = {str(path.relative_to(ROOT)): sha256(path.read_bytes()) for path in source_files if path.is_file()}
    source_hashes[str(selected_path.relative_to(ROOT))] = generator_hash
    failures = []
    episodes = []
    with nullcontext(runner) if runner is not None else RacketRunner() as active:
        execution_start = active.grid_executions
        labeled = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        actual = active.apply(program_source(), [pair["input"] for pair in labeled])
        canonical_rows = [{**pair, "racket_output": result, "matches": result == pair["output"]}
                          for pair, result in zip(labeled, actual)]
        parity = {"pairs": len(labeled), "matches": sum(row["matches"] for row in canonical_rows),
                  "program_sha256": CANONICAL_SHA256, "rows": canonical_rows}
        if parity["pairs"] != 4 or parity["matches"] != 4:
            failures.append("default failed a canonical label or canonical coverage changed")
        _json(output / "private/canonical-parity.json", parity)

        witnesses = []
        for index in range(4):
            grid = input_draw(base_seed, index)
            outputs = {str(reach): active.apply(program_source(reach), [grid])[0] for reach in ALLOWED_REACHES}
            distinct = len({json.dumps(value) for value in outputs.values()})
            facts = _reference_probe().shape_facts(grid)
            witnesses.append({"input": grid, "facts": facts, "ray_runways": ray_runways(grid),
                              "racket_outputs": outputs, "distinct_outputs": distinct})
            if distinct != len(ALLOWED_REACHES):
                failures.append(f"witness {index} does not distinguish every reach")
        _json(output / "private/long-ray-witnesses.json", witnesses)

        # Same seeds and inputs for each setting make parameter effects directly
        # comparable; the public filenames are opaque sequential episode IDs.
        for reach in ALLOWED_REACHES:
            for offset in range(per_setting):
                episode = generate_episode(base_seed + offset, spout_reach=reach, runner=active)
                episode["program_file"] = programs[str(reach)]["file"]
                episode["identifiability"] = assess_identifiability(episode, runner=active)
                episode["source_sha256"] = source_hashes
                episode["public_file"] = f"public/episode-{len(episodes):03d}.json"
                if episode["identifiability"]["status"] != "pass":
                    failures.append(f"episode {len(episodes)} has an ambiguous declared rival")
                _json(output / episode["public_file"], public_challenge(episode))
                episodes.append(episode)
        runtime_identity = active.bridge.runtime_identity
        executions = active.grid_executions - execution_start
    private_path = output / "private/episodes.jsonl"
    private_path.write_text("".join(json.dumps(episode, separators=(",", ":")) + "\n" for episode in episodes), encoding="utf-8")
    files = {path.relative_to(output).as_posix(): sha256(path.read_bytes())
             for path in sorted(output.rglob("*")) if path.is_file()}
    report = {
        "schema": "bee63e6e52bd-parametric-prototype-evidence-v1",
        "status": "pass" if not failures else "fail",
        "scope": "proposed task-local prototype; no production or training approval",
        "version": VERSION,
        "parameter": {"name": "spout_reach", "allowed": list(ALLOWED_REACHES), "default": DEFAULT_REACH,
                      "unit": "diagonal steps beyond the preserved outside arm-tip anchor"},
        "base_seed": base_seed,
        "per_setting": per_setting,
        "episodes": len(episodes),
        "demonstrations": sum(len(e["train"]) for e in episodes),
        "queries": sum(len(e["test"]) for e in episodes),
        "canonical_parity": {key: value for key, value in parity.items() if key != "rows"},
        "witnesses": len(witnesses),
        "racket_grid_executions": executions,
        "programs": programs,
        "source_sha256": source_hashes,
        "runtime_identity": runtime_identity,
        "files_sha256": files,
        "failures": failures,
        "limitations": [
            "Only the three declared reach settings and recorded seeds are evidenced.",
            "Identifiability is checked against the two other declared reaches, not every possible rule.",
            "Dedicated canvases exceed canonical size profiles to expose at least four ray steps.",
            "Zero reach removes only diagonal continuations; outside tip anchors and canonical mouth flooding remain.",
            "This prototype changes no canonical production rule, runtime interface or approval hash; production generator repairs are separate.",
        ],
    }
    _json(output / "manifest.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=26023)
    parser.add_argument("--per-setting", type=int, default=2)
    args = parser.parse_args()
    report = write_evidence(args.out, base_seed=args.seed, per_setting=args.per_setting)
    print(json.dumps({key: report[key] for key in (
        "status", "episodes", "demonstrations", "queries", "canonical_parity",
        "witnesses", "racket_grid_executions", "programs", "failures")}, indent=2))
    return int(report["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
