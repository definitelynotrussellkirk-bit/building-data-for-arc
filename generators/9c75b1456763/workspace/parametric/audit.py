"""Finite protected-Racket label and teaching audit for 9c75b1456763.

One seed, both declared settings, two demonstrations, and four queries are
deliberately the entire audit budget.  Candidate selection uses demonstrations
alone; query labels are consulted only after that selection.  The resulting
private evidence is source-bound and makes no claim of universal uniqueness.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "9c75b1456763"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEMOS = 2
QUERIES = 4
SCOPES = ("all_interiors", "unmarked_rooms")
CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
EIGHT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
RIVALS = {
    "global-first-marker": "Use the first row-major marker for every eligible marked network.",
    "nearest-marker-row": "Assign each eligible cell the marker with the nearest row; ties use row-major marker order.",
    "nearest-marker-column": "Assign each eligible cell the marker with the nearest column; ties use row-major marker order.",
    "nearest-Manhattan-marker": "Assign each eligible cell the nearest Manhattan marker; ties use row-major marker order.",
    "local-marker-room-only": "Restrict the scope's eligible cells to the erosion room containing the marker; unmarked_rooms therefore becomes identity.",
    "first-component-only": "Apply the selected scope to only the first row-major marked component.",
    "4-neighbor-fill": "Use complete cardinal neighborhoods for erosion and room separation, preserving the selected scope's marker-room exclusion.",
    "remote_by_radius_2": "For unmarked_rooms, replace connected-core exclusion with Chebyshev distance greater than two from the component marker; all_interiors retains its full mask.",
    "skip_first_core": "For unmarked_rooms, exclude the first row-major erosion core instead of the core containing the marker; all_interiors retains its full mask.",
}


def _raw(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_prototype():
    path = HERE / "prototype.py"
    source = path.read_bytes()
    name = "_9c75_audit_prototype_" + _sha(str(path).encode() + source)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load exact prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _sources() -> dict[str, str]:
    paths = (HERE / "prototype.py", HERE / "adapter.py", HERE / "audit.py", HERE.parents[1] / "generator.py")
    return {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in paths}


def _grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not value or not isinstance(value[0], list) or not value[0]:
        raise ValueError("expected a nonempty grid")
    width = len(value[0])
    if any(not isinstance(row, list) or len(row) != width or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in value):
        raise ValueError("expected a rectangular integer 0..9 grid")
    return value


def _difference(expected: list[list[int]], observed: list[list[int]]) -> dict:
    if len(expected) != len(observed) or len(expected[0]) != len(observed[0]):
        return {"shape_mismatch": True, "expected_shape": [len(expected), len(expected[0])], "observed_shape": [len(observed), len(observed[0])]}
    cells = [[r, c, expected[r][c], observed[r][c]] for r in range(len(expected)) for c in range(len(expected[0])) if expected[r][c] != observed[r][c]]
    return {"changed_cells": len(cells), "first_changed_cells": cells[:8], "cell_format": ["row", "column", "expected", "observed"]}


def _pieces(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        piece, frontier = {start}, [start]
        while frontier:
            r, c = frontier.pop()
            for dr, dc in CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    piece.add(neighbor)
                    frontier.append(neighbor)
        result.append(piece)
    return result


def rival_solve(grid: list[list[int]], settings: dict, name: str, prototype) -> list[list[int]]:
    """Independent description-level mirror for the authored wrong programs."""
    if name not in RIVALS or settings.get("fill_scope") not in SCOPES:
        raise ValueError("unknown rival or scope")
    output = deepcopy(grid)
    components = sorted((component for component in prototype.analyze(grid) if component["marker"] is not None), key=lambda component: min(component["cells"]))
    markers = sorted(component["marker"] for component in components)
    for component_index, component in enumerate(components):
        if name == "first-component-only" and component_index:
            continue
        marker = component["marker"]
        if name == "4-neighbor-fill":
            interiors = {p for p in component["cells"] if all((p[0] + dr, p[1] + dc) in component["cells"] for dr, dc in CARDINAL)}
            rooms = _pieces(interiors)
        else:
            interiors = set(component["interiors"])
            rooms = component["rooms"]
        marker_room = next((set(room) for room in rooms if marker[:2] in room), set())
        targets = interiors if settings["fill_scope"] == "all_interiors" else interiors - marker_room
        if settings["fill_scope"] == "unmarked_rooms" and name == "remote_by_radius_2":
            targets = {p for p in interiors if max(abs(p[0] - marker[0]), abs(p[1] - marker[1])) > 2}
        elif settings["fill_scope"] == "unmarked_rooms" and name == "skip_first_core":
            targets = interiors - min(rooms, key=min) if rooms else set()
        if name == "local-marker-room-only":
            targets &= marker_room
        for r, c in targets:
            selected = marker
            if name == "global-first-marker":
                selected = markers[0]
            elif name == "nearest-marker-row":
                selected = min(markers, key=lambda other: (abs(r - other[0]), other[0], other[1]))
            elif name == "nearest-marker-column":
                selected = min(markers, key=lambda other: (abs(c - other[1]), other[0], other[1]))
            elif name == "nearest-Manhattan-marker":
                selected = min(markers, key=lambda other: (abs(r - other[0]) + abs(c - other[1]), other[0], other[1]))
            output[r][c] = selected[2]
    return output


def rival_program(name: str, settings: dict) -> str:
    """Build finite, replayable Racket rivals without rewriting protected code."""
    if name not in RIVALS or settings.get("fill_scope") not in SCOPES:
        raise ValueError("unknown rival or scope")
    offsets = CARDINAL if name == "4-neighbor-fill" else EIGHT
    offsets_text = "'(" + " ".join(f"({dr} {dc})" for dr, dc in offsets) + ")"
    mask = "interiors" if settings["fill_scope"] == "all_interiors" else "(filter (lambda (p) (not (member p marker-room))) interiors)"
    if settings["fill_scope"] == "unmarked_rooms" and name == "remote_by_radius_2":
        mask = "(filter (lambda (p) (> (max (abs (- (first p) (first marker))) (abs (- (second p) (second marker)))) 2)) interiors)"
    elif settings["fill_scope"] == "unmarked_rooms" and name == "skip_first_core":
        mask = "(filter (lambda (p) (not (member p (or (first rooms) (list))))) interiors)"
    if name == "local-marker-room-only":
        mask = f"(filter (lambda (p) (member p marker-room)) {mask})"
    use_component = "(and marker (equal? cells first-marked))" if name == "first-component-only" else "marker"
    selection = "marker"
    if name == "global-first-marker":
        selection = "(first markers)"
    elif name in ("nearest-marker-row", "nearest-marker-column", "nearest-Manhattan-marker"):
        distance = {
            "nearest-marker-row": "(abs (- (first p) (first m)))",
            "nearest-marker-column": "(abs (- (second p) (second m)))",
            "nearest-Manhattan-marker": "(+ (abs (- (first p) (first m))) (abs (- (second p) (second m))))",
        }[name]
        selection = f"(pick-min markers (lambda (m) (+ (* h w {distance}) (* w (first m)) (second m))))"
    return f"""(rule!
 ;; Bounded rival: {name}; scope {settings['fill_scope']}.
 ;; {RIVALS[name]}
 ;; Unmarked blue components remain unchanged. Marker ties use row-major order.
 (lambda (g)
  (let ()
   (define networks (map obj-cells (objects (grid-from-fn h w (lambda (r c) (if (= (at g r c) 0) 0 1))) 0)))
   (define (marker-of cells) (for/first ((p cells) #:when (> (at g (first p) (second p)) 1)) p))
   (define markers (for*/list ((r (range h)) (c (range w)) #:when (> (at g r c) 1)) (list r c)))
   (define first-marked (for/first ((cells networks) #:when (marker-of cells)) cells))
   (define offsets {offsets_text})
   (define (interior? p)
    (and (> (first p) 0) (< (first p) (- h 1)) (> (second p) 0) (< (second p) (- w 1))
     (for/and ((d offsets)) (not (= (at g (+ (first p) (first d)) (+ (second p) (second d))) 0)))))
   (for/fold ((out g)) ((cells networks))
    (define marker (marker-of cells))
    (if {use_component}
     (let ()
      (define interiors (filter interior? cells))
      (define rooms (map obj-cells (objects (paint-cells (empty-grid h w 0) interiors 1) 0)))
      (define marker-room (or (for/first ((room rooms) #:when (member marker room)) room) (list)))
      (define targets {mask})
      (for/fold ((painted out)) ((p targets))
       (define selected {selection})
       (set-cell painted (first p) (second p) (at g (first selected) (second selected)))))
     out)))))
"""


class Oracle:
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        self.bridge = RacketBridge(timeout=15)
        self.identity = dict(self.bridge.runtime_identity)
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.shutdown()
            raise RuntimeError("audit requires the protected Racket runtime")
        self.wrap_rule = wrap_rule
        self.wrapped = {}
        self.cache = {}
        self.calls = 0
        self.cache_hits = 0
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.bridge.shutdown()
        return False

    def execute(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        key = (_sha(program.encode()), _sha(_raw(grid)))
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        if key[0] not in self.wrapped:
            self.wrapped[key[0]] = self.wrap_rule(program)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in _grid(grid)) + ")"
        self.calls += 1
        result = _grid(self.bridge.eval_text(f"({self.wrapped[key[0]]} {literal})"))
        self.cache[key] = deepcopy(result)
        return result


def run(seed: int = 0) -> dict:
    """Run exactly the documented finite audit; never search for passing seeds."""
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    prototype = _load_prototype()
    if tuple(prototype.SETTINGS) != tuple({"fill_scope": scope} for scope in SCOPES):
        raise ValueError("prototype SETTINGS differs from the audited two-scope contract")
    source_hashes = _sources()
    programs = []
    for scope in SCOPES:
        settings = {"fill_scope": scope}
        for name in ("declared", *RIVALS):
            source = prototype.program(settings) if name == "declared" else rival_program(name, settings)
            programs.append({"id": f"{scope}/{name}", "scope": scope, "kind": name, "sha256": _sha(source.encode()), "source": source})
    report = {
        "schema": "9c75b1456763-parametric-bounded-audit-v1",
        "task_id": TASK_ID,
        "private": True,
        "status": "running",
        "seed": seed,
        "budget": {"settings": len(SCOPES), "seeds": 1, "demonstrations_per_episode": DEMOS, "queries_per_episode": QUERIES, "candidate_programs": len(programs)},
        "source_hashes": source_hashes,
        "programs": programs,
        "rival_definitions": RIVALS,
        "episodes": [],
        "failures": [],
        "limits": [
            "Only the recorded seed, two settings, two demonstrations, and four queries per setting were checked.",
            "Demonstrations alone select survivors; query outputs are checked only after selection.",
            "The finite rival list is not a universal uniqueness proof and does not cover all seeds or all possible programs.",
            "This private audit does not grant native acceptance, canonical approval, or training admission.",
        ],
    }
    failures = report["failures"]
    witnesses = []
    label_count = 0
    mirror_checks = 0
    with Oracle() as oracle:
        report["runtime_identity"] = oracle.identity
        for scope in SCOPES:
            settings = {"fill_scope": scope}
            episode = prototype.generate(seed, settings, demos=DEMOS, queries=QUERIES)
            expected_id = f"{scope}/declared"
            selected_program = next(item for item in programs if item["id"] == expected_id)
            if episode.get("program_solution") != selected_program["source"] or episode.get("settings") != settings:
                failures.append({"kind": "private_metadata_mismatch", "scope": scope})
            if len(episode["train"]) != DEMOS or len(episode["test"]) != QUERIES:
                raise ValueError("prototype returned a different episode budget")
            record = {"settings": settings, "seed": seed, "labels": [], "candidate_checks": []}
            report["episodes"].append(record)
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    input_grid, label = _grid(pair["input"]), _grid(pair["output"])
                    python_output = _grid(prototype.solve(input_grid, settings))
                    racket_output = oracle.execute(selected_program["source"], input_grid)
                    label_count += 1
                    row = {"split": split, "index": index, "shape": [len(input_grid), len(input_grid[0])], "input_sha256": _sha(_raw(input_grid)), "label_sha256": _sha(_raw(label)), "python_matches": python_output == label, "racket_matches": racket_output == label}
                    record["labels"].append(row)
                    if not row["python_matches"] or not row["racket_matches"]:
                        failures.append({"kind": "label_mismatch", "scope": scope, **row, "python_difference": _difference(label, python_output), "racket_difference": _difference(label, racket_output)})
                    if split == "train":
                        witnesses.append((len(input_grid) * len(input_grid[0]), index, input_grid))
            survivors = []
            for candidate in programs:
                candidate_settings = {"fill_scope": candidate["scope"]}
                check = {"program_id": candidate["id"], "program_sha256": candidate["sha256"], "demo_exclusions": [], "demo_observations": []}
                for index, pair in enumerate(episode["train"]):
                    observed = oracle.execute(candidate["source"], pair["input"])
                    mirror = prototype.solve(pair["input"], candidate_settings) if candidate["kind"] == "declared" else rival_solve(pair["input"], candidate_settings, candidate["kind"], prototype)
                    mirror_checks += 1
                    if mirror != observed:
                        failures.append({"kind": "candidate_mirror_mismatch", "program_id": candidate["id"], "scope": scope, "demo_index": index, **_difference(mirror, observed)})
                    check["demo_observations"].append({"demo_index": index, "input_sha256": _sha(_raw(pair["input"])), "output_sha256": _sha(_raw(observed)), "matches_label": observed == pair["output"]})
                    if observed != pair["output"]:
                        check["demo_exclusions"].append({"demo_index": index, **_difference(pair["output"], observed)})
                check["survives_demonstrations"] = not check["demo_exclusions"]
                record["candidate_checks"].append(check)
                if check["survives_demonstrations"]:
                    survivors.append(candidate)
            record["demonstration_survivors"] = [candidate["id"] for candidate in survivors]
            record["declared_setting_survivors"] = [candidate["scope"] for candidate in survivors if candidate["kind"] == "declared"]
            if expected_id not in record["demonstration_survivors"]:
                failures.append({"kind": "selected_program_does_not_fit_demos", "scope": scope})
            record["query_disagreeing_survivors"] = []
            for candidate in survivors:
                check = next(item for item in record["candidate_checks"] if item["program_id"] == candidate["id"])
                check["query_disagreements"] = []
                for index, pair in enumerate(episode["test"]):
                    observed = oracle.execute(candidate["source"], pair["input"])
                    if observed != pair["output"]:
                        check["query_disagreements"].append({"query_index": index, "input_sha256": _sha(_raw(pair["input"])), "output_sha256": _sha(_raw(observed)), **_difference(pair["output"], observed)})
                if check["query_disagreements"]:
                    record["query_disagreeing_survivors"].append(candidate["id"])
                    failures.append({"kind": "demo_survivor_changes_query", "scope": scope, "program_id": candidate["id"], "query_indices": [row["query_index"] for row in check["query_disagreements"]]})
            record["excluded_candidate_count"] = len(programs) - len(survivors)
        wrong_id = "all_interiors/nearest-Manhattan-marker"
        wrong = next(item for item in programs if item["id"] == wrong_id)
        radius_id = "unmarked_rooms/remote_by_radius_2"
        radius = next(item for item in programs if item["id"] == radius_id)
        # Reuse cached demonstration outputs. Prefer a compact case witnessing
        # both the wrong component association and the fixed-radius shortcut.
        ranked_witnesses = []
        for area, index, input_grid in witnesses:
            true_all = oracle.execute(prototype.program({"fill_scope": "all_interiors"}), input_grid)
            true_remote = oracle.execute(prototype.program({"fill_scope": "unmarked_rooms"}), input_grid)
            has_assignment_difference = oracle.execute(wrong["source"], input_grid) != true_all
            has_radius_difference = oracle.execute(radius["source"], input_grid) != true_remote
            ranked_witnesses.append((not (has_assignment_difference and has_radius_difference), area, index, _sha(_raw(input_grid)), input_grid))
        witness_grid = min(ranked_witnesses, key=lambda item: item[:4])[4]
        outputs = {scope: oracle.execute(prototype.program({"fill_scope": scope}), witness_grid) for scope in SCOPES}
        wrong_output = oracle.execute(wrong["source"], witness_grid)
        radius_output = oracle.execute(radius["source"], witness_grid)
        report["labeled_semantic_case"] = {
            "origin": "smallest existing demonstration witnessing both assignment and radius shortcuts, if available; no extra sampling",
            "input": witness_grid,
            "scope_outputs": outputs,
            "scope_difference": _difference(outputs["all_interiors"], outputs["unmarked_rooms"]),
            "wrong_assignment_program_id": wrong_id,
            "wrong_assignment_output": wrong_output,
            "wrong_assignment_difference": _difference(outputs["all_interiors"], wrong_output),
            "radius_shortcut_program_id": radius_id,
            "radius_shortcut_output_sha256": _sha(_raw(radius_output)),
            "radius_shortcut_difference": _difference(outputs["unmarked_rooms"], radius_output),
            "component_intermediate": [{"first_cell": list(min(component["cells"])), "cell_count": len(component["cells"]), "marker": list(component["marker"]) if component["marker"] is not None else None, "interior_count": len(component["interiors"]), "room_sizes": sorted(len(room) for room in component["rooms"])} for component in prototype.analyze(witness_grid)],
            "dependency": "Connectivity assigns a marker to each network before the selected erosion-room mask is painted. Replacing that assignment with nearest-marker geometry can change the output.",
        }
        if outputs["all_interiors"] == outputs["unmarked_rooms"]:
            failures.append({"kind": "no_scope_difference_in_retained_case"})
        report["execution"] = {"protected_racket_calls": oracle.calls, "cache_hits": oracle.cache_hits, "labels_checked": label_count, "candidate_demo_mirror_checks": mirror_checks}
    report["source_hashes_unchanged"] = source_hashes == _sources()
    if not report["source_hashes_unchanged"]:
        failures.append({"kind": "source_changed_during_audit"})
    report["status"] = "pass" if not failures else "fail"
    report["no_query_disagreeing_survivor"] = all(not item["query_disagreeing_survivors"] for item in report["episodes"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.absolute()
    if output.exists() or any(path.is_symlink() for path in (output, *output.parents)):
        parser.error("refusing to overwrite an existing output or write through a symlink")
    report = run(args.seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "out": str(output), "execution": report["execution"], "no_query_disagreeing_survivor": report["no_query_disagreeing_survivor"], "failure_count": len(report["failures"])}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
