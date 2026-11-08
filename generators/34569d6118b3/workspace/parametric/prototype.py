#!/usr/bin/env python3
"""Proposed task-local swatch/template variants, never production approval.

Every exported label and rival prediction is evaluated through Racket. Python
is an independent comparison and a cheap bounded-sampling filter only.
"""
from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


TASK_ID = "34569d6118b3"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import (canonical_path, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)
from puzzle_generators.rule_wrap import strip_rule_wrapper

GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=REPO)
CANONICAL_SHA256 = "213d60bb58991cfb0f063a34f4ad178ac1fe312f144a5583abcfc166cfe8fc8f"


@dataclass(frozen=True)
class Settings:
    template_order: str = "forward"
    mirror: bool = False

    def __post_init__(self):
        if self.template_order not in ("forward", "reverse") or type(self.mirror) is not bool:
            raise ValueError("template_order must be forward/reverse and mirror must be a literal bool")

    def as_dict(self):
        return {"template_order": self.template_order, "mirror": self.mirror}


DEFAULT_SETTING = Settings()
ALL_SETTINGS = tuple(Settings(order, mirror) for order in ("forward", "reverse")
                     for mirror in (False, True))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _frozen(grid):
    return tuple(map(tuple, grid))


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def canonical_reference():
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        programs = {row["program_solution"] for row in map(json.loads, handle)
                    if row.get("task_id") == TASK_ID}
    if len(programs) != 1:
        raise ValueError("expected one exact canonical reference across this task's ledger rows")
    program = programs.pop()
    if _sha(program.encode()) != CANONICAL_SHA256:
        raise ValueError("canonical source changed: review variant derivation before proceeding")
    return program


def reference_program(setting=DEFAULT_SETTING):
    """Return canonical text unchanged by default; fail closed on changed anchors."""
    if not isinstance(setting, Settings):
        raise ValueError("setting must be Settings")
    program = canonical_reference()
    replacements = []
    if setting.template_order == "reverse":
        replacements.append(("(list-ref template-mats i)",
                             "(list-ref template-mats (- (length template-mats) 1 i))"))
    if setting.mirror:
        replacements.append(("(list-ref (list-ref template tr) tc)",
                             "(list-ref (list-ref template tr) (- tmpl-w 1 tc))"))
    for old, new in replacements:
        if program.count(old) != 1:
            raise ValueError(f"expected exactly one source anchor: {old}")
        program = program.replace(old, new, 1)
    return program


def python_mirror(grid, setting=DEFAULT_SETTING):
    """Independent mask composition; does not label an exported episode."""
    if not isinstance(setting, Settings):
        raise ValueError("setting must be Settings")
    parsed = GENERATOR._parse_scene(grid)
    if parsed["errors"]:
        raise ValueError("; ".join(parsed["errors"]))
    masks = parsed["templates"]
    if setting.template_order == "reverse":
        masks = tuple(reversed(masks))
    mapping = dict(zip(parsed["swatch_colors"], masks))
    output = []
    for layout_row in parsed["layout"]:
        for template_row in range(parsed["template_h"]):
            row = []
            for color in layout_row:
                values = mapping[color][template_row]
                if setting.mirror:
                    values = tuple(reversed(values))
                row.extend(color if value == 5 else 0 for value in values)
            output.append(row)
    return output


def surviving_settings(demonstrations, *, predict=python_mirror):
    """Infer the rule using only visible demonstration inputs and outputs."""
    if not demonstrations:
        raise ValueError("at least one demonstration is required")
    return tuple(setting for setting in ALL_SETTINGS
                 if all(predict(pair["input"], setting) == pair["output"] for pair in demonstrations))


def check_query_identifiability(demonstrations, query_inputs, *, predict=python_mirror):
    survivors = surviving_settings(demonstrations, predict=predict)
    checks = []
    for index, grid in enumerate(query_inputs):
        predictions = {_frozen(predict(grid, setting)) for setting in survivors}
        checks.append({"query_index": index, "survivor_count": len(survivors),
                       "distinct_predictions": len(predictions),
                       "identifiable": bool(survivors) and len(predictions) == 1})
    return {"survivors": [setting.as_dict() for setting in survivors], "queries": checks}


class SamplingError(RuntimeError):
    def __init__(self, message, rejections):
        super().__init__(message)
        self.rejections = rejections


def sample_inputs(seed, *, demo_count=3, query_count=4, max_attempts=512):
    """Sample canonical general profiles; first demo must distinguish all four rules."""
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    for name, count in (("demo_count", demo_count), ("query_count", query_count)):
        if type(count) is not int or not 1 <= count <= 32:
            raise ValueError(f"{name} must be an integer between 1 and 32")
    total = demo_count + query_count
    if type(max_attempts) is not int or not total <= max_attempts <= 4096:
        raise ValueError("max_attempts must be an integer between requested pair count and 4096")
    inputs, draws, rejections, seen = [], [], [], set()
    for sample_index in range(max_attempts):
        profile = GENERATOR.GENERAL_PROFILES[sample_index % len(GENERATOR.GENERAL_PROFILES)]
        grid = GENERATOR.generate(seed, sample_index, scene_profile=profile)
        errors = GENERATOR.self_check(grid)
        if errors:
            raise ValueError(f"canonical sampler produced an invalid input: {errors}")
        row = {"sample_index": sample_index, "scene_profile": profile}
        signature = _frozen(grid)
        if signature in seen:
            rejections.append(dict(row, reason="duplicate_input"))
            continue
        if not inputs:
            distinguishable = len({_frozen(python_mirror(grid, setting)) for setting in ALL_SETTINGS})
            if distinguishable != len(ALL_SETTINGS):
                rejections.append(dict(row, reason="ambiguous_first_demonstration",
                                       distinct_predictions=distinguishable))
                continue
        seen.add(signature)
        inputs.append(grid)
        draws.append(row)
        if len(inputs) == total:
            return {"train_inputs": inputs[:demo_count], "test_inputs": inputs[demo_count:],
                    "draws": draws, "rejections": rejections, "attempts": sample_index + 1,
                    "max_attempts": max_attempts}
    raise SamplingError(f"requested {total} distinct inputs; found {len(inputs)} in {max_attempts} attempts",
                        rejections)


class RacketOracle:
    """Evaluate the exact closed lambda using the shared wrapper-peeling helper.

    These pinned sources already use standard Racket syntax and bind h/w inside
    the lambda, so no shorthand rewriting or auto-bound variables are needed.
    Each eval includes the function definition and input together: bridge restart
    cannot silently lose a previous definition.
    """
    def __init__(self, bridge):
        self.bridge = bridge
        self.programs = {setting: reference_program(setting) for setting in ALL_SETTINGS}
        self.callables = {setting: strip_rule_wrapper(program) for setting, program in self.programs.items()}
        self.cache = {}
        self.executed_predictions = 0

    def predict(self, grid, setting=DEFAULT_SETTING):
        # Validate before lookup too: Python bool/float keys can equal integer
        # keys, so a cache hit must not admit a malformed ARC grid.
        expected = python_mirror(grid, setting)
        key = (setting, _frozen(grid))
        if key not in self.cache:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            result = self.bridge.eval_text(f"({self.callables[setting]} {literal})")
            if result != expected:
                raise AssertionError(f"Racket/Python mismatch for {setting.as_dict()}")
            self.cache[key] = result
            self.executed_predictions += 1
        return [row[:] for row in self.cache[key]]


def source_hashes():
    paths = [Path(__file__), GENERATOR_PATH, RUNTIME / "reviewer_support.py",
             RUNTIME / "puzzle_generators/rule_wrap.py", RUNTIME / "arc_repl/racket_bridge.py"]
    return {path.relative_to(REPO).as_posix(): _sha(path.read_bytes()) for path in paths}


def build_episode(seed, *, setting=DEFAULT_SETTING, demo_count=3, query_count=4,
                  max_attempts=512, bridge=None):
    """Build one fixed-setting episode, requiring successful matching Racket execution."""
    if not isinstance(setting, Settings):
        raise ValueError("setting must be Settings")
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=20.0) as owned:
            return build_episode(seed, setting=setting, demo_count=demo_count,
                                 query_count=query_count, max_attempts=max_attempts, bridge=owned)
    sample = sample_inputs(seed, demo_count=demo_count, query_count=query_count, max_attempts=max_attempts)
    oracle = RacketOracle(bridge)
    all_inputs = sample["train_inputs"] + sample["test_inputs"]
    # Check every rival on every retained input as well as the selected labels.
    for grid in all_inputs:
        for rival in ALL_SETTINGS:
            oracle.predict(grid, rival)
    train = [{"input": grid, "output": oracle.predict(grid, setting)} for grid in sample["train_inputs"]]
    test = [{"input": grid, "output": oracle.predict(grid, setting)} for grid in sample["test_inputs"]]
    identifiable = check_query_identifiability(train, sample["test_inputs"], predict=oracle.predict)
    if identifiable["survivors"] != [setting.as_dict()] or not all(row["identifiable"] for row in identifiable["queries"]):
        raise AssertionError("executed demonstrations do not identify the requested episode rule")
    witness = [{"parameters": rival.as_dict(), "output": oracle.predict(train[0]["input"], rival)}
               for rival in ALL_SETTINGS]
    if len({_frozen(row["output"]) for row in witness}) != 4:
        raise AssertionError("executed witness does not distinguish all four settings")
    program = oracle.programs[setting]
    return {
        "schema": "34569d6118b3-parametric-prototype-v1", "status": "proposed_not_approved",
        "task_id": TASK_ID, "parent": "training:42f83767", "seed": seed,
        "parameters": setting.as_dict(), "demo_count": demo_count, "query_count": query_count,
        "train": train, "test": test, "reference_program": program,
        "reference_sha256": _sha(program.encode()),
        "executed_callable_sha256": _sha(oracle.callables[setting].encode()),
        "canonical_program_sha256": CANONICAL_SHA256, "source_hashes": source_hashes(),
        "sampling": {key: value for key, value in sample.items() if not key.endswith("_inputs")},
        "identifiability": identifiable, "witness": {"train_index": 0, "rival_outputs": witness},
        "verification": {"label_backend": "racket", "python_mirror_parity": True,
                         "executed_predictions": oracle.executed_predictions,
                         "runtime": bridge.runtime_identity},
        "limits": ["Only four declared parameter rivals are checked; not an unrestricted solver census.",
                   "The first demonstration is filtered to expose both parameters.",
                   "Counts are bounded to 1..32 per split and sampling may fail at the explicit cap.",
                   "Prototype evidence grants neither canonical approval nor training admission."],
    }


def _publish_no_replace(stage, destination):
    """Linux atomic directory rename with no-overwrite, including concurrent writers."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise RuntimeError("atomic export requires Linux renameat2 (the packet runtime platform)")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(stage), -100, os.fsencode(destination), 1):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def write_export(destination, episodes, *, command=None):
    """Publish new public/private siblings after validating the complete batch.

    Public contents, names and order depend only on the shared exact projection.
    All duplicate detection precedes any directory creation. Labels/references
    remain private; callers must publish only the public/ child.
    """
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    prepared, programs, seen = [], {}, set()
    for episode in episodes:
        blob = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        if identifier != _sha(blob):
            raise AssertionError("public identifier does not hash the exact shared bytes")
        if identifier in seen:
            raise ValueError(f"duplicate public challenge: {identifier}")
        seen.add(identifier)
        program = episode["reference_program"]
        digest = _sha(program.encode())
        if digest != episode["reference_sha256"]:
            raise ValueError("private reference hash does not match exact program text")
        programs[digest] = program.encode()
        prepared.append((identifier, blob, episode))
    if not prepared:
        raise ValueError("at least one episode is required")
    prepared.sort(key=lambda row: row[0])
    # Serialize everything before touching the destination filesystem.
    private_blob = _json_bytes([{**episode, "public_id": identifier} for identifier, _, episode in prepared])
    ids = [identifier for identifier, _, _ in prepared]
    manifest = {"schema": "34569d6118b3-parametric-export-v1", "status": "proposed_not_approved",
                "public_ids": ids, "episode_count": len(prepared), "command": command,
                "source_hashes": source_hashes(),
                "reference_sha256s": sorted(programs),
                "public_projection": "reviewer_support.public_challenge_bytes exact bytes",
                "duplicate_policy": "reject_complete_batch_before_writes",
                "publication": "Linux atomic renameat2 RENAME_NOREPLACE"}
    manifest_blob = _json_bytes(manifest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".parametric-stage-", dir=destination.parent))
    try:
        public, private = stage / "public", stage / "private"
        public.mkdir()
        private.mkdir(mode=0o700)
        (private / "references").mkdir(mode=0o700)
        for identifier, blob, _ in prepared:
            (public / (identifier + ".json")).write_bytes(blob)
        (public / "index.json").write_bytes(_json_bytes(ids))
        for digest, program in programs.items():
            (private / "references" / (digest + ".rkt")).write_bytes(program)
        (private / "episodes.json").write_bytes(private_blob)
        (private / "receipt.json").write_bytes(manifest_blob)
        _publish_no_replace(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42426)
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=512)
    parser.add_argument("--template-order", choices=("forward", "reverse"), default="forward")
    parser.add_argument("--mirror", choices=("false", "true"), default="false")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    settings = ALL_SETTINGS if args.all_settings else (Settings(args.template_order, args.mirror == "true"),)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=20.0) as bridge:
        episodes = [build_episode(args.seed, setting=setting, demo_count=args.demo_count,
                                  query_count=args.query_count, max_attempts=args.max_attempts,
                                  bridge=bridge) for setting in settings]
    manifest = write_export(args.out, episodes, command=[sys.executable, *sys.argv])
    print(json.dumps({"status": manifest["status"], "episode_count": len(episodes),
                      "demo_count": args.demo_count, "query_count": args.query_count,
                      "executed_predictions": sum(ep["verification"]["executed_predictions"] for ep in episodes),
                      "public_ids": manifest["public_ids"], "output": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
