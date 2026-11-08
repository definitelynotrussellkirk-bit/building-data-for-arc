#!/usr/bin/env python3
"""Task-local, opt-in Racket-labelled prototype episodes and public export.

The certificate checks only the explicitly declared setting family. It never
uses query answers to choose surviving settings. Production/training admission
is outside this tool's scope.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path[:0] = [str(HERE), str(REPO / "shared/runtime")]
from reviewer_support import public_challenge_bytes, public_challenge_id
from puzzle_generators.rule_wrap import wrap_rule

FAMILIES = {"strip": "strip_stack", "focus": "focus_reconstruction"}
SCHEMA = "arcpuzzles-task-parametric-prototype-v1"


def _module(family):
    if type(family) is not str or family not in FAMILIES:
        raise ValueError("family must be strip or focus")
    return importlib.import_module(FAMILIES[family])


def _strict_equal(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _grid_bytes(grid):
    # The public helper validates exact numeric types and ARC bounds.
    visible = {"train": [{"input": grid, "output": grid}], "test": [{"input": grid}]}
    public_challenge_bytes(visible)
    return json.dumps(grid, separators=(",", ":")).encode()


def _sources(module):
    paths = [Path(__file__), Path(module.__file__),
             REPO / "generators/6b88648ff0e0/generator.py",
             REPO / "shared/runtime/reviewer_support.py",
             REPO / "shared/runtime/puzzle_generators/rule_wrap.py"]
    return {str(p.relative_to(REPO)): _sha(p.read_bytes()) for p in paths}


def execute(bridge, program, grid):
    _grid_bytes(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    # Modules may emit the exact canonical rule! text or a standalone lambda.
    # Route both through the shared normalization pipeline.
    rule_source = program if program.lstrip().startswith("(rule!") else "(rule! " + program + ")"
    output = bridge.eval_text("(" + wrap_rule(rule_source) + " " + literal + ")")
    _grid_bytes(output)
    return output


def certify(challenge, family, bridge):
    """Recompute demo survivors, then require agreement separately on each query."""
    public = json.loads(public_challenge_bytes(challenge))
    module = _module(family)
    survivors = []
    for setting in module.SETTINGS:
        program = module.render_program(setting)
        if all(execute(bridge, program, pair["input"]) == pair["output"]
               for pair in public["train"]):
            survivors.append(setting)
    if not survivors:
        raise ValueError("no declared setting fits the demonstrations")
    query_hashes = []
    for index, pair in enumerate(public["test"]):
        predictions = [execute(bridge, module.render_program(s), pair["input"]) for s in survivors]
        if any(p != predictions[0] for p in predictions[1:]):
            raise ValueError(f"underidentified query {index}: surviving settings disagree")
        query_hashes.append(_sha(_grid_bytes(predictions[0])))
    return {
        "schema": "declared-setting-demo-certificate-v1",
        "family": family,
        "declared_settings": list(module.SETTINGS),
        "survivors": survivors,
        "public_id": public_challenge_id(public),
        "query_prediction_sha256": query_hashes,
        "query_count": len(public["test"]),
        "scope": "declared settings only; query labels are not evidence for survivor selection",
    }


def _counts(n_demo, n_query, max_attempts):
    if any(type(v) is not int or not 1 <= v <= 8 for v in (n_demo, n_query)):
        raise ValueError("demo/query counts must be separate exact integers in 1..8")
    if type(max_attempts) is not int or not n_demo + n_query <= max_attempts <= 4096:
        raise ValueError("max_attempts must cover requested counts and be at most 4096")


def build_episode(family, setting, seed, *, bridge, n_demo=2, n_query=4,
                  input_seed=None, max_attempts=64):
    _counts(n_demo, n_query, max_attempts)
    if type(seed) is not int or (input_seed is not None and type(input_seed) is not int):
        raise ValueError("seed and input_seed must be exact integers")
    module = _module(family)
    program = module.render_program(setting)
    actual_input_seed = seed if input_seed is None else input_seed
    pairs, seen = [], set()
    for index in range(max_attempts):
        grid = module.sample_input(actual_input_seed, index)
        key = _grid_bytes(grid)
        if key in seen:
            continue
        output = execute(bridge, program, grid)
        if output != module.python_expected(grid, setting):
            raise ValueError("Racket/Python mismatch in generated label")
        seen.add(key)
        pairs.append({"input": grid, "output": output})
        if len(pairs) == n_demo + n_query:
            break
    if len(pairs) != n_demo + n_query:
        raise ValueError(f"distinct-input budget exhausted: {len(pairs)}/{n_demo+n_query}")
    challenge = {"train": pairs[:n_demo], "test": pairs[n_demo:]}
    certificate = certify(challenge, family, bridge)
    if setting not in certificate["survivors"]:
        raise ValueError("chosen setting was rejected by its own demonstrations")
    return {
        "schema": SCHEMA, "status": "proposed", "training_admitted": False,
        "family": family, "setting": setting, "seed": seed,
        "input_seed": actual_input_seed, "requested_counts": {"demo": n_demo, "query": n_query},
        "attempts": index + 1, "program": program,
        "program_sha256": _sha(program.encode()),
        "source_sha256": _sources(module), "challenge": challenge, "certificate": certificate,
    }


def verify_episode(episode, bridge):
    if episode.get("schema") != SCHEMA or episode.get("status") != "proposed" or episode.get("training_admitted") is not False:
        raise ValueError("expected an explicitly proposed, unadmitted prototype")
    if type(episode.get("seed")) is not int or type(episode.get("input_seed")) is not int:
        raise ValueError("stored seeds must be exact integers")
    attempts = episode.get("attempts")
    if type(attempts) is not int or not 1 <= attempts <= 4096:
        raise ValueError("stored attempts must be an exact integer in 1..4096")
    module = _module(episode.get("family"))
    program = module.render_program(episode.get("setting"))
    if episode.get("program") != program or episode.get("program_sha256") != _sha(program.encode()):
        raise ValueError("stored program does not match the exact setting/program hash")
    if episode.get("source_sha256") != _sources(module):
        raise ValueError("stored prototype source bindings are stale")
    challenge = episode["challenge"]
    public_challenge_bytes(challenge)
    counts = episode.get("requested_counts", {})
    if counts != {"demo": len(challenge["train"]), "query": len(challenge["test"])}:
        raise ValueError("stored counts disagree with the actual episode")
    _counts(counts["demo"], counts["query"], max(64, counts["demo"] + counts["query"]))
    if attempts < counts["demo"] + counts["query"]:
        raise ValueError("stored attempts cannot be smaller than the requested pair count")
    seen = set()
    for pair in challenge["train"] + challenge["test"]:
        key = _grid_bytes(pair["input"])
        if key in seen:
            raise ValueError("duplicate visible input within episode")
        seen.add(key)
        if "output" not in pair:
            raise ValueError("private episode is missing an executed label")
        _grid_bytes(pair["output"])
        expected = execute(bridge, program, pair["input"])
        if expected != pair["output"] or expected != module.python_expected(pair["input"], episode["setting"]):
            raise ValueError("private label mismatch")
    if not _strict_equal(episode.get("certificate"), certify(challenge, episode["family"], bridge)):
        raise ValueError("stored lesson certificate does not match fresh demo-only verification")
    return True


def write_batch(episodes, out, bridge):
    if type(episodes) is not list or not episodes:
        raise ValueError("batch must contain at least one episode")
    out = Path(out)
    if out.exists():
        raise ValueError("output path already exists")
    planned = []
    for episode in episodes:
        verify_episode(episode, bridge)
        raw = public_challenge_bytes(episode["challenge"])
        planned.append((public_challenge_id(episode["challenge"]), raw, episode))
    planned.sort(key=lambda row: row[0])
    if len({row[0] for row in planned}) != len(planned):
        raise ValueError("duplicate visible payload in batch")
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".parametric-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        private = []
        for public_id, raw, episode in planned:
            (stage / "public" / (public_id + ".json")).write_bytes(raw)
            private.append(dict(episode, public_id=public_id))
        (stage / "private/episodes.json").write_text(json.dumps(private, sort_keys=True, indent=2) + "\n")
        report = {
            "schema": SCHEMA, "status": "proposed", "training_admitted": False,
            "episode_count": len(planned), "public_ids": [r[0] for r in planned],
            "label_count": sum(len(r[2]["challenge"][s]) for r in planned for s in ("train", "test")),
            "runtime_identity": bridge.runtime_identity,
            "limits": ["Finite declared-setting checks do not prove universal rule uniqueness.",
                       "Prototype evidence grants neither production approval nor training admission."],
        }
        (stage / "private/verification.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
        stage.rename(out)
        return report
    except BaseException:
        shutil.rmtree(stage)
        raise


def verify_batch(path, bridge):
    path = Path(path)
    rows = json.loads((path / "private/episodes.json").read_text())
    ids = []
    for row in rows:
        verify_episode(row, bridge)
        public_id = public_challenge_id(row["challenge"])
        if row.get("public_id") != public_id:
            raise ValueError("private public-ID binding mismatch")
        if (path / "public" / (public_id + ".json")).read_bytes() != public_challenge_bytes(row["challenge"]):
            raise ValueError("public bytes differ from their exact visible projection")
        ids.append(public_id)
    if ids != sorted(set(ids)) or not ids:
        raise ValueError("batch must be nonempty, sorted and visibly distinct")
    if sorted(p.name for p in (path / "public").iterdir()) != [i + ".json" for i in ids]:
        raise ValueError("unexpected public files")
    report_path = path / "private/verification.json"
    try:
        report = json.loads(report_path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError("missing or invalid batch verification report") from error
    expected_fields = {
        "schema": SCHEMA, "status": "proposed", "training_admitted": False,
        "episode_count": len(rows), "public_ids": ids,
        "label_count": sum(len(row["challenge"][split]) for row in rows for split in ("train", "test")),
        "limits": ["Finite declared-setting checks do not prove universal rule uniqueness.",
                   "Prototype evidence grants neither production approval nor training admission."],
    }
    if not isinstance(report, dict) or set(report) != set(expected_fields) | {"runtime_identity"}:
        raise ValueError("batch verification report schema mismatch")
    if not _strict_equal({k: report[k] for k in expected_fields}, expected_fields):
        raise ValueError("batch verification report claims disagree with verified rows")
    stored_identity = report["runtime_identity"]
    current_identity = bridge.runtime_identity
    # Runtime paths are machine-local. All executable hashes and protection facts
    # must match the fresh bridge; moving the same checkout does not change them.
    if not isinstance(stored_identity, dict) or not _strict_equal(
            {k: v for k, v in stored_identity.items() if not k.endswith("_path")},
            {k: v for k, v in current_identity.items() if not k.endswith("_path")}):
        raise ValueError("batch runtime identity differs from the fresh protected bridge")
    return {"verified_episodes": len(rows), "public_ids": ids}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--family", choices=["strip", "focus", "both"], default="both")
    build.add_argument("--seed", type=int, default=20261023)
    build.add_argument("--n-demo", type=int, default=2)
    build.add_argument("--n-query", type=int, default=4)
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--batch", type=Path, required=True)
    args = parser.parse_args()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=20) as bridge:
        if args.command == "verify":
            result = verify_batch(args.batch, bridge)
        else:
            families = list(FAMILIES) if args.family == "both" else [args.family]
            episodes = [build_episode(f, s, args.seed, bridge=bridge, n_demo=args.n_demo, n_query=args.n_query)
                        for f in families for s in _module(f).SETTINGS]
            result = write_batch(episodes, args.out, bridge)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
