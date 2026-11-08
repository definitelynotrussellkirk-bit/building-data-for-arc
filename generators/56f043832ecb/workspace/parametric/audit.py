"""Protected-Racket finite-rival audit and strict one-query public export.

Run through the packet launcher. Serialized export verification checks exact
bytes, schemas and projections; it does not claim another Racket replay.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

TASK = "56f043832ecb"
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import canonical_pairs, public_challenge_bytes, public_challenge_id
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

EXPORT_SCHEMA = "56f043832ecb-public-turn-export-v1"
PRIVATE_SCHEMA = "56f043832ecb-private-turn-export-v1"
_HASH = re.compile(r"[0-9a-f]{64}\Z")


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _object(value, keys, name):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError(f"{name} must have exactly {sorted(keys)}")
    return value


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _digest(value):
    if type(value) is not str or not _HASH.fullmatch(value):
        raise ValueError("Expected a lowercase SHA-256 digest")


def _pairs(value, low, high, public_query=False):
    if type(value) is not list or not low <= len(value) <= high:
        raise ValueError("Pair count is outside this export's supported bounds")
    for pair in value:
        _object(pair, {"input"} if public_query else {"input", "output"}, "pair")
        for grid in pair.values():
            _grid(grid)


def _episode(value, serialized=False):
    keys = {"seed", "settings", "program", "train", "test"}
    if serialized:
        keys |= {"program_sha256", "turn_ids"}
    _object(value, keys, "private episode")
    _integer(value["seed"], 0, 2**63 - 1, "seed")
    _object(value["settings"], {"selection"}, "settings")
    if (type(value["settings"]["selection"]) is not str
            or value["settings"]["selection"] not in ("all", "largest", "smallest")):
        raise ValueError("Undeclared selection")
    if type(value["program"]) is not str or not value["program"].strip():
        raise ValueError("Private program must be exact nonempty text")
    _pairs(value["train"], 3, 6)
    _pairs(value["test"], 4, 4)
    inputs = [_bytes(pair["input"]) for split in ("train", "test") for pair in value[split]]
    if len(set(inputs)) != len(inputs):
        raise ValueError("Demo and query inputs must be distinct")
    if serialized:
        if value["program_sha256"] != _sha(value["program"].encode("utf-8")):
            raise ValueError("Private program hash mismatch")
        if type(value["turn_ids"]) is not list or len(value["turn_ids"]) != 4:
            raise ValueError("Each episode must cover all four public turns")
        for content_id in value["turn_ids"]:
            _digest(content_id)
    return copy.deepcopy(value)


def export_episodes(episodes, out, *, source_snapshot, racket):
    """Export private complete episodes and four independent visible files each."""
    out = Path(out)
    if out.exists():
        raise ValueError("Refusing to overwrite an existing export")
    if type(episodes) is not list or not episodes:
        raise ValueError("Export requires at least one complete episode")
    private, files = [], {}
    for episode in episodes:
        item = _episode(episode)
        item["program_sha256"] = _sha(item["program"].encode("utf-8"))
        item["turn_ids"] = []
        for query in item["test"]:
            visible = {"train": item["train"], "test": [query]}
            data, content_id = public_challenge_bytes(visible), public_challenge_id(visible)
            path = f"public/{content_id}.json"
            if path in files:
                raise ValueError("Duplicate public challenge bytes are not exportable")
            files[path] = data
            item["turn_ids"].append(content_id)
        private.append(item)
    files["private/episodes.json"] = _bytes({"schema": PRIVATE_SCHEMA, "task_id": TASK,
        "source_snapshot": source_snapshot, "racket": racket, "episodes": private})
    manifest = {"schema": EXPORT_SCHEMA, "task_id": TASK,
                "counts": {"episodes": len(private), "public_files": len(private) * 4},
                "files": [{"path": path, "sha256": _sha(data)} for path, data in sorted(files.items())]}
    out.mkdir(parents=True)
    for path, data in files.items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (out / "manifest.json").write_bytes(_bytes(manifest))
    return verify_export(out)


def _read_json(path):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result
    try:
        return json.loads(path.read_bytes(), object_pairs_hook=unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unreadable export JSON: {path.name}") from exc


def verify_export(out):
    """Strict schema/hash/projection verification, without executing private code."""
    out = Path(out)
    manifest = _read_json(out / "manifest.json")
    _object(manifest, {"schema", "task_id", "counts", "files"}, "manifest")
    if manifest["schema"] != EXPORT_SCHEMA or manifest["task_id"] != TASK:
        raise ValueError("Wrong export schema/task")
    counts = _object(manifest["counts"], {"episodes", "public_files"}, "counts")
    _integer(counts["episodes"], 1, 1000, "episode count")
    _integer(counts["public_files"], 4, 4000, "public file count")
    if counts["public_files"] != 4 * counts["episodes"]:
        raise ValueError("Every episode requires four public turns")
    if type(manifest["files"]) is not list:
        raise ValueError("Manifest files must be a list")
    inventory = {}
    for row in manifest["files"]:
        _object(row, {"path", "sha256"}, "manifest file")
        name = row["path"]
        if (type(name) is not str or name in inventory or
                (name != "private/episodes.json" and not re.fullmatch(r"public/[0-9a-f]{64}\.json", name))):
            raise ValueError("Unsafe, duplicate, or undeclared export path")
        _digest(row["sha256"])
        path = out / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(out.resolve()):
            raise ValueError("Missing or nonlocal export file")
        if _sha(path.read_bytes()) != row["sha256"]:
            raise ValueError("Manifest file hash mismatch")
        inventory[name] = row["sha256"]
    found = set()
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlinks are forbidden in exports")
        if path.is_file():
            found.add(path.relative_to(out).as_posix())
    if found != set(inventory) | {"manifest.json"}:
        raise ValueError("Missing or orphan export files")
    if set(inventory) - {"private/episodes.json"} != {n for n in inventory if n.startswith("public/")}:
        raise ValueError("Unexpected private export layout")
    if len(inventory) != counts["public_files"] + 1 or "private/episodes.json" not in inventory:
        raise ValueError("Manifest coverage does not match its counts")
    private = _read_json(out / "private/episodes.json")
    _object(private, {"schema", "task_id", "source_snapshot", "racket", "episodes"}, "private bundle")
    if private["schema"] != PRIVATE_SCHEMA or private["task_id"] != TASK:
        raise ValueError("Wrong private schema/task")
    if type(private["source_snapshot"]) is not dict or type(private["racket"]) is not dict:
        raise ValueError("Source/runtime metadata must be objects")
    for name, digest in private["source_snapshot"].items():
        if type(name) is not str or not name:
            raise ValueError("Invalid source snapshot path")
        _digest(digest)
    if type(private["episodes"]) is not list or len(private["episodes"]) != counts["episodes"]:
        raise ValueError("Private episode count mismatch")
    seen = set()
    for episode in private["episodes"]:
        _episode(episode, serialized=True)
        for index, content_id in enumerate(episode["turn_ids"]):
            if content_id in seen:
                raise ValueError("Repeated public turn coverage")
            seen.add(content_id)
            name = f"public/{content_id}.json"
            if name not in inventory:
                raise ValueError("Private turn is absent from the public inventory")
            visible = _read_json(out / name)
            _object(visible, {"train", "test"}, "public challenge")
            _pairs(visible["train"], 3, 6)
            _pairs(visible["test"], 1, 1, public_query=True)
            projection = {"train": episode["train"], "test": [episode["test"][index]]}
            expected = public_challenge_bytes(projection)
            if (out / name).read_bytes() != expected or _sha(expected) != content_id:
                raise ValueError("Public bytes, content ID, or private projection mismatch")
            if public_challenge_bytes(visible) != expected:
                raise ValueError("Public challenge canonicalization mismatch")
    if {f"public/{i}.json" for i in seen} != set(inventory) - {"private/episodes.json"}:
        raise ValueError("Uncovered public turn")
    return {"passed": True, **counts, "racket_replayed": False,
            "scope": "Exact serialized schemas, grids, counts, hashes, projections and file coverage"}


class MemoizedEvaluator:
    """One protected evaluation per exact program/input hash, including errors."""
    def __init__(self, execute):
        self.execute = execute
        self.results = {}
        self.requests = 0

    def __call__(self, program, grid):
        self.requests += 1
        key = (_sha(program.encode("utf-8")), _sha(_bytes(grid)))
        if key not in self.results:
            item = {"program_sha256": key[0], "input_sha256": key[1],
                    "program": program, "input": copy.deepcopy(grid)}
            try:
                item["output"] = _grid(self.execute(program, copy.deepcopy(grid)))
            except Exception as exc:
                item["error"] = {"type": type(exc).__name__, "message": str(exc)}
            self.results[key] = item
        item = self.results[key]
        if "error" in item:
            raise ValueError(f"Reference execution failed: {item['error']}")
        return copy.deepcopy(item["output"])


def audit_rivals(episode, rivals, execute):
    """Check every rival on every demo; execute queries only for demo survivors."""
    rows = []
    for rival in rivals:
        row = {**copy.deepcopy(rival), "program_sha256": _sha(rival["program"].encode()),
               "demo_outputs": [], "query_outputs": [], "first_refuting_demo": None,
               "first_disagreeing_query": None}
        errors = []
        for index, pair in enumerate(episode["train"]):
            try:
                row["demo_outputs"].append(_grid(execute(rival["program"], pair["input"])))
            except Exception as exc:
                error = {"split": "train", "index": index, "type": type(exc).__name__, "message": str(exc)}
                errors.append(error)
                row["demo_outputs"].append({"error": error})
        if errors:
            row.update(status="execution_error", errors=errors)
        else:
            mismatches = [i for i, (output, pair) in enumerate(zip(row["demo_outputs"], episode["train"]))
                          if output != pair["output"]]
            if mismatches:
                row.update(status="refuted", first_refuting_demo=mismatches[0])
            else:
                for index, pair in enumerate(episode["test"]):
                    try:
                        row["query_outputs"].append(_grid(execute(rival["program"], pair["input"])))
                    except Exception as exc:
                        error = {"split": "test", "index": index, "type": type(exc).__name__, "message": str(exc)}
                        errors.append(error)
                        row["query_outputs"].append({"error": error})
                if errors:
                    row.update(status="execution_error", errors=errors)
                else:
                    mismatches = [i for i, (output, pair) in enumerate(zip(row["query_outputs"], episode["test"]))
                                  if output != pair["output"]]
                    row["status"] = "query_disagreement" if mismatches else "finite_consistent"
                    row["first_disagreeing_query"] = mismatches[0] if mismatches else None
        rows.append(row)
    return {"passed": all(row["status"] in ("refuted", "finite_consistent") for row in rows),
            "rivals": rows,
            "scope": "Only named executable rivals on the stated demonstrations and queries; not universal uniqueness"}


def _replace(program, old, new):
    if program.count(old) != 1:
        raise ValueError(f"Rival patch does not name one exact source expression: {old}")
    return program.replace(old, new, 1)


def make_rivals(native, setting):
    """Nearby wrong rules; topology and painting helpers stay in protected Racket."""
    selection = setting["selection"]
    base = native.build_program(selection)
    rows = []

    def add(name, program, description):
        rows.append({"name": name, "program": program, "description": description})

    for other in ("all", "largest", "smallest"):
        if other != selection:
            add(f"selection_{other}", native.program({"selection": other}), f"Use {other} total-hole-area selection")
    hole_objects = "(objects (paint (empty-grid (rows sub) (cols sub) 0) holes 1) 0)"
    if selection != "all":
        scores = {
            "wall_count": ("(obj-size obj)", "Rank wall-cell count"),
            "bbox_area": ("(* (rows sub) (cols sub))", "Rank bounding-box area"),
            "inner_bbox_area": ("(* (max 0 (- (rows sub) 2)) (max 0 (- (cols sub) 2)))", "Rank the bounding-box interior"),
            "region_count": (f"(length {hole_objects})", "Rank the number of separate cavities"),
            "largest_cavity": (f"(let ((cavities {hole_objects})) (if (empty? cavities) 0 (apply max (map obj-size cavities))))", "Rank one largest cavity instead of total cavity area"),
            "color_aggregate_area": ("(for/sum ((peer (in-list (objects g 0)))) (if (= (obj-color peer) (obj-color obj)) (length (hole-mask (component-grid peer))) 0))", "Aggregate cavity area across disconnected components sharing a color"),
        }
        for name, (score, description) in scores.items():
            add(name, _replace(base, "(score (length holes))", f"(score {score})"), description)
        for tie in ("first", "last"):
            source = "(filter (lambda (record) (= (third record) target-score)) eligible)"
            add(f"tie_{tie}", _replace(base, source, f"(list ({tie} {source}))"),
                f"Keep only the {tie} extremum in row-major component order")
    for name, mode, score, description in (
        ("lowest_color", "smallest", "(obj-color obj)", "Choose the lowest numeric color"),
        ("highest_color", "largest", "(obj-color obj)", "Choose the highest numeric color"),
        ("topmost", "smallest", "(first bb)", "Choose the topmost component"),
        ("bottommost", "largest", "(third bb)", "Choose the bottommost component"),
        ("leftmost", "smallest", "(second bb)", "Choose the leftmost component"),
        ("rightmost", "largest", "(fourth bb)", "Choose the rightmost component"),
    ):
        add(name, _replace(native.build_program(mode), "(score (length holes))", f"(score {score})"), description)
    rectangular_zeros = "(filter (lambda (p) (= (at sub (first p) (second p)) 0)) (grid-positions sub))"
    add("bbox_fill", _replace(base, "(holes (hole-mask sub))", f"(holes {rectangular_zeros})"),
        "Treat every component-bbox zero as enclosed, including open pockets")
    perimeter = "(filter (lambda (p) (or (= (first p) 0) (= (second p) 0) (= (first p) (- (rows sub) 1)) (= (second p) (- (cols sub) 1)))) (grid-positions sub))"
    frame_only = f"(if (and (> (rows sub) 2) (> (cols sub) 2) (all? (lambda (p) (> (at sub (first p) (second p)) 0)) {perimeter})) (hole-mask sub) (list))"
    add("rectangle_only", _replace(base, "(holes (hole-mask sub))", f"(holes {frame_only})"),
        "Complete-bbox-perimeter-only: allow thick walls and multiple cavities, exclude exterior bbox zeros")
    no_border = "(if (or (= (first bb) 0) (= (second bb) 0) (= (third bb) (- (rows g) 1)) (= (fourth bb) (- (cols g) 1))) (list) (hole-mask sub))"
    add("skip_border", _replace(base, "(holes (hole-mask sub))", f"(holes {no_border})"),
        "Ignore components touching the canvas border")
    border_only = "(if (or (= (first bb) 0) (= (second bb) 0) (= (third bb) (- (rows g) 1)) (= (fourth bb) (- (cols g) 1))) (hole-mask sub) (list))"
    add("border_only", _replace(base, "(holes (hole-mask sub))", f"(holes {border_only})"),
        "Ignore strictly interior components; the converse of skip_border")
    add("missing_positive_filter", _replace(base, "(> (length (second record)) 0)", "#t"),
        "Let zero-hole components enter the extremum calculation")
    return rows


def _load_native():
    path = HOME / "native_family.py"
    data = path.read_bytes()
    name = "_audit_native_" + _sha(data)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(data, str(path), "exec"), module.__dict__)
    return module


def source_snapshot():
    paths = list(HOME.glob("*.py")) + [HOME / "canonical.rkt", HOME / "promotion.json",
        HOME.parents[1] / "generator.py", RUNTIME / "reviewer_support.py",
        ROOT / "src/arcpuzzles/parametric_worker.py"]
    paths += list((HOME.parents[1] / "tests").glob("test_native*.py"))
    return {path.relative_to(ROOT).as_posix(): _sha(path.read_bytes()) for path in sorted(paths)}


def _prefix_gap(episode, audit):
    """Reuse already executed demo outputs; this is an authored shorter lesson."""
    for row in audit["rivals"]:
        if row["name"] != "largest_cavity" or row["status"] == "execution_error":
            continue
        predictions = row["demo_outputs"]
        if (all(predictions[i] == episode["train"][i]["output"] for i in (0, 1))
                and predictions[2] != episode["train"][2]["output"]):
            return {"status": "authored_short_prefix_gap_repaired_by_third_demo",
                    "seed": episode["seed"], "settings": episode["settings"],
                    "train": episode["train"][:2], "program": episode["program"],
                    "rival_name": row["name"], "rival_program": row["program"],
                    "query": {"input": episode["train"][2]["input"],
                              "output": episode["train"][2]["output"],
                              "rival_output": predictions[2]},
                    "scope": "Deliberately shortened authored lesson; production uses all three demonstrations"}
    return None


def run_audit(out, seeds=(0, 17)):
    out = Path(out)
    if out.exists():
        raise ValueError("Use a fresh audit output directory")
    out.mkdir(parents=True)
    before = source_snapshot()
    native = _load_native()
    episodes, reports, canonical, gaps, first_turns = [], [], [], [], []
    paired_inputs = {}
    with _local_imports(RUNTIME, HOME):
        execute, identity, bridge = _real_evaluator(RUNTIME)
        cached = MemoizedEvaluator(execute)
        try:
            pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
            if len(pairs) != 4:
                raise ValueError("Expected the exact four labeled canonical pairs")
            for pair in pairs:
                output = cached(native.program(native.DEFAULT), pair["input"])
                twin = cached(native.build_program("all"), pair["input"])
                canonical.append({**pair, "executed_output": output, "explicit_all_output": twin,
                                  "passed": output == pair["output"] == twin})
            for seed in seeds:
                for setting in native.SETTINGS:
                    claims = native.generate(seed, setting, 3, 4)
                    episode = {"seed": seed, "settings": copy.deepcopy(setting),
                               "program": claims["program_solution"], "train": [], "test": []}
                    labels_match = True
                    for split in ("train", "test"):
                        for pair in claims[split]:
                            output = cached(episode["program"], pair["input"])
                            labels_match &= output == pair["output"]
                            episode[split].append({"input": copy.deepcopy(pair["input"]), "output": output})
                    inputs = _bytes({s: [p["input"] for p in episode[s]] for s in ("train", "test")})
                    if seed in paired_inputs and paired_inputs[seed] != inputs:
                        raise ValueError("Settings must share all ordered inputs for a seed")
                    paired_inputs[seed] = inputs
                    one_query = native.generate(seed, setting, 3, 1)
                    first = {"train": episode["train"], "test": episode["test"][:1]}
                    same_first = public_challenge_bytes(one_query) == public_challenge_bytes(first)
                    first_turns.append({"seed": seed, "settings": setting, "passed": same_first,
                                        "visible_sha256": public_challenge_id(first)})
                    checked = audit_rivals(episode, make_rivals(native, setting), cached)
                    checked.update(seed=seed, settings=setting, claim_labels_match_racket=labels_match)
                    checked["component_metadata"] = {split: [native.analyze_grid(p["input"])
                        for p in episode[split]] for split in ("train", "test")}
                    gap = _prefix_gap(episode, checked)
                    if gap is not None:
                        gaps.append(gap)
                    episodes.append(episode)
                    reports.append(checked)
        finally:
            bridge.close()
    after = source_snapshot()
    passed = (before == after and all(p["passed"] for p in canonical)
              and all(r["passed"] and r["claim_labels_match_racket"] for r in reports)
              and all(row["passed"] for row in first_turns))
    result = {"schema": "56f043832ecb-finite-rival-audit-v1", "task_id": TASK, "passed": passed,
              "racket": identity, "source_snapshot_before": before, "source_snapshot_after": after,
              "sources_unchanged": before == after,
              "scope": {"seeds": list(seeds), "settings": list(native.SETTINGS), "demos": 3, "queries": 4,
                        "episodes": len(episodes), "canonical_pairs": len(canonical),
                        "rival_episode_checks": sum(len(r["rivals"]) for r in reports),
                        "execution_requests": cached.requests, "unique_racket_executions": len(cached.results),
                        "claims": "Finite named rivals only; no universal uniqueness or native acceptance"},
              "canonical": canonical, "episodes": episodes, "audits": reports,
              "first_turn_equality": first_turns, "authored_prefix_gaps": gaps}
    (out / "audit.json").write_bytes(_bytes(result))
    (out / "executions.json").write_bytes(_bytes({"racket": identity, "executions": list(cached.results.values())}))
    if passed:
        verification = export_episodes(episodes, out / "export", source_snapshot=before, racket=identity)
        (out / "export-verification.json").write_bytes(_bytes(verification))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out", required=True, type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_audit(args.out) if args.command == "run" else verify_export(args.path)
    except Exception as exc:
        print(json.dumps({"passed": False, "error": type(exc).__name__, "message": str(exc)}))
        return 1
    summary = {key: value for key, value in result.items() if key in ("passed", "scope", "episodes", "public_files")}
    if args.command == "run":
        summary.pop("episodes", None)
        summary["report"] = str(args.out / "audit.json")
        summary["failures"] = [{"seed": row["seed"], "settings": row["settings"],
                                "rival": rival["name"], "status": rival["status"]}
                               for row in result["audits"] for rival in row["rivals"]
                               if rival["status"] not in ("refuted", "finite_consistent")]
    print(json.dumps(summary, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
