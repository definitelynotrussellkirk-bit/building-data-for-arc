#!/usr/bin/env python3
"""Build or verify a bounded, source-bound protected-Racket authoring audit.

The public directory contains only demonstrations and one current query input,
with each filename equal to the SHA-256 of its exact bytes. Private records keep
settings, programs, answers, rival outcomes, and future queries. This is
reviewer evidence only: it does not grant owner acceptance or training admission.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "ba0c6a5828f9"
SCHEMA = "arcpuzzles-ba0c6a5828f9-parametric-audit-v1"


def _load_prototype():
    path = HERE / "prototype.py"
    name = f"_{TASK_ID}_audit_prototype_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


model = _load_prototype()


def _encoded(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_digest(path: Path) -> str:
    return _digest(path.read_bytes())


def _source_paths() -> list[Path]:
    return [
        ROOT / f"generators/{TASK_ID}/generator.py",
        HERE / "adapter.py",
        HERE / "audit.py",
        HERE / "prototype.py",
        HERE / "promotion.json",
        HERE / "rules/canonical.rkt",
        HERE / "rules/most_clipped.rkt",
    ]


def source_bindings() -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _file_digest(path),
        }
        for path in _source_paths()
    ]


def _validate_jobs(jobs: Any, default_demos: int) -> list[dict[str, Any]]:
    if type(jobs) is not list or not 1 <= len(jobs) <= 16:
        raise ValueError("jobs must be a list of 1..16 entries")
    checked = []
    for raw in jobs:
        if type(raw) is not dict or set(raw) not in ({"seed", "settings"}, {"seed", "settings", "demos"}):
            raise ValueError("each job needs exactly seed/settings and optional demos")
        seed = model._integer(raw["seed"], 0, model.MAX_SEED, "seed")
        scope = model._setting(raw["settings"])
        demos = model._integer(raw.get("demos", default_demos), model.MIN_DEMOS, model.MAX_DEMOS, "demos")
        checked.append({"seed": seed, "settings": {model.PARAMETER: scope}, "demos": demos})
    if len({_encoded(row) for row in checked}) != len(checked):
        raise ValueError("duplicate audit job")
    return checked


def _safe_destination(output: Path) -> None:
    output = output.absolute()
    for path in (output, *output.parents):
        if path.is_symlink():
            raise ValueError("symlink audit destinations are forbidden")
    if output.exists():
        raise FileExistsError(output)


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


class Oracle:
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        self._wrap_rule = wrap_rule
        self._bridge = RacketBridge(timeout=20)
        identity = self._bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self._bridge.close()
            raise ValueError("audit requires a protected Racket runtime")
        self.identity = identity
        self._wrapped: dict[str, str] = {}
        self._cache: dict[tuple[str, str], list[list[int]]] = {}
        self.calls = 0
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._bridge.close()
        return False

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        key = (program, json.dumps(grid, separators=(",", ":")))
        if key not in self._cache:
            wrapped = self._wrapped.setdefault(program, self._wrap_rule(program))
            result = self._bridge.eval_text(f"({wrapped} {_grid_literal(grid)})")
            # Reuse the strict public serializer to reject malformed grids.
            _encoded({"train": [{"input": grid, "output": result}], "test": [{"input": grid}]})
            self._cache[key] = result
            self.calls += 1
        return self._cache[key]


def _asset_path(stage: Path, relative: str) -> Path:
    target = (stage / relative).resolve()
    if not target.is_relative_to(stage.resolve()):
        raise ValueError("audit asset escapes destination")
    return target


def build(output: Path | str, jobs: Any, *, demos: int = 3, queries: int = 4,
          reliability_seeds: int = 50) -> dict[str, Any]:
    output = Path(output).absolute()
    _safe_destination(output)
    demos = model._integer(demos, model.MIN_DEMOS, model.MAX_DEMOS, "demos")
    queries = model._integer(queries, model.MIN_QUERIES, model.MAX_QUERIES, "queries")
    reliability_seeds = model._integer(reliability_seeds, 0, 200, "reliability_seeds")
    jobs = _validate_jobs(jobs, demos)
    bindings = source_bindings()
    started = time.monotonic()
    assets: dict[str, bytes] = {}
    records = []
    public_ids: set[str] = set()
    programs = dict(model.RIVAL_PROGRAMS)
    program_hashes = {name: _digest(source.encode("utf-8")) for name, source in programs.items()}
    for name, source in sorted(programs.items()):
        assets[f"private/programs/{program_hashes[name]}.rkt"] = source.encode("utf-8")

    with Oracle() as oracle:
        for job in jobs:
            episode = model.generate(job["seed"], job["settings"], job["demos"], queries)
            selected = job["settings"][model.PARAMETER]
            selected_program = programs[selected]
            for split in ("train", "test"):
                for pair in episode[split]:
                    actual = oracle.apply(selected_program, pair["input"])
                    if actual != pair["output"]:
                        raise AssertionError(f"selected Racket label mismatch: {job}/{split}")

            eliminated = {}
            for rival, source in programs.items():
                if rival == selected:
                    continue
                demo_outputs = [oracle.apply(source, pair["input"]) for pair in episode["train"]]
                mismatches = [i for i, (pair, value) in enumerate(zip(episode["train"], demo_outputs))
                              if pair["output"] != value]
                if not mismatches:
                    raise AssertionError(f"demonstrations leave declared rival alive: {job}/{rival}")
                query_outputs = [oracle.apply(source, pair["input"]) for pair in episode["test"]]
                eliminated[rival] = {
                    "first_distinguishing_demo": mismatches[0],
                    "distinguishing_demos": mismatches,
                    "query_disagreements": [
                        i for i, (pair, value) in enumerate(zip(episode["test"], query_outputs))
                        if pair["output"] != value
                    ],
                }

            one_query = model.generate(job["seed"], job["settings"], job["demos"], 1)
            if model.public_turn_bytes(one_query, 0) != model.public_turn_bytes(episode, 0):
                raise AssertionError("four-query first turn differs from one-query generation")
            turns = []
            for index in range(queries):
                raw = model.public_turn_bytes(episode, index)
                public_id = _digest(raw)
                if public_id != model.public_turn_id(episode, index) or public_id in public_ids:
                    raise AssertionError("public turn ID mismatch or duplicate")
                public_ids.add(public_id)
                path = f"public/{public_id}.json"
                assets[path] = raw
                turns.append({"index": index, "public_id": public_id, "path": path,
                              "answer": episode["test"][index]["output"]})

            private = {
                "schema": f"{TASK_ID}-parametric-audit-episode-v1",
                "task_id": TASK_ID,
                "seed": job["seed"],
                "settings": job["settings"],
                "demos": job["demos"],
                "queries": queries,
                "program_sha256": program_hashes[selected],
                "train": episode["train"],
                "test": episode["test"],
                "turns": turns,
                "eliminated_rivals": eliminated,
                "training_admitted": False,
            }
            raw = _encoded(private)
            private_id = _digest(raw)
            private_path = f"private/episodes/{private_id}.json"
            assets[private_path] = raw
            records.append({
                "seed": job["seed"],
                "settings_sha256": _digest(_encoded(job["settings"])),
                "demos": job["demos"],
                "private": private_path,
                "public_ids": [turn["public_id"] for turn in turns],
            })
        racket_identity = oracle.identity
        racket_evaluations = oracle.calls

    reliability = {"attempted": 0, "successful": 0, "visible_pairs": 0,
                   "matched_input_comparisons": 0, "label_basis": "Python claims; protected cases above"}
    for seed in range(reliability_seeds):
        for demo_count in (2, 3, 6):
            episodes = [model.generate(seed, {model.PARAMETER: scope}, demo_count, 4)
                        for scope in model.SCOPES]
            reliability["attempted"] += len(episodes)
            inputs = [[pair["input"] for split in ("train", "test") for pair in ep[split]]
                      for ep in episodes]
            if inputs[0] != inputs[1]:
                raise AssertionError("settings changed the visible inputs")
            reliability["matched_input_comparisons"] += 1
            for episode in episodes:
                serial = [json.dumps(pair["input"], separators=(",", ":"))
                          for split in ("train", "test") for pair in episode[split]]
                if len(serial) != len(set(serial)):
                    raise AssertionError("reliability episode repeats an input")
                reliability["successful"] += 1
                reliability["visible_pairs"] += len(serial)

    if source_bindings() != bindings:
        raise ValueError("authoring sources changed during audit")
    manifest = {
        "schema": SCHEMA,
        "status": "passed",
        "task_id": TASK_ID,
        "visibility": "controller-only",
        "records": records,
        "programs": program_hashes,
        "source_files": bindings,
        "racket": racket_identity,
        "racket_evaluations": racket_evaluations,
        "reliability": reliability,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "scope": "Finite declared-rival and sampled-seed audit; no universal uniqueness, owner acceptance, or training admission.",
        "training_admitted": False,
        "owner_acceptance": "not_performed",
        "files": {name: _digest(raw) for name, raw in sorted(assets.items())},
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-audit-", dir=output.parent) as temp:
        stage = Path(temp) / "bundle"
        stage.mkdir()
        for name, raw in sorted(assets.items()):
            path = _asset_path(stage, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (stage / "manifest.json").write_bytes(_encoded(manifest))
        os.replace(stage, output)
    return {
        "status": "passed",
        "episodes": len(records),
        "public_turns": len(public_ids),
        "racket_evaluations": racket_evaluations,
        "reliability": reliability,
        "out": str(output),
    }


def verify(output: Path | str) -> dict[str, Any]:
    output = Path(output).absolute()
    for path in (output, *output.parents):
        if path.is_symlink():
            raise ValueError("symlink audit paths are forbidden")
    manifest = json.loads((output / "manifest.json").read_bytes())
    if manifest.get("schema") != SCHEMA or manifest.get("task_id") != TASK_ID:
        raise ValueError("wrong audit schema or task")
    files = manifest.get("files")
    if type(files) is not dict:
        raise ValueError("audit file inventory missing")
    expected = {"manifest.json", *files}
    actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError(f"audit file set differs: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    for name, expected_hash in files.items():
        path = _asset_path(output, name)
        if _file_digest(path) != expected_hash:
            raise ValueError(f"audit asset hash mismatch: {name}")
    if manifest.get("source_files") != source_bindings():
        raise ValueError("audit source binding is stale")
    public = sorted((output / "public").glob("*.json"))
    if len(public) != sum(len(row["public_ids"]) for row in manifest["records"]):
        raise ValueError("public turn count mismatch")
    for path in public:
        raw = path.read_bytes()
        if path.stem != _digest(raw):
            raise ValueError(f"public filename is not its byte hash: {path.name}")
        visible = json.loads(raw)
        if set(visible) != {"train", "test"} or type(visible["train"]) is not list \
                or type(visible["test"]) is not list or len(visible["test"]) != 1 \
                or set(visible["test"][0]) != {"input"}:
            raise ValueError(f"invalid public projection: {path.name}")
    return {"status": "passed", "episodes": len(manifest["records"]),
            "public_turns": len(public), "files": len(actual), "out": str(output)}


def _default_jobs() -> list[dict[str, Any]]:
    result = []
    for seed, demos in ((0, 2), (17, 3), (41, 6)):
        for scope in model.SCOPES:
            result.append({"seed": seed, "settings": {model.PARAMETER: scope}, "demos": demos})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--out", type=Path, required=True)
    build_parser.add_argument("--reliability-seeds", type=int, default=50)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build(args.out, _default_jobs(), reliability_seeds=args.reliability_seeds)
    else:
        result = verify(args.out)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
