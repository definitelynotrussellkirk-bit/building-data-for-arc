"""Task-local proposed tie-policy episodes; never a production generator API."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from itertools import product
import json
import random
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parent.parent
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
RUNTIME_ROOT = ROOT if (ROOT / "RUNTIME_MANIFEST.json").is_file() else ROOT / "shared/runtime"
TASK_ID = "77e3acd21c5d"
VERSION = "1.0.0-native"
VALUES = ("both", "low", "high")
DEMO_MODES = ("row_tie", "col_tie", "corner", "both_tie", "clipped")
PROFILES = ("compact4", "stack3", "wide4", "large6")
sys.path.insert(0, str(RUNTIME_ROOT))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, load_selected_generator


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def object_sha256(value) -> str:
    return text_sha256(json.dumps(value, sort_keys=True, separators=(",", ":")))


@dataclass(frozen=True)
class Parameters:
    row_ties: str = "both"
    column_ties: str = "both"

    def __post_init__(self):
        for name, value in self.as_dict().items():
            if type(value) is not str:
                raise TypeError(f"{name} must be a string")
            if value not in VALUES:
                raise ValueError(f"{name} must be one of {VALUES}; got {value!r}")

    def as_dict(self) -> dict:
        return {"row_ties": self.row_ties, "column_ties": self.column_ties}

    @property
    def key(self) -> str:
        return f"rows-{self.row_ties}_columns-{self.column_ties}"


DEFAULT = Parameters()
ALL_PARAMETERS = tuple(Parameters(*values) for values in product(VALUES, repeat=2))


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a Python integer, not a Boolean or coercible value")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _derived_seed(seed: int, namespace: str) -> int:
    return int(text_sha256(f"{TASK_ID}:{VERSION}:{namespace}:{seed}"), 16) % (2**63)


def choose_parameters(seed: int) -> Parameters:
    """Select one immutable rule setting for the whole episode."""
    _validate_seed(seed)
    return ALL_PARAMETERS[_derived_seed(seed, "rule") % len(ALL_PARAMETERS)]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = set()
    path = canonical_path(ROOT)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if TASK_ID not in line:
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one unique canonical program for {TASK_ID}; found {len(programs)}")
    return programs.pop()


def materialize_rule(parameters: Parameters = DEFAULT) -> str:
    """Keep exact canonical bytes except for the two selected tie branches.

    low/high identify source edges (top/bottom or left/right), not a numeric
    sorting of destination coordinates. Clipping happens after both choices.
    """
    if not isinstance(parameters, Parameters):
        raise TypeError("parameters must be Parameters")
    source = canonical_program()
    clauses = (
        ("(else (list mr (- eh 1 bot)))", parameters.row_ties, "mr", "(- eh 1 bot)"),
        ("(else (list mc (- ew 1 right)))", parameters.column_ties, "mc", "(- ew 1 right)"),
    )
    for original, value, low, high in clauses:
        if source.count(original) != 1:
            raise ValueError("canonical tie-clause shape changed; re-review the prototype")
        if value != "both":
            source = source.replace(original, f"(else (list {low if value == 'low' else high}))")
    return source


@lru_cache(maxsize=1)
def _generator_record():
    return load_selected_generator(TASK_ID, root=ROOT)


def generator():
    module, path, loaded_hash = _generator_record()
    if hashlib.sha256(path.read_bytes()).hexdigest() != loaded_hash:
        raise RuntimeError("canonical generator changed during this process; start a fresh probe")
    return module


def source_hashes() -> dict[str, str]:
    """Hash the local implementation, input sampler and direct runtime helpers."""
    generator()
    paths = list(HERE.glob("*.py")) + list((TASK_HOME / "tests").glob("test_parametric_*.py"))
    if (HERE / "README.md").exists():
        paths.append(HERE / "README.md")
    paths.append(TASK_HOME / "workspace/reference_probe.py")
    hashes = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(set(paths))
    }
    _, selected_path, selected_sha256 = _generator_record()
    hashes[f"generators/{TASK_ID}/generator.py"] = selected_sha256
    for relative in (
        "puzzle_generators/base.py", "puzzle_generators/helpers/grid.py",
        "puzzle_generators/rule_wrap.py", "arc_repl/racket_bridge.py", "reviewer_support.py",
    ):
        hashes[f"shared/runtime/{relative}"] = hashlib.sha256((RUNTIME_ROOT / relative).read_bytes()).hexdigest()
    return dict(sorted(hashes.items()))


DEMONSTRATION_SPECS = (
    ("teaching", "both_tie", "hard"),
    ("large6", "row_tie", "hard"),
    ("compact4", "col_tie", "medium"),
    ("stack3", "corner", "medium"),
    ("large6", "clipped", "hard"),
    ("compact4", "both_tie", "easy"),
)
QUERY_SPECS = (
    ("wide4", "both_tie", "medium"),
    ("stack3", "row_tie", "hard"),
    ("large6", "col_tie", "hard"),
    ("stress30", "both_tie", "hard"),
)


def _validate_counts(demo_count: int, query_count: int) -> tuple[int, int]:
    if type(demo_count) is not int:
        raise TypeError("demo_count must be a literal integer")
    if type(query_count) is not int:
        raise TypeError("query_count must be a literal integer")
    if not 2 <= demo_count <= 6:
        raise ValueError("demo_count must be in 2..6")
    if not 1 <= query_count <= 4:
        raise ValueError("query_count must be in 1..4")
    return demo_count, query_count


def _axis_landings(value: int, source_size: int, output_size: int, policy: str) -> tuple[int, ...]:
    opposite = source_size - 1 - value
    if value < opposite:
        return (value,)
    if value > opposite:
        return (output_size - 1 - opposite,)
    if policy == "both":
        return (value, output_size - 1 - opposite)
    if policy == "low":
        return (value,)
    if policy == "high":
        return (output_size - 1 - opposite,)
    raise ValueError(f"unknown tie policy {policy!r}")


def python_mirror(grid, parameters: Parameters = DEFAULT) -> list[list[int]]:
    """Pure mirror of the selected native Racket rule for adapter claims."""
    if not isinstance(parameters, Parameters):
        raise TypeError("parameters must be Parameters")
    sampler = generator()
    facts = sampler._require_scene(grid)
    blank = facts["blank"]
    source = facts["source"]
    blank_color = next(iter(blank["colors"]))
    _body_color, marker_color, offsets = sampler._component_marker_facts(grid, source)
    output = [[blank_color for _ in range(blank["w"])] for _ in range(blank["h"])]
    for marker_row, marker_col in offsets:
        rows = _axis_landings(marker_row, source["h"], blank["h"], parameters.row_ties)
        columns = _axis_landings(marker_col, source["w"], blank["w"], parameters.column_ties)
        for row in rows:
            for column in columns:
                if 0 <= row < blank["h"] and 0 <= column < blank["w"]:
                    output[row][column] = marker_color
    return output


def _paint_rectangle(grid, slot, body_color: int, marker_color: int | None, markers=()) -> None:
    top, left, height, width = slot
    for row in range(top, top + height):
        for column in range(left, left + width):
            grid[row][column] = body_color
    if marker_color is not None:
        for row, column in markers:
            grid[top + row][left + column] = marker_color


def _teaching_scene(seed: int) -> list[list[int]]:
    """Construct a seed-stable two-demo curriculum anchor.

    The unique widest marker rectangle is deliberately neither the first
    marker rectangle nor the largest-area marker rectangle. Its central
    marker is tied on both axes, so one scene distinguishes all nine tie
    policies and also rejects the diagonal-zip shortcut.
    """
    rng = random.Random(_derived_seed(seed, "teaching"))
    palette = list(range(10))
    rng.shuffle(palette)
    background, marker_color, distractor_body, source_body, blank_body = palette[:5]
    grid = [[background] * 22 for _ in range(20)]

    # First and largest-area multicolor component: a deliberate distractor.
    _paint_rectangle(
        grid,
        (1, 1, 12, 7),
        distractor_body,
        marker_color,
        ((1, 1), (10, 5)),
    )
    # Unique widest component: the true source. The centre marker teaches
    # row ties, column ties, and their Cartesian product in one example.
    _paint_rectangle(
        grid,
        (1, 10, 7, 11),
        source_body,
        marker_color,
        generator()._source_markers("both_tie", 7, 11),
    )
    _paint_rectangle(grid, (14, 10, 5, 9), blank_body, None)

    sampler = generator()
    errors = sampler.self_check(grid)
    if errors:
        raise AssertionError("invalid teaching scene: " + "; ".join(errors))
    facts = sampler._require_scene(grid)
    first = facts["markers"][0]
    largest = max(facts["markers"], key=lambda item: item["h"] * item["w"])
    if facts["source"] is first or facts["source"] is largest:
        raise AssertionError("teaching scene no longer separates source-selection shortcuts")
    return grid


def _stress30(seed: int) -> list[list[int]]:
    """A dense lawful 30x30 scene spread to every inner boundary."""
    rng = random.Random(_derived_seed(seed, "stress30"))
    palette = list(range(10))
    rng.shuffle(palette)
    background, marker_color = palette[:2]
    body_colors = palette[2:8]
    slots = (
        (1, 1, 9, 15),       # unique widest source
        (1, 18, 11, 11),     # monochrome output canvas
        (13, 1, 16, 7),
        (14, 10, 7, 9),
        (14, 22, 6, 7),
        (23, 11, 6, 11),
    )
    grid = [[background] * 30 for _ in range(30)]
    sampler = generator()
    _paint_rectangle(
        grid, slots[0], body_colors[0], marker_color,
        sampler._source_markers("both_tie", slots[0][2], slots[0][3]),
    )
    _paint_rectangle(grid, slots[1], body_colors[1], None)
    distractor_modes = ("row_tie", "col_tie", "corner", "both_tie")
    for index, (slot, mode) in enumerate(zip(slots[2:], distractor_modes), start=2):
        _paint_rectangle(
            grid, slot, body_colors[index], marker_color,
            sampler._source_markers(mode, slot[2], slot[3]),
        )
    errors = sampler.self_check(grid)
    if errors:
        raise AssertionError("invalid 30x30 stress scene: " + "; ".join(errors))
    return grid


def _build_input_pool(seed: int) -> tuple[list, list, list[dict]]:
    """Return six teaching inputs and four count-neutral novel queries."""
    _validate_seed(seed)
    sampler = generator()
    rejection_log = []
    for attempt in range(32):
        input_seed = _derived_seed(seed, f"native-inputs:{attempt}")
        demonstrations = []
        queries = []
        draws = []
        for index, (profile, mode, difficulty) in enumerate(DEMONSTRATION_SPECS):
            if profile == "teaching":
                grid = _teaching_scene(input_seed)
            else:
                grid = sampler.generate(
                    input_seed, attempt * 100 + index, difficulty=difficulty,
                    profile=profile, marker_mode=mode,
                )
            demonstrations.append(grid)
            draws.append({"split": "train", "index": index, "profile": profile,
                          "marker_mode": mode, "difficulty": difficulty})
        for offset, (profile, mode, difficulty) in enumerate(QUERY_SPECS):
            index = len(DEMONSTRATION_SPECS) + offset
            if profile == "stress30":
                grid = _stress30(input_seed)
            else:
                grid = sampler.generate(
                    input_seed, attempt * 100 + index, difficulty=difficulty,
                    profile=profile, marker_mode=mode,
                )
            queries.append(grid)
            draws.append({"split": "test", "index": offset, "profile": profile,
                          "marker_mode": mode, "difficulty": difficulty})
        all_inputs = demonstrations + queries
        keys = [object_sha256(grid) for grid in all_inputs]
        signatures = {
            tuple(object_sha256(python_mirror(grid, parameters)) for grid in demonstrations[:2])
            for parameters in ALL_PARAMETERS
        }
        query_variation = [
            len({object_sha256(python_mirror(grid, parameters)) for parameters in ALL_PARAMETERS})
            for grid in queries
        ]
        if len(set(keys)) == len(keys) and len(signatures) == len(ALL_PARAMETERS) and min(query_variation) >= 2:
            return demonstrations, queries, draws
        rejection_log.append({
            "attempt": attempt,
            "unique_inputs": len(set(keys)),
            "teaching_signatures": len(signatures),
            "query_variation": query_variation,
        })
    raise RuntimeError(f"could not construct a robust native input pool: {rejection_log}")


def sample_inputs(seed: int, *, demo_count: int, query_count: int) -> dict:
    demo_count, query_count = _validate_counts(demo_count, query_count)
    demonstrations, queries, draws = _build_input_pool(seed)
    return {
        "demonstrations": deepcopy(demonstrations[:demo_count]),
        "queries": deepcopy(queries[:query_count]),
        "draws": deepcopy(draws),
    }


def public_challenge(episode: dict, *, revealed_queries: int = 1) -> dict:
    if type(revealed_queries) is not int or not 1 <= revealed_queries <= len(episode.get("test", [])):
        raise ValueError("revealed_queries must be a literal integer within the available query count")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"][:revealed_queries]
        ],
    }


class RacketRules:
    """One real included Racket bridge, with all nine exact programs installed."""

    def __init__(self):
        self.programs = {p.key: materialize_rule(p) for p in ALL_PARAMETERS}
        self.bridge = RacketBridge()
        self.calls = 0
        self.names = {}
        try:
            for index, parameters in enumerate(ALL_PARAMETERS):
                name = f"__parametric_{index}"
                # This authority is already a complete native Racket lambda,
                # with no shorthand, dict literals or free h/w variables.
                # Use the shared normalizers needed for this exact source.
                body = strip_rule_wrapper(strip_line_comments(self.programs[parameters.key]))
                if not body.startswith("(lambda (g)"):
                    raise ValueError("the authority is no longer the reviewed native lambda")
                self.bridge.eval_text(f"(define {name} {body})")
                self.names[parameters.key] = name
            self.runtime_identity = self.bridge.runtime_identity
        except BaseException:
            self.bridge.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.bridge.close()

    def outputs(self, parameters: Parameters, grids: list) -> list:
        result = []
        for grid in grids:
            self.bridge.define_grid("__parametric_input", grid)
            result.append(self.bridge.eval_text(f"({self.names[parameters.key]} __parametric_input)"))
            self.calls += 1
        return result

    def matrix(self, grids: list) -> dict[str, list]:
        return {p.key: self.outputs(p, grids) for p in ALL_PARAMETERS}


def score_rivals(matrix: dict[str, list], selected: Parameters, *, n_train: int) -> dict:
    """Measure only the nine declared settings; preserve ambiguous survivors."""
    truth = matrix[selected.key]
    if not 1 <= n_train < len(truth):
        raise ValueError("need at least one demonstration and one query")
    result = {}
    for parameters in ALL_PARAMETERS:
        outputs = matrix[parameters.key]
        if len(outputs) != len(truth):
            raise ValueError("rival output matrix has inconsistent lengths")
        matches = [actual == expected for actual, expected in zip(outputs, truth)]
        refuting = next((i for i, equal in enumerate(matches[:n_train]) if not equal), None)
        if parameters == selected:
            status = "selected"
        elif refuting is not None:
            status = "eliminated"
        elif all(matches[n_train:]):
            status = "survived_agree"
        else:
            status = "ambiguous"
        result[parameters.key] = {
            "parameters": parameters.as_dict(),
            "program_sha256": text_sha256(materialize_rule(parameters)),
            "status": status,
            "demo_matches": matches[:n_train],
            "query_matches": matches[n_train:],
            "first_refuting_demo": refuting,
            "first_refuting_output": None if refuting is None else outputs[refuting],
            "output_sha256": [object_sha256(output) for output in outputs],
        }
    return result


def generate_episode(seed: int, *, parameters: Parameters | None = None, rules: RacketRules | None = None) -> dict:
    """Five demonstrations and one query, with all nine rivals checked in Racket.

    Rule selection happens once, before any pair. Input draws use a separate
    deterministic seed and acceptance requires pairwise demo separation for ALL
    settings, so explicit parameter overrides cannot influence input draws.
    """
    _validate_seed(seed)
    if rules is None:
        with RacketRules() as owned:
            return generate_episode(seed, parameters=parameters, rules=owned)
    selected = choose_parameters(seed) if parameters is None else parameters
    if not isinstance(selected, Parameters):
        raise TypeError("parameters must be Parameters or None")
    sources = source_hashes()
    calls_before = rules.calls
    input_seed = _derived_seed(seed, "inputs")
    sampler = generator()
    modes = DEMO_MODES + ("both_tie",)
    rejections = []
    for attempt in range(16):
        indices = [attempt * len(modes) + i for i in range(len(modes))]
        draws = []
        inputs = []
        for index, mode in zip(indices, modes):
            profile = PROFILES[(input_seed + index) % len(PROFILES)]
            grid = sampler.generate(input_seed, index, difficulty="medium", profile=profile, marker_mode=mode)
            errors = sampler.self_check(grid)
            if errors:
                raise ValueError(f"canonical input sampler failed self_check at {index}: {errors}")
            inputs.append(grid)
            draws.append({"sample_index": index, "profile": profile, "marker_mode": mode})
        matrix = rules.matrix(inputs)
        signatures = {object_sha256(matrix[p.key][:len(DEMO_MODES)]) for p in ALL_PARAMETERS}
        if len(signatures) == len(ALL_PARAMETERS):
            break
        rejections.append({"attempt": attempt, "reason": "demonstrations do not separate all nine declared settings", "distinct_demo_signatures": len(signatures)})
    else:
        raise ValueError(f"no fully distinguished episode after 16 attempts: {rejections}")
    labels = matrix[selected.key]
    pairs = [{"input": deepcopy(grid), "output": deepcopy(output)} for grid, output in zip(inputs, labels)]
    public = {
        "train": deepcopy(pairs[:len(DEMO_MODES)]),
        "test": [{"input": deepcopy(pair["input"])} for pair in pairs[len(DEMO_MODES):]],
    }
    rivals = score_rivals(matrix, selected, n_train=len(DEMO_MODES))
    if source_hashes() != sources:
        raise RuntimeError("prototype or dependencies changed during generation; start a fresh probe")
    private = {
        "schema": "arc-parametric-prototype-episode-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "input_seed": input_seed,
        "parameters": selected.as_dict(),
        "parameter_selection": "seeded" if parameters is None else "explicit_override",
        "rule_choice": "selected once before all demonstrations and queries",
        "program": rules.programs[selected.key],
        "program_sha256": text_sha256(rules.programs[selected.key]),
        "canonical_program_sha256": text_sha256(canonical_program()),
        "source_sha256": sources,
        "runtime_identity": deepcopy(rules.runtime_identity),
        "label_backend": "racket",
        "label_applications": rules.calls - calls_before,
        "train": pairs[:len(DEMO_MODES)],
        "test": pairs[len(DEMO_MODES):],
        "draws": draws,
        "input_sha256": [object_sha256(grid) for grid in inputs],
        "output_sha256": [object_sha256(output) for output in labels],
        "public_sha256": object_sha256(public),
        "rivals": rivals,
        "rejections": rejections,
        "limitations": "Finite evidence against these nine settings only; no universal identifiability or production approval claim.",
    }
    return {"public": public, "private": private}
