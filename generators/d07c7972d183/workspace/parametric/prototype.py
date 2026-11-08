"""Opt-in row-period continuation variants; Racket supplies every exported label.

This module does not change the canonical generator, rule, approval, or training mix.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from functools import lru_cache
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[4]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import load_selected_generator, public_challenge_bytes, public_challenge_id

TASK_ID = "d07c7972d183"
DEFAULT = {"extension_divisor": 2, "output_color": 2}
PARAMETERS = {"extension_divisor": (2, 3), "output_color": (2, 3)}
SETTINGS = tuple(dict(zip(PARAMETERS, values))
                 for values in itertools.product(*PARAMETERS.values()))
DEMO_LIMITS = (2, 8)
QUERY_LIMITS = (1, 8)
MAX_CANDIDATES = 256
GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != set(PARAMETERS):
        raise ValueError("settings must name exactly extension_divisor and output_color")
    for key, options in PARAMETERS.items():
        value = settings[key]
        if type(value) is not int or value not in options:
            raise ValueError(f"{key} must be an exact integer in {options}")
    return dict(settings)


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid requires rectangular 1..30 dimensions and exact integer colors 0..9")
    return grid


def _input(grid):
    _grid(grid)
    errors = GENERATOR.self_check(grid)
    if errors:
        raise ValueError("input outside the unchanged canonical grammar: " + "; ".join(errors))
    return grid


@lru_cache(maxsize=1)
def canonical_record():
    records = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                records.append(row)
    if len(records) != 1:
        raise ValueError("prototype requires one unambiguous canonical authority row")
    return records[0]


def _replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("canonical template drift: expected exactly one " + repr(old))
    return source.replace(old, new, 1)


def program(settings):
    """Return the exact selected program; the original setting is byte-identical."""
    setting = _settings(settings)
    source = canonical_record()["program_solution"]
    source = _replace_once(source, "(/ h 2)", f"(/ h {setting['extension_divisor']})")
    return _replace_once(source, "(if (= v 1) 2 v)",
                         f"(if (= v 1) {setting['output_color']} v)")


def diagnostic_output(grid, settings):
    """Python comparison only. Generation and writer labels always execute Racket."""
    setting = _settings(settings)
    _input(grid)
    height = len(grid)
    period = next(p for p in range(1, height + 1)
                  if all(grid[r] == grid[r % p] for r in range(height)))
    return [[setting["output_color"] if cell == 1 else cell for cell in grid[r % period]]
            for r in range(height + height // setting["extension_divisor"])]


def rival_programs(settings):
    """Seven total, parameter-aware shortcut programs; never label authorities."""
    setting = _settings(settings)
    divisor, color = setting["extension_divisor"], setting["output_color"]
    source = program(setting)
    start = source.index("(period ")
    end = source.index("\n                (new-h", start)
    binding = source[start:end]
    output_height = f"(new-h (+ h (floor (/ h {divisor}))))"
    recolor = f"(if (= v 1) {color} v)"
    columnwise = f"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (new-h (+ h (floor (/ h {divisor})))))
    (grid-from-fn new-h w
      (lambda (r c)
        (let* ((period (find-first
                         (lambda (p)
                           (for/and ((i (range 0 h)))
                             (= (at g i c) (at g (mod i p) c))))
                         (range 1 (+ h 1))))
               (v (at g (mod r period) c)))
          (if (= v 1) {color} v)))))))"""
    return {
        "corner_zero": _replace_once(source, recolor,
            f"(if (and (= r 0) (= c 0)) 0 {recolor})"),
        "first_recurrence": _replace_once(source, binding,
            "(period (or (find-first (lambda (p) (= (row-at g p) (row-at g 0))) "
            "(range 1 h)) h))"),
        "columnwise": columnwise,
        "fixed_nine": _replace_once(source, output_height, "(new-h 9)"),
        "add_three": _replace_once(source, output_height, "(new-h (+ h 3))"),
        "ceiling_extension": _replace_once(source, f"(floor (/ h {divisor}))",
                                           f"(quotient (+ h {divisor - 1}) {divisor})"),
        "repeat_input": _replace_once(source, binding, "(period h)"),
    }


class RacketRunner:
    """One live protected bridge; each apply executes its exact wrapped source."""
    def __init__(self):
        self.bridge = RacketBridge()
        try:
            identity = self.bridge.runtime_identity
            if identity.get("protected") is not True:
                raise ValueError("a live protected Racket runtime is required")
            keys = ("schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                    "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256")
            self.identity = {key: identity[key] for key in keys}
        except BaseException:
            self.bridge.close()
            raise
        self.evaluations = 0
        self._wrapped = {}

    def apply(self, source, grid):
        _grid(grid)
        if type(source) is not str or not source.strip():
            raise ValueError("program must be nonempty Racket source")
        if source not in self._wrapped:
            self._wrapped[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        output = self.bridge.eval_text(f"({self._wrapped[source]} {literal})")
        self.evaluations += 1
        return copy.deepcopy(_grid(output))

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def source_hashes():
    """Bind the authoring code and its relevant same-checkout dependencies."""
    paths = [
        Path(__file__), GENERATOR_PATH,
        ROOT / "shared/data/canonical/puzzles.jsonl",
        RUNTIME / "reviewer_support.py",
        RUNTIME / "puzzle_generators/rule_wrap.py",
        RUNTIME / "arc_repl/racket_bridge.py",
    ]
    for name in ("adapter.py", "promotion.json"):
        optional = Path(__file__).parent / name
        if optional.is_file():
            paths.append(optional)
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()) for path in sorted(paths)}


def sample_inputs(input_seed, demos, queries):
    """Two teaching inputs, then canonical input draws, with bounded deduplication."""
    _integer(input_seed, 0, 2**63 - 1, "input_seed")
    _integer(demos, *DEMO_LIMITS, "demos")
    _integer(queries, *QUERY_LIMITS, "queries")
    selected, seen, draws = [], set(), []
    duplicates = 0

    def consider(grid, index, role):
        nonlocal duplicates
        _input(grid)
        key = _json_bytes(grid)
        if key in seen:
            duplicates += 1
            return
        seen.add(key)
        selected.append(grid)
        draws.append({"sample_index": index, "profile": role, "input_sha256": sha256(key)})

    consider(GENERATOR.generate(input_seed, 1, difficulty="medium"), 1, "period_witness_h9")
    consider(GENERATOR.generate(input_seed, 2, difficulty="medium",
                               grid_h=7, grid_w=3 + input_seed % 10, period=4),
             2, "extent_witness_h7")
    attempts = 0
    for index in range(MAX_CANDIDATES):
        if len(selected) == demos + queries:
            break
        attempts += 1
        consider(GENERATOR.generate(input_seed, index, difficulty="medium"), index, "canonical_sampler")
    if len(selected) != demos + queries:
        raise ValueError(f"sampling exhausted after {MAX_CANDIDATES} additional candidates: "
                         f"needed {demos + queries} distinct inputs, found {len(selected)}")
    return selected, {"additional_candidate_limit": MAX_CANDIDATES,
                      "candidates_drawn": attempts + 2, "duplicate_rejections": duplicates,
                      "accepted": draws}


def lesson_certificate(train, query_inputs, settings, runner):
    """Fit programs to demonstrations only, then compare surviving query predictions.

    This interface accepts query inputs, never query labels. A failed alternative
    execution raises; it cannot count as a rejected interpretation.
    """
    setting = _settings(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("certificate needs nonempty demonstrations and query inputs")
    for pair in train:
        _input(pair["input"])
        _grid(pair["output"])
    for grid in query_inputs:
        _input(grid)
    chosen = program(setting)
    if any(runner.apply(chosen, pair["input"]) != pair["output"] for pair in train):
        raise ValueError("demonstration label disagrees with matching Racket")

    survivors, rejected = [], []
    for candidate in SETTINGS:
        source = program(candidate)
        disagreements = [i for i, pair in enumerate(train)
                         if runner.apply(source, pair["input"]) != pair["output"]]
        if disagreements:
            rejected.append({"settings": dict(candidate), "demo_indices": disagreements})
        else:
            survivors.append(dict(candidate))
    shortcut_rejections = {}
    for name, source in rival_programs(setting).items():
        shortcut_rejections[name] = [
            i for i, pair in enumerate(train)
            if runner.apply(source, pair["input"]) != pair["output"]
        ]
    surviving_shortcuts = [name for name, indices in shortcut_rejections.items() if not indices]
    if survivors != [setting] or surviving_shortcuts:
        raise ValueError(f"demonstrations leave unsupported ambiguity: settings={survivors}, "
                         f"shortcuts={surviving_shortcuts}")

    # With one setting and no surviving shortcut, the surviving interpretation
    # is unique within this declared family. Still materialize every query's
    # independently executed prediction and bind it to its input.
    query_checks = []
    for index, grid in enumerate(query_inputs):
        prediction = runner.apply(chosen, grid)
        query_checks.append({"query_index": index, "input_sha256": sha256(_json_bytes(grid)),
                             "prediction_sha256": sha256(_json_bytes(prediction)),
                             "all_survivors_agree": True, "surviving_programs": 1})
    return {"schema": "row-period-lesson-certificate-v1", "basis": "demonstrations_only",
            "lawful_settings_checked": len(SETTINGS), "shortcut_rules_checked": 7,
            "surviving_settings": survivors, "setting_rejections": rejected,
            "surviving_shortcuts": surviving_shortcuts,
            "shortcut_rejections": shortcut_rejections, "queries": query_checks}


def generate_episode(seed, *, settings=None, input_seed=None, demos=3, queries=4, runner=None):
    """Generate one fixed-setting episode with independent, exact split counts."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, *DEMO_LIMITS, "demos")
    _integer(queries, *QUERY_LIMITS, "queries")
    chosen = _settings(settings) if settings is not None else dict(random.Random(seed).choice(SETTINGS))
    input_seed = seed if input_seed is None else _integer(input_seed, 0, 2**63 - 1, "input_seed")
    if runner is None:
        with RacketRunner() as live:
            return generate_episode(seed, settings=chosen, input_seed=input_seed,
                                    demos=demos, queries=queries, runner=live)
    inputs, sampling = sample_inputs(input_seed, demos, queries)
    source = program(chosen)
    pairs = [{"input": grid, "output": runner.apply(source, grid)} for grid in inputs]
    episode = {"schema": "row-period-parametric-episode-v1", "status": "proposed_prototype",
               "task_id": TASK_ID, "seed": seed, "input_seed": input_seed, "settings": chosen,
               "train": pairs[:demos], "test": pairs[demos:], "sampling": sampling,
               "program_solution": source, "program_sha256": sha256(source.encode()),
               "source_hashes": source_hashes(), "racket_runtime": runner.identity}
    episode["certificate"] = lesson_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], chosen, runner)
    return episode


def _verify_episode(episode, runner):
    if type(episode) is not dict or episode.get("task_id") != TASK_ID:
        raise ValueError("episode must belong to the selected task")
    _integer(episode.get("seed"), 0, 2**63 - 1, "seed")
    _integer(episode.get("input_seed"), 0, 2**63 - 1, "input_seed")
    setting = _settings(episode.get("settings"))
    source = program(setting)
    if (episode.get("program_solution") != source
            or episode.get("program_sha256") != sha256(source.encode())):
        raise ValueError("private program or hash differs from the exact setting program")
    if episode.get("source_hashes") != source_hashes():
        raise ValueError("private source hashes are stale")
    if episode.get("racket_runtime") != runner.identity:
        raise ValueError("private runtime identity is stale")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode requires train/test lists")
    _integer(len(train), *DEMO_LIMITS, "demos")
    _integer(len(test), *QUERY_LIMITS, "queries")
    keys = set()
    for split, pairs in (("demonstration", train), ("query", test)):
        for index, pair in enumerate(pairs):
            _input(pair["input"])
            _grid(pair["output"])
            key = _json_bytes(pair["input"])
            if key in keys:
                raise ValueError("all demonstration and query inputs must be distinct")
            keys.add(key)
            if runner.apply(source, pair["input"]) != pair["output"]:
                raise ValueError(f"{split} {index} label disagrees with matching Racket")
    certificate = lesson_certificate(train, [pair["input"] for pair in test], setting, runner)
    if episode.get("certificate") != certificate:
        raise ValueError("private demonstration-only certificate is stale")
    return copy.deepcopy(episode)


def write_export(episodes, destination, *, runner=None, command=None):
    """Validate private records with Racket; publish exact visible bytes once each."""
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"refusing existing destination: {destination}")
    if type(episodes) is not list or not episodes:
        raise ValueError("export needs a nonempty list of episodes")
    indexed = {}
    for episode in episodes:
        identifier = public_challenge_id(episode)
        if identifier in indexed:
            raise ValueError("duplicate public challenge in batch")
        indexed[identifier] = episode
    if runner is None:
        with RacketRunner() as live:
            return write_export(episodes, destination, runner=live, command=command)
    verified = [(identifier, _verify_episode(indexed[identifier], runner))
                for identifier in sorted(indexed)]

    # Complete every JSON serialization before creating the destination.
    # This includes arbitrary private metadata and the optional command receipt.
    public_rows, private_rows, payloads = [], [], {}
    for identifier, episode in verified:
        visible = public_challenge_bytes(episode)
        public_rows.append(visible)
        payloads[f"public/{identifier}.json"] = visible
        private_rows.append(_json_bytes(dict(episode, public_id=identifier)))
        payloads[f"private/programs/{episode['program_sha256']}.rkt"] = episode["program_solution"].encode()
    payloads["public.jsonl"] = b"".join(public_rows)
    payloads["private.jsonl"] = b"".join(private_rows)
    manifest = {
        "schema": "row-period-parametric-export-v1", "status": "proposed_prototype",
        "episodes": len(verified), "demonstration_pairs": sum(len(ep["train"]) for _, ep in verified),
        "query_pairs": sum(len(ep["test"]) for _, ep in verified),
        "public_ids": [identifier for identifier, _ in verified],
        "source_hashes": source_hashes(), "racket_runtime": runner.identity,
        "racket_evaluations_in_runner": runner.evaluations,
        "command": command, "files": {name: sha256(data) for name, data in payloads.items()},
        "limits": {"demos": list(DEMO_LIMITS), "queries": list(QUERY_LIMITS),
                   "additional_input_candidates": MAX_CANDIDATES},
        "scope": "bounded authoring evidence; no promotion, approval, or training admission",
    }
    manifest_bytes = _json_bytes(manifest)
    # Existing directories are never overwritten. The manifest is the final
    # write, so an OS-level write failure cannot leave a completed manifest.
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "public").mkdir()
    (destination / "private" / "programs").mkdir(parents=True)
    for name, data in payloads.items():
        (destination / name).write_bytes(data)
    (destination / "manifest.json").write_bytes(manifest_bytes)
    return manifest


def _settings_json(raw):
    try:
        return _settings(json.loads(raw))
    except (ValueError, TypeError) as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--input-seed", type=int)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--settings", type=_settings_json, help="exact JSON parameter object")
    group.add_argument("--all-settings", action="store_true", help="paired inputs under all four rules")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    choices = list(SETTINGS) if args.all_settings else [args.settings]
    with RacketRunner() as runner:
        episodes = [generate_episode(args.seed, settings=setting, input_seed=args.input_seed,
                                     demos=args.demos, queries=args.queries, runner=runner)
                    for setting in choices]
        manifest = write_export(episodes, args.out, runner=runner,
                                command=["python", str(Path(__file__).relative_to(ROOT)),
                                         *(sys.argv[1:] if argv is None else argv)])
    print(json.dumps({"status": manifest["status"], "episodes": manifest["episodes"],
                      "demonstration_pairs": manifest["demonstration_pairs"],
                      "query_pairs": manifest["query_pairs"], "public_ids": manifest["public_ids"],
                      "racket_evaluations": manifest["racket_evaluations_in_runner"],
                      "manifest": str(args.out / "manifest.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

