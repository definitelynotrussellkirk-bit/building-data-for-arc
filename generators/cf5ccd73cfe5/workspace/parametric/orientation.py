"""Task-local orientation variants and bounded native-promotion authoring tools."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shlex
import sys
import types

from reviewer_support import public_challenge_bytes, public_challenge_id

ROOT = Path(__file__).resolve().parents[4]
TASK = "cf5ccd73cfe5"
HOME = ROOT / "generators" / TASK
SETTINGS = ("identity", "flip_lr", "flip_ud", "rot180")
DEFAULT = "identity"
LOOKUP = "(hash-has-key? marker-set (list mr mc))"
LIMITATIONS = [
    "Proposed prototype only; no production parametric API, approval, or training admission.",
    "One bounded orientation parameter; no quarter-turn setting because independent scales and rectangular marker dimensions would change roles.",
    "Rejects any marker with fewer than four distinct orientation outputs; one-dimensional and symmetric shapes cannot teach all settings.",
    "Independent 2..6 demonstration and 1..4 query counts; CLI defaults to 3 and 4; bounded 256 input attempts.",
    "Canonical production sampling is unchanged; the separate query grammar includes 8x8 through substantive 30x30 scenes.",
    "Finite teaching audit includes the four orientations and eight named shortcuts under each orientation, not arbitrary programs.",
    "Finite seed and setting evidence; no assertion about every future generator version or all seeds.",
    "For a quarter-turn of the input, the LR/UD comparison swaps axes; episode semantics themselves remain fixed in input coordinates.",
]


def digest(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def canonical_rows():
    """Read only selected-task rows into the authoring workflow."""
    rows = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    if not rows or len({row["program_solution"] for row in rows}) != 1:
        raise ValueError("expected one exact canonical program across selected-task rows")
    return rows


def program(orientation=DEFAULT):
    if orientation not in SETTINGS:
        raise ValueError(f"unsupported orientation: {orientation!r}")
    source = canonical_rows()[0]["program_solution"]
    if source.count(LOOKUP) != 1:
        raise ValueError("canonical membership lookup changed; explicit review required")
    if orientation == DEFAULT:
        return source  # Keep exact canonical bytes, including whitespace.
    row = "(- marker-h 1 mr)" if orientation in ("flip_ud", "rot180") else "mr"
    col = "(- marker-w 1 mc)" if orientation in ("flip_lr", "rot180") else "mc"
    return source.replace(LOOKUP, f"(hash-has-key? marker-set (list {row} {col}))")


def generator():
    spec = importlib.util.spec_from_file_location("orientation_canonical_generator", HOME / "generator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def choose_orientation(seed):
    """Choose the hidden rule once, independently of scene/rejection draws."""
    return random.Random(f"{TASK}:orientation-v1:{seed}").choice(SETTINGS)


def execute(bridge, source, grid):
    # The portable source layout stores legacy scripts under shared/tools;
    # expose that local namespace to the existing normalization helper.
    if "scripts" not in sys.modules:
        scripts = types.ModuleType("scripts")
        scripts.__path__ = [str(ROOT / "shared/tools")]
        sys.modules["scripts"] = scripts
    from puzzle_generators.rule_wrap import wrap_rule
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    result = bridge.eval_text(f"({wrap_rule(source)} {literal})")
    if not isinstance(result, list) or not result or any(not isinstance(row, list) for row in result):
        raise ValueError("Racket did not return a nonempty grid")
    return result


def outputs_for(bridge, grid, programs=None):
    programs = programs or {setting: program(setting) for setting in SETTINGS}
    return {setting: execute(bridge, programs[setting], grid) for setting in SETTINGS}


def equal_groups(outputs):
    groups = {}
    for setting, grid in outputs.items():
        groups.setdefault(encoded(grid), []).append(setting)
    return [group for group in groups.values() if len(group) > 1]


class EpisodeSamplingError(RuntimeError):
    def __init__(self, seed, orientation, rejections, attempts):
        super().__init__(f"could not build the requested distinct identifiable pairs in {attempts} attempts")
        self.details = dict(seed=seed, orientation=orientation, rejections=rejections, attempts=attempts)


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def reflect(grid, orientation):
    """Mirror a prediction in output coordinates, preserving its frame."""
    result = [row[:] for row in grid]
    if orientation in ("flip_ud", "rot180"):
        result.reverse()
    if orientation in ("flip_lr", "rot180"):
        result = [row[::-1] for row in result]
    return result


def shortcut_outputs(grid, gen=None):
    """Explicit Python rival predictions; the true labels are executed in Racket."""
    gen = gen or generator()
    facts, errors = gen._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    base = {name: function(grid) for name, function in gen.CANONICAL_SHORTCUTS.items()}
    mr, mc, _, _ = facts["marker_bbox"]
    mh, mw = facts["marker_h"], facts["marker_w"]
    for name in ("solid_fill", "tile_marker", "unscaled_marker"):
        output = [[facts["frame_color"]] * facts["frame_w"] for _ in range(facts["frame_h"])]
        for r in range(facts["frame_h"] - 2):
            for c in range(facts["frame_w"] - 2):
                if name == "solid_fill":
                    occupied = True
                elif name == "tile_marker":
                    occupied = grid[mr + r % mh][mc + c % mw] == facts["marker_color"]
                else:
                    occupied = r < mh and c < mw and grid[mr + r][mc + c] == facts["marker_color"]
                output[r + 1][c + 1] = facts["marker_color"] if occupied else 0
        base[name] = output
    return {f"{name}/{setting}": reflect(output, setting)
            for name, output in base.items() for setting in SETTINGS}


def query_scene(seed, query_index, attempt=0, gen=None):
    """Independent input stream; large frames genuinely scale with the canvas.

    Profiles are (canvas H/W, marker H/W, repetition H/W). The last frame is
    26x26 with a 3x6 marker across the opposite edge of a 30x30 input.
    Transposition and whole-scene reflections preserve the input grammar.
    """
    profiles = ((8, 8, 2, 3, 1, 1), (18, 24, 3, 4, 4, 5),
                (24, 30, 3, 5, 6, 5), (30, 30, 3, 6, 8, 4))
    _integer("query_index", query_index, 0, 3)
    _integer("attempt", attempt, 0, 4096)
    rng = random.Random(f"{TASK}:native-query-v1:{seed}:{query_index}:{attempt}")
    gen = gen or generator()
    h, w, mh, mw, sh, sw = profiles[query_index]
    fh, fw = mh * sh + 2, mw * sw + 2
    frame_color, marker_color = rng.sample(range(1, 10), 2)
    grid = [[0] * w for _ in range(h)]
    fr = rng.randrange(h - fh - 1 - mh + 1)
    fc = rng.randrange(w - fw + 1) if query_index < 3 else 0
    marker_r, marker_c = fr + fh + 1, w - mw
    for r in range(fr, fr + fh):
        for c in range(fc, fc + fw):
            if r in (fr, fr + fh - 1) or c in (fc, fc + fw - 1):
                grid[r][c] = frame_color
    for r, c in gen._marker(rng, mh, mw):
        grid[marker_r + r][marker_c + c] = marker_color
    if rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    return reflect(grid, rng.choice(SETTINGS))


def build_episode(seed, bridge, orientation=None, *, demos=3, queries=1, max_attempts=256):
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _integer("max_attempts", max_attempts, 0, 4096)
    orientation = choose_orientation(seed) if orientation is None else orientation
    if type(orientation) is not str or orientation not in SETTINGS:
        raise ValueError(f"unsupported orientation: {orientation!r}")
    programs = {setting: program(setting) for setting in SETTINGS}
    gen = generator()
    accepted, rejections, seen = [], [], set()
    attempts = 0

    def consider(grid, split, index):
        nonlocal attempts
        attempts += 1
        errors = gen.self_check(grid)
        if errors:
            raise ValueError(f"input sampler returned an unlawful input: {errors}")
        fingerprint = encoded(grid)
        if fingerprint in seen:
            rejections.append({"split": split, "sample_index": index, "reason": "duplicate input"})
            return False
        outputs = outputs_for(bridge, grid, programs)
        groups = equal_groups(outputs)
        if groups:
            rejections.append({"split": split, "sample_index": index, "reason": "orientation ambiguity", "equal_groups": groups,
                               "input": grid, "output_sha256": {s: digest(encoded(o)) for s, o in outputs.items()}})
            return False
        # Select a distinguishing first demo before choosing the hidden setting.
        # Unlike the old raw-index schedule argument, this checks accepted pairs.
        if not accepted:
            shortcuts = shortcut_outputs(grid, gen)
            matching = [name for name, predicted in shortcuts.items()
                        if any(predicted == gold for gold in outputs.values())]
            if matching:
                rejections.append({"split": split, "sample_index": index,
                                   "reason": "shortcut teaching", "matching": matching})
                return False
        seen.add(fingerprint)
        accepted.append({"split": split, "sample_index": index, "input": grid, "outputs": outputs})
        return True

    index = 0
    while len(accepted) < demos and attempts < max_attempts:
        consider(gen.generate(seed, index), "train", index)
        index += 1
    if len(accepted) != demos:
        raise EpisodeSamplingError(seed, orientation, rejections, attempts)
    for query_index in range(queries):
        retry = 0
        while attempts < max_attempts:
            grid = query_scene(seed, query_index, retry, gen)
            if consider(grid, "test", {"query_index": query_index, "attempt": retry}):
                break
            retry += 1
        else:
            raise EpisodeSamplingError(seed, orientation, rejections, attempts)
    public = {"train": [{"input": pair["input"], "output": pair["outputs"][orientation]} for pair in accepted[:demos]],
              "test": [{"input": pair["input"]} for pair in accepted[demos:]]}
    rivals = {rival: {"demo_mismatches": [i for i, pair in enumerate(accepted[:demos]) if pair["outputs"][rival] != pair["outputs"][orientation]],
                      "query_differs": [pair["outputs"][rival] != pair["outputs"][orientation] for pair in accepted[demos:]]}
              for rival in SETTINGS if rival != orientation}
    shortcut_predictions = [shortcut_outputs(pair["input"], gen) for pair in accepted]
    self_review = {}
    for rival in shortcut_predictions[0]:
        mismatches = [i for i in range(demos)
                      if shortcut_predictions[i][rival] != accepted[i]["outputs"][orientation]]
        query_differs = [shortcut_predictions[i][rival] != accepted[i]["outputs"][orientation]
                         for i in range(demos, demos + queries)]
        self_review[rival] = {"demo_mismatches": mismatches, "query_differs": query_differs}
    ambiguous = [name for name, item in self_review.items()
                 if not item["demo_mismatches"] and any(item["query_differs"])]
    if ambiguous:
        raise RuntimeError(f"accepted lesson has undeclared teaching gap: {ambiguous}")
    private = {"schema": "arc-task-local-orientation-prototype-v1", "status": "proposed prototype",
               "task_id": TASK, "seed": seed, "parameters": {"orientation": orientation},
               "program_sha256": digest(programs[orientation]),
               "query_outputs": [pair["outputs"][orientation] for pair in accepted[demos:]],
               "accepted": accepted, "rejections": rejections, "attempts": attempts,
               "rivals": rivals, "self_review": {"rivals": self_review, "ambiguous_rivals": ambiguous,
                    "scope": "32 Python shortcut predictions and three Racket orientation rivals; no universal uniqueness claim"},
               "public_sha256": public_challenge_id(public)}
    return public, private


def rotate(grid, turns=1):
    result = grid
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def rotation_checks(bridge, query, programs=None):
    programs = programs or {s: program(s) for s in SETTINGS}
    original = outputs_for(bridge, query, programs)
    checks = []
    for turns in range(4):
        for setting in SETTINGS:
            comparison = {"flip_lr": "flip_ud", "flip_ud": "flip_lr"}.get(setting, setting) if turns % 2 else setting
            grid = rotate(query, turns)
            output = execute(bridge, programs[setting], grid)
            expected = rotate(original[comparison], turns)
            checks.append({"quarter_turns": turns, "orientation": setting, "comparison_orientation": comparison,
                           "input": grid, "output": output, "expected_sha256": digest(encoded(expected)), "passed": output == expected})
    return checks


def symmetry_fixture():
    grid = [[0] * 12 for _ in range(12)]
    for r in range(5):
        for c in range(8):
            if r in (0, 4) or c in (0, 7):
                grid[r][c] = 1
    for r, c in ((7, 1), (8, 2), (9, 3)):
        grid[r][c] = 2
    return grid


def source_hashes():
    paths = [HOME / "generator.py", HOME / "tests/test_parametric_orientation.py",
             HOME / "tests/test_native_orientation.py",
             Path(__file__).with_name("promotion.json"),
             ROOT / "shared/runtime/reviewer_support.py",
             ROOT / "shared/runtime/arc_repl/racket_bridge.py",
             ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
             ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
             ROOT / "shared/tools/comment_solutions.py"]
    paths += sorted(Path(__file__).parent.glob("*.py")) + sorted(Path(__file__).parent.glob("*.md"))
    return {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in paths}


def public_filename(seed, public):
    """Exact visible-byte identity; the legacy seed argument is intentionally ignored."""
    return public_challenge_id(public) + ".json"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--orientation", choices=(*SETTINGS, "auto", "all"), default="all")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True, help="new authoring evidence directory")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "public").mkdir()
    (args.out / "private").mkdir()
    (args.out / "programs").mkdir()
    programs = {s: program(s) for s in SETTINGS}
    for s, text in programs.items():
        (args.out / "programs" / f"{s}.rkt").write_text(text)
    receipt = {"schema": "arc-task-local-parametric-evidence-v1", "status": "proposed prototype", "task_id": TASK,
               "seed": args.seed, "settings": list(SETTINGS), "default": DEFAULT,
               "command": shlex.join([sys.executable, "../run_with_racket.py", sys.executable, *sys.argv]),
               "payload_cwd": "WORK/repo", "source_sha256": source_hashes(),
               "canonical_selected_rows_sha256": digest(encoded(canonical_rows())),
               "programs": {s: {"path": f"programs/{s}.rkt", "sha256": digest(text)} for s, text in programs.items()},
               "auto_setting": choose_orientation(args.seed), "failures": [], "limitations": LIMITATIONS}
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
    receipt["runtime"] = racket_runtime_status()
    settings = SETTINGS if args.orientation == "all" else (choose_orientation(args.seed) if args.orientation == "auto" else args.orientation,)
    episodes = []
    try:
        with RacketBridge() as bridge:
            canonical = []
            for row in canonical_rows():
                for split in ("train", "test"):
                    for index, pair in enumerate(row.get(split, [])):
                        actual = execute(bridge, programs[DEFAULT], pair["input"])
                        canonical.append({"source": row["source"], "split": split, "index": index,
                                          "output": actual, "passed": actual == pair["output"]})
            write_json(args.out / "private/canonical.json", canonical)
            receipt["canonical_pairs"] = {"checked": len(canonical), "passed": sum(c["passed"] for c in canonical)}
            if not all(c["passed"] for c in canonical):
                raise AssertionError("canonical identity mismatch")
            built = []
            for setting in settings:
                public, private = build_episode(args.seed, bridge, setting, demos=args.demos, queries=args.queries)
                filename = public_filename(args.seed, public)
                built.append((filename, setting, public, private))
            if len({item[0] for item in built}) != len(built):
                raise ValueError("duplicate visible challenge")
            for filename, setting, public, private in sorted(built):
                (args.out / "public" / filename).write_bytes(public_challenge_bytes(public))
                write_json(args.out / "private" / filename, private)
                episodes.append({"public_path": f"public/{filename}", "private_path": f"private/{filename}", "orientation": setting, "demonstrations": args.demos, "queries": args.queries,
                                 "attempts": private["attempts"], "rejected": len(private["rejections"]), "rivals": private["rivals"]})
            rotations = rotation_checks(bridge, public["test"][0]["input"], programs)
            write_json(args.out / "private/query-rotations.json", rotations)
            receipt["query_rotations"] = {"checked": len(rotations), "passed": sum(c["passed"] for c in rotations)}
            if not all(c["passed"] for c in rotations):
                raise AssertionError("query rotation mismatch")
            fixture = symmetry_fixture()
            outputs = outputs_for(bridge, fixture, programs)
            write_json(args.out / "private/symmetric-rejection.json", {"input": fixture, "outputs": outputs,
                       "equal_groups": equal_groups(outputs), "reason": "rejected: orientation ambiguity"})
            if not equal_groups(outputs):
                raise AssertionError("symmetric fixture unexpectedly identifiable")
    except Exception as exc:
        receipt["failures"].append({"type": type(exc).__name__, "message": str(exc), "details": getattr(exc, "details", None)})
    receipt["episodes"] = episodes
    receipt["artifact_sha256"] = {str(p.relative_to(args.out)): digest(p.read_bytes()) for p in sorted(args.out.rglob("*")) if p.is_file()}
    write_json(args.out / "receipt.json", receipt)
    print(json.dumps({"out": str(args.out), "episodes": len(episodes), "failures": receipt["failures"],
                      "canonical_pairs": receipt.get("canonical_pairs"), "query_rotations": receipt.get("query_rotations")}, sort_keys=True))
    return bool(receipt["failures"])


if __name__ == "__main__":
    raise SystemExit(main())
