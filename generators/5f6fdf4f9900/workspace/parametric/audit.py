"""Bounded reviewer-only Racket replay, finite-rival audit, and safe export.

Run through the packet's ``review.py run`` wrapper.  Give a solver only one
``turns/<public-content-sha256>.json`` file.  ``public_archive`` contains all
query inputs and is controller-facing; ``private`` and ``audit.json`` contain
answers, programs, settings, source identities, and finite audit findings.

Every rival is executable Racket.  Runtime errors abort the audit, never count
as an eliminated hypothesis. Queries are replayed only for demo survivors;
demo-refuted rules carry an explicit not-needed query status. Finite survivors
are findings, not evidence of universal ambiguity; finite elimination is not
an acceptance or training gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
TASK_ID = "5f6fdf4f9900"
SEEDS = (0, 17)


def _repo_root():
    for parent in HOME.parents:
        if (parent / "shared/runtime/reviewer_support.py").is_file():
            return parent
    raise FileNotFoundError("audit needs its own checkout's shared/runtime")


ROOT = _repo_root()
RUNTIME = ROOT / "shared/runtime"


def _load_exact(path, name):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import exact source {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path:
        raise ImportError(f"source import escaped {path}")
    return module


def load_adapter():
    return _load_exact(HOME / "adapter.py", "corner_priority_audit_adapter")


SUPPORT = _load_exact(RUNTIME / "reviewer_support.py", "corner_priority_audit_support")


def _runtime_modules():
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))
    modules = []
    for name in ("arc_repl.racket_bridge", "puzzle_generators.rule_wrap"):
        module = importlib.import_module(name)
        expected = (RUNTIME / (name.replace(".", "/") + ".py")).resolve()
        if Path(module.__file__).resolve() != expected:
            raise ImportError(f"{name} must come from this checkout: {expected}")
        modules.append(module)
    return tuple(modules)


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _write_json(path, value):
    with Path(path).open("xb") as handle:
        handle.write(_bytes(value))


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("Racket must return a nonempty 1..30 rectangular grid")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("Racket must return literal integer colors, never booleans")
    return value


def execute(bridge, wrapper, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in _grid(grid)) + ")"
    # RacketBridgeError deliberately propagates: an error is not a mismatch.
    return _grid(bridge.eval_text(f"({wrapper.wrap_rule(program)} {literal})"))


def public_turn(episode, query_index=0):
    """Project exactly the demos and one current query, with no future hints."""
    if (type(query_index) is not int or not 0 <= query_index < len(episode["test"])):
        raise ValueError("query_index must identify an existing query")
    # The shared helper both validates grid values and strips all private keys.
    raw = SUPPORT.public_challenge_bytes({"train": episode["train"],
                                          "test": [episode["test"][query_index]]})
    result = json.loads(raw)
    if set(result) != {"train", "test"} or len(result["test"]) != 1:
        raise ValueError("unsafe current-turn projection")
    return result


def public_first_turn(episode):
    return public_turn(episode, 0)


def _replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Racket rival anchor changed: {old!r}")
    return source.replace(old, new, 1)


_PICK = """(pick-max eligible
                           (lambda (d)
                             (at areas (+ r (first d)) (+ c (second d)))))"""
_AREA = """(obj-size
                        (first (filter
                          (lambda (o) (member (list ar ac) (obj-cells o)))
                          parts)))"""
_GATES = """(zero? (at g nr c))
                                (zero? (at g r nc))"""
_COLOR_COUNT = "(length (filter (lambda (v) (!= v 0)) (grid-colors g)))"


def rival_programs(adapter, settings):
    """A declared finite family; each entry is independently executed below."""
    largest = adapter.LARGEST_PROGRAM
    scan_template = _replace_once(largest, _PICK, "(first eligible)")
    selected = settings["corner_priority"]
    base = largest if selected == "largest_component" else scan_template
    other = "scan" if selected == "largest_component" else "largest_component"
    no_red = _replace_once(base, "(if (= lr lc) 2 0)", "(if (= lr lc) 0 0)")
    no_red = _replace_once(no_red, "(if (= lr (- (- n 1) lc)) 2 0)",
                           "(if (= lr (- (- n 1) lc)) 0 0)")
    result = {
        "other_setting": adapter.program({"corner_priority": other}),
        "last_eligible_candidate": _replace_once(largest, _PICK, "(last eligible)"),
        "smallest_component": _replace_once(largest, "(pick-max eligible", "(pick-min eligible"),
        "largest_component_tie_last": _replace_once(largest, "(pick-max eligible",
                                                       "(pick-max (reverse eligible)"),
        "whole_color_frequency": _replace_once(largest, _AREA,
            "(count (lambda (v) (= v (at g ar ac))) (flatten g))"),
        "eight_connected_component": _replace_once(largest, "(objects g 0)", "(objects-8 g 0)"),
        "component_bbox_area": _replace_once(largest, "(obj-size",
                                              "((lambda (o) (* (obj-h o) (obj-w o)))"),
        "ignore_orthogonal_gates": _replace_once(base, _GATES, "#t"),
        "no_red_corners": no_red,
        "fixed_scale_3": _replace_once(base, _COLOR_COUNT, "3"),
    }
    if len(set(result.values())) != len(result):
        raise ValueError("finite rivals unexpectedly duplicate one another")
    return result, base


def _difference(expected, actual):
    """One concrete cell (or shape) is enough to refute one false rule."""
    if expected == actual:
        return None
    result = {"expected_shape": [len(expected), len(expected[0])],
              "rival_shape": [len(actual), len(actual[0])],
              "expected_sha256": _sha(_bytes(expected)),
              "rival_sha256": _sha(_bytes(actual))}
    for r in range(min(len(expected), len(actual))):
        for c in range(min(len(expected[0]), len(actual[0]))):
            if expected[r][c] != actual[r][c]:
                result["cell"] = {"row": r, "col": c, "expected": expected[r][c],
                                  "rival": actual[r][c]}
                return result
    return result


def _source_inventory():
    paths = [HOME / name for name in ("adapter.py", "canonical.rkt", "promotion.json", "audit.py")]
    paths += [RUNTIME / name for name in (
        "reviewer_support.py", "puzzle_generators/rule_wrap.py", "arc_repl/racket_bridge.py",
        "arc_repl/security.py", "arc_repl/racket_prelude/arc-prelude.rkt")]
    return {path.relative_to(ROOT).as_posix(): _sha(path.read_bytes()) for path in paths}


def _public_file(out, folder, challenge):
    raw = SUPPORT.public_challenge_bytes(challenge)
    identity = SUPPORT.public_challenge_id(challenge)
    if identity != _sha(raw):
        raise ValueError("public helper identity differs from exact public bytes")
    path = out / folder / f"{identity}.json"
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("public identity collision")
    else:
        with path.open("xb") as handle:
            handle.write(raw)
    return {"id": identity, "path": path.relative_to(out).as_posix()}


def run(out):
    """Retain four small lessons; source drift, label mismatch, or errors fail."""
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(f"refusing to overwrite an existing output directory: {out}")
    sources = _source_inventory()
    adapter = load_adapter()
    bridge_module, wrapper = _runtime_modules()
    out.mkdir(parents=True, exist_ok=False)
    for folder in ("public_archive", "turns", "private", "private/rules"):
        (out / folder).mkdir()
    episodes, inputs_by_seed, input_shapes = [], {}, set()
    evaluated_labels, evaluated_rivals, equivalent_replays = 0, 0, 0
    saved_programs = set()

    def save_program(source):
        identity = _sha(source.encode())
        path = f"private/rules/{identity}.rkt"
        if identity not in saved_programs:
            with (out / path).open("x", encoding="utf-8") as handle:
                handle.write(source)
            saved_programs.add(identity)
        return {"sha256": identity, "path": path}

    with bridge_module.RacketBridge(timeout=15, max_calls_before_restart=128) as bridge:
        runtime = bridge.runtime_identity
        if runtime.get("protected") is not True or runtime.get("startup_handshake") != "pass":
            raise RuntimeError("live Racket runtime failed its protected handshake")
        for seed in SEEDS:
            for settings in adapter.SETTINGS:
                settings = dict(settings)
                episode = adapter.generate(seed, settings, demos=2, queries=4)
                if len(episode["train"]) != 2 or len(episode["test"]) != 4:
                    raise ValueError("audit requires exactly two demos and four queries")
                source = adapter.program(settings)
                if episode.get("program_solution") != source:
                    raise ValueError("episode does not bind the exact selected program")
                pairs = episode["train"] + episode["test"]
                inputs = [pair["input"] for pair in pairs]
                if seed in inputs_by_seed and inputs_by_seed[seed] != inputs:
                    raise ValueError("input sampling depends on hidden settings")
                inputs_by_seed[seed] = inputs
                for pair in pairs:
                    input_shapes.add((len(pair["input"]), len(pair["input"][0])))
                    actual = execute(bridge, wrapper, source, pair["input"])
                    evaluated_labels += 1
                    if actual != _grid(pair["output"]):
                        raise ValueError(f"Python/Racket label disagreement at seed={seed}, setting={settings}")
                    pair["output"] = actual
                one = adapter.generate(seed, settings, demos=2, queries=1)
                first = public_first_turn(episode)
                if SUPPORT.public_challenge_bytes(first) != SUPPORT.public_challenge_bytes(public_first_turn(one)):
                    raise ValueError("one-query and four-query first turns differ")
                archive = _public_file(out, "public_archive", episode)
                turns = [_public_file(out, "turns", public_turn(episode, i)) for i in range(4)]
                rivals, equivalent = rival_programs(adapter, settings)
                rule_binding = save_program(source)
                # The scan mutations share a clearer selection template; prove
                # that unmutated template equals the exact reference on every
                # retained pair before using it to state any rival result.
                for pair in pairs:
                    if execute(bridge, wrapper, equivalent, pair["input"]) != pair["output"]:
                        raise ValueError("rival construction baseline differs from selected reference")
                    equivalent_replays += 1
                rival_rows = []
                for name, rival in rivals.items():
                    mismatches = {"train": [], "test": []}
                    details = {}
                    for split in ("train", "test"):
                        if split == "test" and mismatches["train"]:
                            # Refutation on a shown demonstration is already
                            # decisive; held-out predictions matter only for
                            # hypotheses that survive every demonstration.
                            continue
                        for index, pair in enumerate(episode[split]):
                            actual = execute(bridge, wrapper, rival, pair["input"])
                            evaluated_rivals += 1
                            difference = _difference(pair["output"], actual)
                            if difference is not None:
                                mismatches[split].append(index)
                                details[(split, index)] = difference
                    row = {"name": name, "program": save_program(rival),
                           "demo_survives": not mismatches["train"],
                           "demo_disagreements": mismatches["train"],
                           "query_status": ("not_needed_demo_refuted" if mismatches["train"]
                                            else "executed_demo_survivor"),
                           "query_disagreements": mismatches["test"]}
                    if mismatches["train"]:
                        index = min(mismatches["train"], key=lambda i: (
                            len(episode["train"][i]["input"]) * len(episode["train"][i]["input"][0]), i))
                        row["minimal_demo_witness"] = {"demo_index": index,
                            "selection": "smallest retained disagreeing demo; then earliest index",
                            **details[("train", index)]}
                    elif mismatches["test"]:
                        index = mismatches["test"][0]
                        row["held_out_counterexample"] = {"query_index": index,
                                                          **details[("test", index)]}
                    rival_rows.append(row)
                survivors = [row["name"] for row in rival_rows if row["demo_survives"]]
                private = {"schema": "arcpuzzles-corner-priority-private-v1", "task_id": TASK_ID,
                           "seed": seed, "settings": settings, "sources": sources,
                           "label_backend": "live protected Racket", "program": rule_binding,
                           "mutation_baseline": save_program(equivalent),
                           "episode": episode, "public_archive": archive, "turns": turns,
                           "first_turn_independent_of_requested_query_count": True,
                           "finite_rivals": rival_rows, "demo_only_survivors": survivors}
                private_path = f"private/{archive['id']}.json"
                _write_json(out / private_path, private)
                episodes.append({"seed": seed, "settings": settings,
                                 "private_path": private_path,
                                 "public_archive": archive, "first_turn": turns[0],
                                 "demo_only_survivors": survivors,
                                 "rival_count": len(rival_rows)})
        final_runtime = bridge.runtime_identity
        if final_runtime.get("protected") is not True:
            raise RuntimeError("protected Racket identity lost during replay")
        for key in ("binary_sha256", "prelude_sha256", "bridge_sha256", "boot_script_sha256"):
            if final_runtime[key] != runtime[key]:
                raise RuntimeError(f"runtime source drift during audit: {key}")
    if _source_inventory() != sources:
        raise RuntimeError("source changed during replay; rerun into a new directory")
    finite_ok = all(not row["demo_only_survivors"] for row in episodes)
    report = {"schema": "arcpuzzles-corner-priority-finite-audit-v1", "task_id": TASK_ID,
              "status": "pass" if finite_ok else "finite_rival_survivors",
              "scope": "reviewer-only, four retained episodes and ten executable rivals per episode",
              "limits": "finite elimination does not prove universal uniqueness or confer acceptance or training admission",
              "sources": sources, "runtime": runtime, "episodes": episodes,
              "counts": {"episodes": len(episodes), "reference_label_replays": evaluated_labels,
                         "equivalent_baseline_replays": equivalent_replays,
                         "rival_pair_executions": evaluated_rivals,
                         "unique_racket_programs": len(saved_programs)},
              "input_shapes": sorted(map(list, input_shapes)),
              "checks": {"all_retained_labels_equal_live_racket": True,
                         "setting_independent_inputs": True,
                         "one_vs_four_query_first_turn_identical": True,
                         "all_rivals_eliminated_by_demos_only": finite_ok,
                         "public_names_derived_only_from_public_bytes": True,
                         "per_turn_has_one_query_no_private_or_future_fields": True},
              "visibility": {"solver": "exactly one turns/<sha256>.json file at a time",
                             "controller_only": ["public_archive/", "private/", "audit.json", "manifest.json"]}}
    _write_json(out / "audit.json", report)
    files = {path.relative_to(out).as_posix(): {"sha256": _sha(path.read_bytes()), "bytes": path.stat().st_size}
             for path in sorted(out.rglob("*")) if path.is_file()}
    _write_json(out / "manifest.json", {"schema": "arcpuzzles-corner-priority-export-manifest-v1",
                                       "sources": sources, "files": files})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new evidence directory; never overwritten")
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "counts": report["counts"], "checks": report["checks"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
