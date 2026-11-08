"""Proposed episode-fixed payload reflection; labels always come from Racket.

Run through review.py run so imports and the packet's Racket are selected.
This task-local authoring tool does not register or approve a production rule.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sys
import tempfile
from types import ModuleType

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "1f3e27c86f7a"
CANONICAL_RULE_HASH = "a3f0a934419a"
ORIENTATIONS = ("identity", "mirror_lr")
ROOT = find_root(__file__)
GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _integer(value, name, low=None, high=None):
    if type(value) is not int or (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _orientation(value):
    if value not in ORIENTATIONS:
        raise ValueError(f"payload_orientation must be one of {ORIENTATIONS}")
    return value


def _rng(seed, purpose):
    return random.Random(hashlib.sha256(f"payload-reflection-v1:{seed}:{purpose}".encode()).digest())


@lru_cache(maxsize=1)
def canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [row for line in handle if line.strip()
                if (row := json.loads(line)).get("task_id") == TASK_ID]
    if len(rows) != 1:
        raise ValueError("Expected exactly one bound canonical rule")
    source = rows[0]["program_solution"]
    if _sha(" ".join(source.split()).encode())[:12] != CANONICAL_RULE_HASH:
        raise ValueError("Canonical rule changed; review the proposed transformation before reuse")
    return source


def program_for(orientation="identity"):
    """Materialize an exact rule; identity is byte-for-byte the canonical text."""
    _orientation(orientation)
    source = canonical_program()
    if orientation == "identity":
        return source
    original = "(lc (at g sr sc))"
    reflected = "(lc (at g sr (- (+ ti-c1 ti-c2) sc)))"
    if source.count(original) != 1:
        raise ValueError("Canonical payload lookup no longer has one unambiguous edit site")
    return source.replace(original, reflected, 1)


def _wrapped_program(source):
    """Use the shared compiler in native and staged layouts without copying it.

    Native repositories keep the compiler's historical `scripts` package in
    shared/tools. Supply that local namespace only while the compiler imports
    its parser; do not borrow a different checkout's cached package.
    """
    tools_path = ROOT / ("scripts" if (ROOT / "RUNTIME_MANIFEST.json").is_file() else "shared/tools")
    if not (tools_path / "comment_solutions.py").is_file():
        raise ImportError(f"Missing local rule parser under {tools_path}")
    for name, module in tuple(sys.modules.items()):
        if name != "scripts" and not name.startswith("scripts."):
            continue
        origins = list(getattr(module, "__path__", []))
        if getattr(module, "__file__", None):
            origins.append(module.__file__)
        if not origins or any(not Path(path).resolve().is_relative_to(tools_path.resolve()) for path in origins):
            raise ImportError(f"{name} belongs to another source tree; use a fresh process")
    existing = sys.modules.get("scripts")
    if existing is not None:
        return wrap_rule(source)
    namespace = ModuleType("scripts")
    namespace.__path__ = [str(tools_path)]
    before = set(sys.modules)
    sys.modules["scripts"] = namespace
    try:
        return wrap_rule(source)
    finally:
        for name in set(sys.modules) - before:
            if name == "scripts" or name.startswith("scripts."):
                del sys.modules[name]


class RuleRunner:
    """One real Racket process for both settings, with immutable result caching."""

    def __init__(self):
        self.bridge = None
        self.cache = {}

    def __enter__(self):
        if self.bridge is not None:
            raise RuntimeError("RuleRunner is already open")
        self.bridge = RacketBridge()
        try:
            for index, orientation in enumerate(ORIENTATIONS):
                self.bridge.eval_text(f"(define payload_rule_{index} {_wrapped_program(program_for(orientation))})")
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.bridge is not None:
            self.bridge.shutdown()
            self.bridge = None

    def apply(self, grid, orientation="identity"):
        _orientation(orientation)
        if self.bridge is None:
            raise RuntimeError("Use RuleRunner as a context manager")
        # The projection helper validates exact ARC integer grids and bounds.
        public_challenge_bytes({"train": [{"input": grid, "output": grid}], "test": [{"input": grid}]})
        key = (orientation, _json_bytes(grid))
        if key not in self.cache:
            self.bridge.define_grid("payload_input", grid)
            output = self.bridge.eval_text(f"(payload_rule_{ORIENTATIONS.index(orientation)} payload_input)")
            self.cache[key] = normalize_grid(output)
        return deepcopy(self.cache[key])


def generate_input(seed, sample_index, branch, difficulty="medium"):
    """Retain scene geometry, adding four rectangular asymmetric payload regions."""
    _integer(seed, "seed")
    _integer(sample_index, "sample_index", 0)
    if branch not in GENERATOR.BRANCHES:
        raise ValueError("Unknown rule branch")
    grid = GENERATOR.generate(seed, sample_index, difficulty=difficulty, rule_branch=branch)
    if branch != "stripe":
        facts = GENERATOR._analyze(grid)["facts"]
        template = facts["template"]
        row1, col1, row2, col2 = template["bbox"]
        top, bottom, left, right = GENERATOR._border_depths(grid, template)
        row1, row2, col1, col2 = row1 + top, row2 - bottom, col1 + left, col2 - right
        if min(row2 - row1 + 1, col2 - col1 + 1) < 2:
            raise ValueError("Need at least a 2x2 payload for asymmetric quadrants")
        rng = _rng(seed, f"payload:{sample_index}")
        colors = rng.sample([c for c in range(1, 10) if c != template["color"]], 4)
        split_row = rng.randint(row1 + 1, row2)
        split_col = rng.randint(col1 + 1, col2)
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                grid[row][col] = colors[2 * (row >= split_row) + (col >= split_col)]
    findings = GENERATOR.self_check(grid)
    if findings or GENERATOR.observe_overrides(grid).get("rule_branch") != branch:
        raise RuntimeError(f"Prototype construction changed the intended branch: {findings}")
    return grid


def assess_episode(episode, runner):
    """Check parameter rivals on demos; assess each query without its hidden label.

    Scope: the two declared orientations, identity/skip-branch rivals, and
    observable branch support. This is not universal program identifiability.
    """
    visible = json.loads(public_challenge_bytes(episode))
    branches = {"train": [], "test": []}
    for split in branches:
        for pair in visible[split]:
            errors = GENERATOR.self_check(pair["input"])
            if errors:
                raise ValueError(f"Invalid {split} input: {'; '.join(errors)}")
            branches[split].append(GENERATOR.observe_overrides(pair["input"])["rule_branch"])
    candidates = [setting for setting in ORIENTATIONS
                  if all(runner.apply(pair["input"], setting) == pair["output"]
                         for pair in visible["train"])]
    changed_branches = {branch for branch, pair in zip(branches["train"], visible["train"])
                        if pair["input"] != pair["output"]}
    queries = []
    for index, (branch, pair) in enumerate(zip(branches["test"], visible["test"])):
        reasons = []
        if not candidates:
            reasons.append("No declared parameter setting fits all demonstrations")
        if branch not in branches["train"]:
            reasons.append(f"Query branch {branch} is absent from demonstrations")
        elif branch not in changed_branches:
            reasons.append(f"No changed {branch} demonstration refutes the skip-branch rival")
        predictions = [runner.apply(pair["input"], setting) for setting in candidates]
        if predictions and any(prediction != predictions[0] for prediction in predictions[1:]):
            reasons.append("Demo-surviving parameter settings disagree on this query")
        queries.append({"query_index": index, "branch": branch,
                        "supported": not reasons, "reasons": reasons})
    return {
        "status": "supported" if all(row["supported"] for row in queries) else "unsupported",
        "parameter_candidates": candidates,
        "branch_coverage": {"demonstrated": sorted(set(branches["train"])),
                            "queried": branches["test"],
                            "changed_demo_branches": sorted(changed_branches),
                            "all_six_demonstrated": set(branches["train"]) == set(GENERATOR.BRANCHES)},
        "queries": queries,
        "scope": "two parameter settings and branch-skipping/identity rivals; demonstrations only",
        "query_answers_used": False,
    }


def build_episode(seed, orientation=None, *, demo_count=6, query_count=4,
                  difficulty="medium", runner=None):
    _integer(seed, "seed")
    _integer(demo_count, "demo_count", 1, 12)
    _integer(query_count, "query_count", 1, 12)
    if orientation is not None:
        _orientation(orientation)
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium or hard")
    if _sha(GENERATOR_PATH.read_bytes()) != GENERATOR_SHA256:
        raise RuntimeError("Generator changed after import; restart to bind the current source")
    if runner is None:
        with RuleRunner() as opened:
            return build_episode(seed, orientation, demo_count=demo_count,
                                 query_count=query_count, difficulty=difficulty, runner=opened)
    chosen = _orientation(orientation if orientation is not None else _rng(seed, "setting").choice(ORIENTATIONS))
    order = list(GENERATOR.BRANCHES[1:])
    _rng(seed, "branch-order").shuffle(order)
    order.insert(0, "proportional")
    demo_branches = [order[i % len(order)] for i in range(demo_count)]
    query_pool = list(dict.fromkeys(demo_branches))
    _rng(seed, "query-order").shuffle(query_pool)
    query_branches = [query_pool[i % len(query_pool)] for i in range(query_count)]
    seen = set()
    pairs = []
    sample_index = 0
    # A deterministic finite budget; unsupported requests fail, never clone pairs.
    for branch in demo_branches + query_branches:
        for _ in range(128):
            grid = generate_input(seed, sample_index, branch, difficulty)
            sample_index += 1
            key = _json_bytes(grid)
            if key in seen:
                continue
            output = runner.apply(grid, chosen)
            if output == grid:
                continue
            # The first proportional demo must distinguish both orientation rules.
            if not pairs and runner.apply(grid, ORIENTATIONS[1 - ORIENTATIONS.index(chosen)]) == output:
                continue
            seen.add(key)
            pairs.append({"input": grid, "output": output})
            break
        else:
            raise RuntimeError(f"Sampling budget exhausted for branch {branch}; no partial episode returned")
    program = program_for(chosen)
    episode = {
        "train": pairs[:demo_count], "test": pairs[demo_count:],
        "parameters": {"payload_orientation": chosen}, "seed": seed, "difficulty": difficulty,
        "status": "proposed_prototype", "variant_approved": False, "training_admitted": False,
        "source_bindings": {"generator_sha256": GENERATOR_SHA256,
                            "prototype_sha256": _sha(Path(__file__).read_bytes()),
                            "canonical_rule_hash": CANONICAL_RULE_HASH,
                            "canonical_program_sha256": _sha(canonical_program().encode()),
                            "program_sha256": _sha(program.encode())},
        "sampling": {"draws": sample_index, "demo_count": demo_count, "query_count": query_count,
                     "limit": "1..12 of each; with fewer than six demos queries use only demonstrated branches"},
    }
    episode["verification"] = assess_episode(episode, runner)
    if episode["verification"]["status"] != "supported":
        raise RuntimeError("Constructed lesson is unsupported: " + json.dumps(episode["verification"]))
    return episode


def write_batch(episodes, out_dir):
    """Write exact visible bytes and private evidence separately, with no overwrite.

    This projection writer does not revalidate private query labels. Callers use
    build_episode (Racket-backed) or independently verify authored labels first.
    """
    if not episodes:
        raise ValueError("Need at least one episode")
    out = Path(out_dir)
    if out.is_symlink() or (out.exists() and (not out.is_dir() or any(out.iterdir()))):
        raise ValueError("Output must be a new or empty directory")
    entries = {}
    for episode in episodes:
        visible = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id in entries:
            raise ValueError("Duplicate visible payload; refusing ambiguous public identity")
        setting = _orientation(episode["parameters"]["payload_orientation"])
        program = program_for(setting).encode()
        entries[public_id] = (visible, deepcopy(episode), program)
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".payload-export-", dir=out.parent))
    try:
        (temporary / "public").mkdir()
        (temporary / "private/programs").mkdir(parents=True)
        rows = []
        for public_id, (visible, episode, program) in sorted(entries.items()):
            program_id = _sha(program)
            paths = {"public_path": f"public/{public_id}.json",
                     "private_path": f"private/{public_id}.json",
                     "program_path": f"private/programs/{program_id}.rkt"}
            (temporary / paths["public_path"]).write_bytes(visible)
            (temporary / paths["private_path"]).write_bytes(_json_bytes(episode))
            (temporary / paths["program_path"]).write_bytes(program)
            rows.append({"public_id": public_id, **paths,
                         "program_sha256": program_id, "parameters": episode["parameters"],
                         "seed": episode["seed"], "demo_count": len(episode["train"]),
                         "query_count": len(episode["test"])})
        index = {"schema": "arcpuzzles-payload-reflection-prototype-v1",
                 "status": "proposed_prototype", "variant_approved": False,
                 "training_admitted": False, "public_identifier_status": "verified_visible_content",
                 "public_identity": "SHA-256 of exact reviewer_support.public_challenge_bytes",
                 "episodes": rows}
        (temporary / "private/index.json").write_bytes(_json_bytes(index))
        # Atomic directory publication; an existing nonempty destination is never replaced.
        os.replace(temporary, out)
        return index
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--orientation", choices=(*ORIENTATIONS, "both", "random"), default="both")
    parser.add_argument("--episodes", type=int, default=1, help="episodes per requested setting, 1..16")
    parser.add_argument("--demo-count", type=int, default=6)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    _integer(args.episodes, "episodes", 1, 16)
    settings = ORIENTATIONS if args.orientation == "both" else (None if args.orientation == "random" else args.orientation,)
    with RuleRunner() as runner:
        episodes = [build_episode(args.seed + i, setting, demo_count=args.demo_count,
                                  query_count=args.query_count, difficulty=args.difficulty, runner=runner)
                    for setting in settings for i in range(args.episodes)]
    index = write_batch(episodes, args.out)
    print(json.dumps({"status": index["status"], "episodes": len(episodes),
                      "demonstrations": sum(len(ep["train"]) for ep in episodes),
                      "queries": sum(len(ep["test"]) for ep in episodes),
                      "all_queries_supported": True, "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
