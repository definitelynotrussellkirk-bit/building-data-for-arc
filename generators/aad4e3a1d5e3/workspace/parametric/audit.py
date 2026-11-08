#!/usr/bin/env python3
"""Build and replay compact protected-Racket evidence for this prototype.

Public files are hash-named ARC views containing all demonstrations and exactly
one current query input. Private files retain settings, programs, answers,
future queries and finite teaching certificates.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Iterable

HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "adapter.py"
SCHEMA = "aad4e3a1d5e3-parametric-audit-v1"


def _load_adapter():
    name = "_aad4e3a1d5e3_parametric_audit_adapter_" + hashlib.sha256(str(ADAPTER_PATH).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = _load_adapter()


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode() + b"\n"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def _safe_path(root: Path, relative: str) -> Path:
    path = root / relative
    if path.resolve().parent != root.resolve() and not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("saved path escapes audit root")
    return path


def source_files() -> list[dict[str, str]]:
    paths = [HERE / name for name in ("adapter.py", "audit.py", "chain_only.rkt", "promotion.json")]
    return [
        {"path": path.relative_to(adapter.ROOT).as_posix(), "sha256": _file_digest(path)}
        for path in paths
    ]


def public_turn(episode: dict, query_index: int) -> dict:
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index outside episode")
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": episode["test"][query_index]["input"]}],
    }


class Oracle:
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        self._wrap_rule = wrap_rule
        self._bridge = RacketBridge(timeout=15)
        identity = self._bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires a protected Racket runtime")
        self.identity = {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        }
        self._wrapped: dict[str, str] = {}
        self.calls = 0
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._bridge.close()
        return False

    def apply(self, program: str, value: list[list[int]]) -> list[list[int]]:
        wrapped = self._wrapped.setdefault(program, self._wrap_rule(program))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in value) + ")"
        self.calls += 1
        return self._bridge.eval_text(f"({wrapped} {literal})")

    def check(self, episode: dict, settings: dict) -> dict:
        selected = settings["mode"]
        programs = {mode: adapter.program({"mode": mode}) for mode in adapter.MODES}
        survivors = [
            mode
            for mode, program in programs.items()
            if all(self.apply(program, pair["input"]) == pair["output"] for pair in episode["train"])
        ]
        if survivors != [selected]:
            raise ValueError(f"Racket demonstrations leave finite settings {survivors!r}")
        for pair in episode["test"]:
            if self.apply(programs[selected], pair["input"]) != pair["output"]:
                raise ValueError("Racket query label differs from generated output")
        certificate = adapter.certificate(episode["train"], [pair["input"] for pair in episode["test"]])
        if certificate["survivors"] != [selected]:
            raise ValueError("declared shortcut certificate differs from selected mode")
        return {
            "finite_setting_survivors": survivors,
            "certificate": certificate,
            "label_count": len(episode["train"]) + len(episode["test"]),
        }


def _validate_jobs(jobs: object) -> list[dict]:
    if type(jobs) is not list or not 1 <= len(jobs) <= 16:
        raise ValueError("jobs must be a list of 1..16 seed/settings objects")
    result = []
    for job in jobs:
        if type(job) is not dict or set(job) != {"seed", "settings"}:
            raise ValueError("each job needs exactly seed and settings")
        seed = adapter._integer(job["seed"], "seed", 0, 2**63 - 1)
        settings = adapter._settings(job["settings"])
        result.append({"seed": seed, "settings": settings})
    if len({encoded(job) for job in result}) != len(result):
        raise ValueError("duplicate audit job")
    return result


def _check_destination(output: Path) -> None:
    output = output.absolute()
    for path in (output, *output.parents):
        if path.is_symlink():
            raise ValueError("symlink destinations are forbidden")
    if output.exists():
        raise FileExistsError(output)


def build_audit(output: Path | str, jobs: object, *, demos: int = 3, queries: int = 4) -> dict:
    output = Path(output).absolute()
    _check_destination(output)
    jobs = _validate_jobs(jobs)
    demos = adapter._integer(demos, "demos", 2, 6)
    queries = adapter._integer(queries, "queries", 1, 4)
    bindings = source_files()
    assets: dict[str, bytes] = {}
    records = []
    seen_public: set[str] = set()
    program_hashes = {}
    for mode in adapter.MODES:
        raw = adapter.program({"mode": mode}).encode()
        identity = digest(raw)
        program_hashes[mode] = identity
        assets[f"private/programs/{identity}.rkt"] = raw

    with Oracle() as oracle:
        for job in jobs:
            episode = adapter.generate(job["seed"], job["settings"], demos, queries)
            mode = job["settings"]["mode"]
            checked = oracle.check(episode, job["settings"])
            turns = []
            for query_index, pair in enumerate(episode["test"]):
                visible = public_turn(episode, query_index)
                raw = encoded(visible)
                identity = digest(raw)
                if identity in seen_public:
                    raise ValueError("duplicate visible public turn")
                seen_public.add(identity)
                path = f"public/{identity}.json"
                assets[path] = raw
                turns.append({
                    "query_index": query_index,
                    "public_id": identity,
                    "public": path,
                    "answer": pair["output"],
                })
            one_query = adapter.generate(job["seed"], job["settings"], demos, 1)
            if encoded(public_turn(one_query, 0)) != assets[turns[0]["public"]]:
                raise ValueError("first public turn differs from one-query generation")
            private = {
                "schema": "aad4e3a1d5e3-parametric-audit-episode-v1",
                "task_id": adapter.TASK_ID,
                "seed": job["seed"],
                "settings": job["settings"],
                "demos": demos,
                "queries": queries,
                "program_sha256": program_hashes[mode],
                "train": episode["train"],
                "test": episode["test"],
                "query_turns": turns,
                "racket_check": checked,
                "training_admitted": False,
            }
            private_raw = encoded(private)
            private_id = digest(private_raw)
            private_path = f"private/{private_id}.json"
            assets[private_path] = private_raw
            records.append({
                "seed": job["seed"],
                "settings_sha256": digest(encoded(job["settings"])),
                "private": private_path,
                "public_ids": [turn["public_id"] for turn in turns],
            })
        racket_identity = oracle.identity
        racket_calls = oracle.calls

    if source_files() != bindings:
        raise ValueError("authoring sources changed during audit")
    manifest = {
        "schema": SCHEMA,
        "task_id": adapter.TASK_ID,
        "visibility": "controller-only",
        "records": records,
        "source_files": bindings,
        "programs": program_hashes,
        "demos": demos,
        "queries": queries,
        "racket": racket_identity,
        "racket_evaluations": racket_calls,
        "training_admitted": False,
        "scope": "Finite two-setting and declared-shortcut audit; no owner acceptance, universal uniqueness or training admission.",
        "files": {name: digest(raw) for name, raw in sorted(assets.items())},
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aad-parametric-audit-", dir=output.parent) as temp:
        stage = Path(temp) / "bundle"
        stage.mkdir()
        for name, raw in sorted(assets.items()):
            path = _safe_path(stage, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(raw)
        with (stage / "manifest.json").open("xb") as stream:
            stream.write(encoded(manifest))
        os.replace(stage, output)
    return {
        "episodes": len(records),
        "public_turns": len(records) * queries,
        "query_labels": len(records) * queries,
        "racket": racket_identity,
        "racket_evaluations": racket_calls,
        "training_admitted": False,
    }


def verify_audit(output: Path | str) -> dict:
    output = Path(output).absolute()
    for path in (output, *output.parents):
        if path.is_symlink():
            raise ValueError("symlink audit paths are forbidden")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    if (
        manifest.get("schema") != SCHEMA
        or manifest.get("task_id") != adapter.TASK_ID
        or manifest.get("visibility") != "controller-only"
        or manifest.get("training_admitted") is not False
    ):
        raise ValueError("invalid audit manifest metadata")
    if manifest.get("source_files") != source_files():
        raise ValueError("audit source bindings changed")
    demos = adapter._integer(manifest.get("demos"), "demos", 2, 6)
    queries = adapter._integer(manifest.get("queries"), "queries", 1, 4)
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path != manifest_path
    }
    declared = manifest.get("files")
    if type(declared) is not dict or set(declared) != actual:
        raise ValueError("audit file inventory differs")
    for name, wanted in declared.items():
        if _file_digest(_safe_path(output, name)) != wanted:
            raise ValueError(f"audit file hash changed: {name}")
    for mode in adapter.MODES:
        raw = adapter.program({"mode": mode}).encode()
        identity = digest(raw)
        if manifest.get("programs", {}).get(mode) != identity:
            raise ValueError("program identity changed")
        if _safe_path(output, f"private/programs/{identity}.rkt").read_bytes() != raw:
            raise ValueError("saved program changed")

    records = manifest.get("records")
    if type(records) is not list or not records:
        raise ValueError("audit records missing")
    seen_public: set[str] = set()
    with Oracle() as oracle:
        for record in records:
            private = json.loads(_safe_path(output, record["private"]).read_bytes())
            if (
                private.get("schema") != "aad4e3a1d5e3-parametric-audit-episode-v1"
                or private.get("task_id") != adapter.TASK_ID
                or private.get("training_admitted") is not False
                or private.get("demos") != demos
                or private.get("queries") != queries
            ):
                raise ValueError("invalid private audit record")
            reproduced = adapter.generate(private["seed"], private["settings"], demos, queries)
            if encoded({"train": private["train"], "test": private["test"]}) != encoded(
                {"train": reproduced["train"], "test": reproduced["test"]}
            ):
                raise ValueError("saved episode does not reproduce")
            mode = private["settings"]["mode"]
            if private["program_sha256"] != digest(adapter.program(private["settings"]).encode()):
                raise ValueError("private program identity changed")
            turns = private.get("query_turns")
            if type(turns) is not list or len(turns) != queries:
                raise ValueError("saved public turn count differs")
            for query_index, turn in enumerate(turns):
                visible = public_turn(reproduced, query_index)
                raw = encoded(visible)
                identity = digest(raw)
                if (
                    turn.get("query_index") != query_index
                    or turn.get("public_id") != identity
                    or turn.get("public") != f"public/{identity}.json"
                    or turn.get("answer") != reproduced["test"][query_index]["output"]
                    or _safe_path(output, turn["public"]).read_bytes() != raw
                ):
                    raise ValueError("public turn identity/projection changed")
                if identity in seen_public:
                    raise ValueError("duplicate public turn identity")
                seen_public.add(identity)
            one_query = adapter.generate(private["seed"], private["settings"], demos, 1)
            if encoded(public_turn(one_query, 0)) != _safe_path(output, turns[0]["public"]).read_bytes():
                raise ValueError("one-query first turn changed")
            checked = oracle.check(reproduced, private["settings"])
            if encoded(checked) != encoded(private["racket_check"]):
                raise ValueError("saved Racket/certificate evidence changed")
            if mode not in adapter.MODES:
                raise ValueError("unknown saved mode")
        if oracle.identity != manifest.get("racket"):
            raise ValueError("protected Racket runtime identity changed")
    return {
        "status": "replayed",
        "episodes": len(records),
        "public_turns": len(seen_public),
        "query_labels": len(records) * queries,
        "racket": oracle.identity,
        "racket_evaluations": oracle.calls,
        "training_admitted": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--seed", type=int, default=0)
    build.add_argument("--seed-count", type=int, default=2)
    build.add_argument("--demos", type=int, default=3)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--mode", choices=adapter.MODES + ("cycle",), default="cycle")
    verify = sub.add_parser("verify")
    verify.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    if args.action == "verify":
        result = verify_audit(args.directory)
    else:
        adapter._integer(args.seed_count, "seed-count", 1, 8)
        jobs = [
            {
                "seed": args.seed + index,
                "settings": {
                    "mode": adapter.MODES[index % len(adapter.MODES)] if args.mode == "cycle" else args.mode
                },
            }
            for index in range(args.seed_count)
        ]
        result = build_audit(args.out, jobs, demos=args.demos, queries=args.queries)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
