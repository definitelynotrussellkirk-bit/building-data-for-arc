#!/usr/bin/env python3
"""Separate, unapproved prototype: concatenate a grid with its reflection."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import sys


TASK_ID = "2c30a4753f6b"
VERSION = "0.1.0"
SCHEMA = "arc-task-parametric-reflection-v1"
TASK_HOME = Path(__file__).resolve().parents[2]
REPO = TASK_HOME.parents[1]
CANONICAL_PROGRAM = "(rule! (lambda (g) (let* ((h (rows g)) (w (cols g))) (build-grid h (* 2 w) (r c) (if (< c w) (at g r c) (at g r (- (- (* 2 w) 1) c)))))))"
WITNESS = [[1, 0, 2], [3, 4, 0]]
LIMITATIONS = [
    "Task-local proposed prototype; no production parametric API, authority change, approval, or training admission.",
    "Evidence covers the recorded seeds and all four declared parameter rivals, not all possible rules or scenes.",
    "Generated episodes use dimensions 3..15 and three varied textures; the transformation accepts the broader axis-specific bounded domain.",
    "The reference labels are executed by the actual protected Racket bridge. The Python transform is only an independent parity check.",
]


@dataclass(frozen=True)
class Settings:
    axis: str = "horizontal"
    side: str = "after"

    def __post_init__(self):
        if type(self.axis) is not str or self.axis not in ("horizontal", "vertical"):
            raise ValueError("axis must be horizontal or vertical")
        if type(self.side) is not str or self.side not in ("after", "before"):
            raise ValueError("side must be after or before")

    @property
    def key(self):
        return f"{self.axis}-{self.side}"


DEFAULT = Settings()
ALL_SETTINGS = tuple(Settings(axis, side) for axis in ("horizontal", "vertical") for side in ("after", "before"))


def _metadata():
    return {
        "schema": SCHEMA, "prototype_version": VERSION, "task_id": TASK_ID,
        "family": "training:c9e6f938", "classification": "proposed prototype",
        "parameter_space": {"axis": ["horizontal", "vertical"], "side": ["after", "before"]},
        "default": asdict(DEFAULT),
        "hash_format": "JSON content hashes: SHA-256 of sorted-key compact UTF-8 JSON; source/program hashes: exact bytes/text.",
        "execution_adapter": "(let ((rule! (lambda (f) f))) (EXACT_PROGRAM QUOTED_INPUT_GRID))",
        "limitations": LIMITATIONS,
    }


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest(value):
    """SHA-256 of canonical JSON: sorted keys, compact separators, UTF-8."""
    return text_digest(json.dumps(value, sort_keys=True, separators=(",", ":")))


def _file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _seed(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def select_settings(seed, *, axis="horizontal", side="after"):
    """Choose each requested 'sample' parameter once for the complete episode."""
    rng = random.Random(f"{TASK_ID}:{VERSION}:parameters:{_seed(seed)}")
    if axis == "sample":
        axis = rng.choice(("horizontal", "vertical"))
    if side == "sample":
        side = rng.choice(("after", "before"))
    return Settings(axis, side)


def validate_grid(grid, settings=DEFAULT):
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a Settings instance")
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be non-empty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be non-empty")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    max_h, max_w = (30, 15) if settings.axis == "horizontal" else (15, 30)
    if h > max_h or w > max_w:
        raise ValueError(f"{settings.axis} requires height 1..{max_h} and width 1..{max_w}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal integers 0..9")
    return h, w


def transform(grid, settings=DEFAULT):
    """Independent Python specification; never used to manufacture labels."""
    validate_grid(grid, settings)
    original = [list(row) for row in grid]
    if settings.axis == "horizontal":
        reflected = [row[::-1] for row in original]
        first, second = (original, reflected) if settings.side == "after" else (reflected, original)
        return [a + b for a, b in zip(first, second)]
    reflected = list(reversed(original))
    first, second = (original, reflected) if settings.side == "after" else (reflected, original)
    return [row[:] for row in first + second]


def program(settings=DEFAULT):
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a Settings instance")
    if settings == DEFAULT:
        return CANONICAL_PROGRAM
    if settings.axis == "horizontal":
        body = "(build-grid h (* 2 w) (r c) (if (< c w) (at g r (- (- w 1) c)) (at g r (- c w))))"
    elif settings.side == "after":
        body = "(build-grid (* 2 h) w (r c) (if (< r h) (at g r c) (at g (- (- (* 2 h) 1) r) c)))"
    else:
        body = "(build-grid (* 2 h) w (r c) (if (< r h) (at g (- (- h 1) r) c) (at g (- r h) c)))"
    return f"(rule! (lambda (g) (let* ((h (rows g)) (w (cols g))) {body})))"


def sample_inputs(seed):
    """Four bounded draws; distinct corner colors construct asymmetry without retries."""
    rng = random.Random(f"{TASK_ID}:{VERSION}:inputs:{_seed(seed)}")
    shapes = [(3, 4), (rng.randint(4, 5), 3), (6, rng.randint(5, 7)), (rng.randint(8, 15), rng.randint(9, 15))]
    result = []
    for index, (h, w) in enumerate(shapes):
        corners = rng.sample(range(1, 10), 4)
        palette = [0] + corners
        density = (0.15, 0.4, 0.75, 0.3)[index]
        grid = [[rng.choice(palette) if rng.random() < density else 0 for _ in range(w)] for _ in range(h)]
        grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1] = corners
        grid[h // 2][w // 2] = 0
        result.append(grid)
    return result


def _sources():
    paths = [Path(__file__).resolve(), Path(__file__).with_name("README.md"), TASK_HOME / "tests/test_parametric_reflection.py"]
    return {path.relative_to(REPO).as_posix(): _file_digest(path) for path in paths}


class RacketLabels:
    """Cache only outputs returned by a live protected Racket subprocess."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=10.0, startup_timeout=30.0)
        self.runtime = self.bridge.runtime_identity
        if not self.runtime.get("protected"):
            self.bridge.shutdown()
            raise RuntimeError("protected Racket runtime required")
        self.cache = {}
        self.requests = 0
        return self

    def __exit__(self, *exc):
        self.bridge.shutdown()

    def output(self, grid, settings):
        validate_grid(grid, settings)
        source = program(settings)
        key = text_digest(source), digest(grid)
        self.requests += 1
        if key not in self.cache:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            # The selected source is evaluated unchanged. rule! registers the
            # callable; this lexical adapter returns it for one direct call.
            expression = f"(let ((rule! (lambda (f) f))) ({source} {literal}))"
            output = self.bridge.eval_text(expression)
            if output != transform(grid, settings):
                raise ValueError(f"Racket/Python parity mismatch for {settings.key} on {digest(grid)}")
            self.cache[key] = output
        return copy.deepcopy(self.cache[key])


def _episode(seed, settings, labels):
    inputs = sample_inputs(seed)
    pairs = [{"index": index, "split": "train" if index < 3 else "test", "input": grid,
              "input_sha256": digest(grid), "output": labels.output(grid, settings)} for index, grid in enumerate(inputs)]
    for pair in pairs:
        pair["output_sha256"] = digest(pair["output"])
    rivals = []
    for alternate in ALL_SETTINGS:
        if alternate == settings:
            continue
        predictions = [labels.output(grid, alternate) for grid in inputs]
        matches = [prediction == pair["output"] for prediction, pair in zip(predictions, pairs)]
        status = "refuted_by_demonstrations" if not all(matches[:3]) else ("survived_all" if matches[3] else "ambiguous_query")
        rivals.append({"parameters": asdict(alternate), "program_sha256": text_digest(program(alternate)),
                       "predictions": predictions, "prediction_sha256": [digest(output) for output in predictions],
                       "demo_matches": matches[:3], "query_matches": matches[3:], "status": status})
    public_id = text_digest(f"{TASK_ID}:{VERSION}:public:{seed}:{settings.key}")[:16]
    return {"seed": seed, "parameters": asdict(settings), "program": program(settings),
            "program_sha256": text_digest(program(settings)), "pairs": pairs, "rivals": rivals,
            "public_path": f"public/episode-{public_id}.json"}


def _public(episode):
    return {"train": [{"input": pair["input"], "output": pair["output"]} for pair in episode["pairs"][:3]],
            "test": [{"input": episode["pairs"][3]["input"]}]}


def _canonical_parity(inputs, labels):
    from arcpuzzles import Catalog
    receipt = Catalog(REPO).apply(TASK_ID, inputs, reference="canonical", timeout=120)
    expected_hash = text_digest(" ".join(CANONICAL_PROGRAM.split()))[:12]
    checks = [result["error"] is None and result["output"] == labels.output(grid, DEFAULT)
              for grid, result in zip(inputs, receipt["results"], strict=True)]
    passed = (receipt["rule_hash_matches_catalog"] is True and receipt["catalog_rule_hash"] == expected_hash and all(checks))
    return {"passed": passed, "pair_matches": checks, "expected_normalized_rule_hash": expected_hash, "receipt": receipt}


def _build_evidence(seed, settings):
    with RacketLabels() as labels:
        episodes = [_episode(seed, setting, labels) for setting in settings]
        witness = {"input": WITNESS, "input_sha256": digest(WITNESS), "results": []}
        for setting in ALL_SETTINGS:
            output = labels.output(WITNESS, setting)
            witness["results"].append({"parameters": asdict(setting), "output": output, "output_sha256": digest(output)})
        witness["all_distinct"] = len({row["output_sha256"] for row in witness["results"]}) == 4
        canonical = _canonical_parity(sample_inputs(seed) + [WITNESS], labels)
        ambiguous = sum(any(rival["status"] == "ambiguous_query" for rival in episode["rivals"]) for episode in episodes)
        separated = all(all(rival["status"] == "refuted_by_demonstrations" for rival in episode["rivals"]) for episode in episodes)
        evidence = {
            **_metadata(), "seed": seed, "source_hashes": _sources(),
            "runtime": labels.runtime,
            "rules": [{"parameters": asdict(setting), "program": program(setting),
                       "program_sha256": text_digest(program(setting)), "path": f"private/rules/{setting.key}.rkt"} for setting in ALL_SETTINGS],
            "episodes": episodes, "distinct_setting_witness": witness, "canonical_parity": canonical,
            "counts": {"episodes": len(episodes), "labelled_pairs": 4 * len(episodes),
                       "alternate_rival_checks": 3 * len(episodes), "alternate_pair_predictions": 12 * len(episodes),
                       "ambiguous_episodes": ambiguous, "bridge_output_requests": labels.requests,
                       "bridge_distinct_outputs_executed": len(labels.cache), "canonical_reference_inputs": 5},
            "status": "pass" if witness["all_distinct"] and canonical["passed"] and separated else "fail",
        }
    return evidence


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, separators=(",", ":"))
        handle.write("\n")


def emit_bundle(output, *, seed=0, settings=None):
    """Create private evidence plus redacted public challenges at a new path."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing existing output path: {output}")
    _seed(seed)
    settings = [DEFAULT] if settings is None else list(settings)
    if not settings or any(not isinstance(setting, Settings) for setting in settings) or len(set(settings)) != len(settings):
        raise ValueError("supply one to four distinct Settings instances")
    output.mkdir(parents=True, exist_ok=False)
    try:
        evidence = _build_evidence(seed, settings)
        evidence["invocation"] = {"command": [sys.executable, *sys.argv], "cwd": str(Path.cwd())}
        for episode in evidence["episodes"]:
            public = _public(episode)
            _write_json(output / episode["public_path"], public)
        for rule in evidence["rules"]:
            path = output / rule["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as handle:
                handle.write(rule["program"])
        _write_json(output / "private/evidence.json", evidence)
        return evidence
    except Exception as error:
        _write_json(output / "private/failure.json", {"status": "error", "seed": seed,
                    "parameters": [asdict(setting) for setting in settings],
                    "error_type": type(error).__name__, "error": str(error)})
        raise


def _saved_file(output, relative):
    if type(relative) is not str:
        raise ValueError(f"invalid evidence path: {relative!r}")
    path = output / relative
    if path.is_symlink() or not path.resolve().is_relative_to(output.resolve()) or not path.is_file():
        raise ValueError(f"invalid evidence path: {relative!r}")
    return path


def verify_bundle(output):
    """Fail closed on changed sources/public data, then reexecute all exact rules."""
    output = Path(output)
    evidence_path = _saved_file(output, "private/evidence.json")
    evidence = json.loads(evidence_path.read_text())
    if evidence.get("schema") != SCHEMA or evidence.get("status") != "pass":
        raise ValueError("evidence schema/status is not a completed passing prototype")
    for field, expected in _metadata().items():
        if field not in evidence or digest(evidence[field]) != digest(expected):
            raise ValueError(f"semantic metadata differs: {field}")
    if evidence.get("source_hashes") != _sources():
        raise ValueError("prototype source hashes changed; emit new evidence")
    _seed(evidence["seed"])
    episodes = evidence["episodes"]
    settings = [Settings(**episode["parameters"]) for episode in episodes]
    if not 1 <= len(settings) <= 4 or len(set(settings)) != len(settings):
        raise ValueError("invalid episode settings inventory")
    public_root = output / "public"
    public_entries = list(public_root.rglob("*"))
    if public_root.is_symlink() or not public_root.is_dir() or any(path.is_symlink() or not path.is_file() for path in public_entries):
        raise ValueError("public directory contains a missing, unexpected, or linked entry")
    if {path.relative_to(output).as_posix() for path in public_entries} != {episode["public_path"] for episode in episodes}:
        raise ValueError("public file inventory differs from the declared challenges")
    for episode, setting in zip(episodes, settings):
        if episode["program"] != program(setting) or episode["program_sha256"] != text_digest(program(setting)):
            raise ValueError("private program does not match the declared setting")
        public = json.loads(_saved_file(output, episode["public_path"]).read_text())
        if digest(public) != digest(_public(episode)) or set(public) != {"train", "test"}:
            raise ValueError("public challenge changed or exposes extra metadata/query answers")
    if len(evidence["rules"]) != 4:
        raise ValueError("incomplete program inventory")
    for rule in evidence["rules"]:
        setting = Settings(**rule["parameters"])
        if rule["program"] != program(setting) or _saved_file(output, rule["path"]).read_text() != program(setting):
            raise ValueError("saved program differs from exact declared Racket")
    fresh = _build_evidence(evidence["seed"], settings)
    for field in ("episodes", "rules", "distinct_setting_witness", "counts", "source_hashes"):
        if digest(evidence[field]) != digest(fresh[field]):
            raise ValueError(f"reexecuted {field} differs from saved evidence")
    old_receipt, new_receipt = evidence["canonical_parity"]["receipt"], fresh["canonical_parity"]["receipt"]
    for field in ("results", "generator_sha256", "catalog_rule_hash", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog"):
        if digest(old_receipt[field]) != digest(new_receipt[field]):
            raise ValueError(f"canonical parity binding changed: {field}")
    for field in ("passed", "pair_matches", "expected_normalized_rule_hash"):
        if digest(evidence["canonical_parity"][field]) != digest(fresh["canonical_parity"][field]):
            raise ValueError(f"canonical parity summary changed: {field}")
    if fresh["status"] != "pass" or evidence["canonical_parity"]["passed"] is not True:
        raise ValueError("fresh execution did not verify the prototype")
    historical_runtime = evidence["runtime"]
    if historical_runtime.get("backend") != "racket" or historical_runtime.get("protected") is not True:
        raise ValueError("historical runtime receipt does not declare protected Racket")
    runtime_hashes = {}
    for field in ("binary_sha256", "bridge_sha256", "prelude_sha256", "candidate_symbol_policy_sha256"):
        old, new = historical_runtime.get(field), fresh["runtime"][field]
        if type(old) is not str or len(old) != 64 or any(char not in "0123456789abcdef" for char in old):
            raise ValueError(f"malformed historical runtime identity: {field}")
        runtime_hashes[field] = {"historical": old, "current": new, "match": old == new}
    return {"schema": SCHEMA + "-verification", "status": "pass", "evidence_sha256": _file_digest(evidence_path),
            "source_hashes": fresh["source_hashes"], "runtime": fresh["runtime"], "counts": fresh["counts"],
            "runtime_comparison": {"policy": "Saved runtime is a historical receipt; verification independently executes the current protected Racket runtime. Content identities are compared and reported, not required to match. Machine paths are not compared.",
                                   "content_hashes": runtime_hashes, "content_hashes_match": all(row["match"] for row in runtime_hashes.values()),
                                   "paths_compared": False},
            "canonical_parity": fresh["canonical_parity"], "limitations": LIMITATIONS,
            "invocation": {"command": [sys.executable, *sys.argv], "cwd": str(Path.cwd())}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    emit = commands.add_parser("emit", help="create a new bundle of Racket-labelled episodes")
    emit.add_argument("--seed", type=int, default=0)
    emit.add_argument("--axis", choices=("horizontal", "vertical", "sample"), default="horizontal")
    emit.add_argument("--side", choices=("after", "before", "sample"), default="after")
    emit.add_argument("--all-settings", action="store_true")
    emit.add_argument("--out", type=Path, required=True)
    verify = commands.add_parser("verify", help="check and reexecute a saved bundle")
    verify.add_argument("bundle", type=Path)
    verify.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "emit":
            if args.all_settings and (args.axis != "horizontal" or args.side != "after"):
                raise ValueError("--all-settings cannot be combined with individual parameter choices")
            settings = list(ALL_SETTINGS) if args.all_settings else [select_settings(args.seed, axis=args.axis, side=args.side)]
            report = emit_bundle(args.out, seed=args.seed, settings=settings)
        else:
            if args.out.exists() or args.out.is_symlink():
                raise FileExistsError(f"refusing existing verification output: {args.out}")
            if args.out.resolve().is_relative_to((args.bundle / "public").resolve()):
                raise ValueError("private verification receipt must be outside the bundle's public directory")
            report = verify_bundle(args.bundle)
            _write_json(args.out, report)
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "counts": report["counts"], "out": str(args.out)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
