#!/usr/bin/env python3
"""Task-local, unapproved nearest/farthest rule prototype; labels execute Racket."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "9971f3a5882c"
VERSION = "prototype-1"
SETTINGS = ("nearest", "farthest")
DEFAULT_SETTING = "nearest"
SCHEMA = "9971f3a5882c-parametric-episode-v1"
HERE = Path(__file__).resolve().parent
PARAMETER_SPEC = {
    "name": "marker_selection",
    "allowed_values": list(SETTINGS),
    "canonical_default": DEFAULT_SETTING,
    "meaning": "Choose the nearest or farthest exterior marker independently on each occupied side.",
    "selection": "One SHA-256-derived setting per episode seed; an explicit setting overrides that one draw.",
    "input_constraints": "Both settings use the selected generator's unchanged sparse-lattice input grammar.",
    "teaching_constraint": "A demonstration must distinguish the settings before a query needs the distinction.",
}
PROFILES = {
    "teaching": ("top_double_right", "top_double_left", "all_sides", "double_left_bottom"),
    "ambiguous_diagnostic": ("left_bottom", "right_bottom", "all_sides", "double_left_bottom"),
    "equivalent_control": ("left_bottom", "right_bottom", "all_sides", "top_bottom"),
}
SUBSTITUTIONS = (
    ("(max-of fst above)", "(min-of fst above)"),
    ("(min-of fst below)", "(max-of fst below)"),
    ("(max-of snd lefts)", "(min-of snd lefts)"),
    ("(min-of snd rights)", "(max-of snd rights)"),
)


def digest(value):
    """Hash JSON data with stable key and whitespace conventions."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def python_solution(grid, marker_selection=DEFAULT_SETTING):
    """Independent mirror for parity checks; never used to label an episode."""
    if marker_selection not in SETTINGS:
        raise ValueError("marker_selection must be 'nearest' or 'farthest'")
    height, width = len(grid), len(grid[0])
    cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 3]
    marks = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 6]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    above = [r for r, c in marks if r < r0 and c0 <= c <= c1]
    below = [r for r, c in marks if r > r1 and c0 <= c <= c1]
    left = [c for _, c in marks if c < c0]
    right = [c for _, c in marks if c > c1]
    low, high = (max, min) if marker_selection == "nearest" else (min, max)
    nr0 = low(above) + 1 if above else r0
    nr1 = high(below) - 1 if below else r1
    nc0 = low(left) + 1 if left else c0
    nc1 = high(right) - 1 if right else c1
    full_rows = [r for r in range(r0, r1 + 1) if all(grid[r][c] == 3 for c in range(c0, c1 + 1))]
    full_cols = [c for c in range(c0, c1 + 1) if all(grid[r][c] == 3 for r in range(r0, r1 + 1))]
    result = [[0] * width for _ in range(height)]
    for r in full_rows:
        mapped = nr0 if r == r0 else nr1 if r == r1 else r
        for c in range(nc0, nc1 + 1):
            result[mapped][c] = 3
    for c in full_cols:
        mapped = nc0 if c == c0 else nc1 if c == c1 else c
        for r in range(nr0, nr1 + 1):
            result[r][mapped] = 3
    for r, c in marks:
        result[r][c] = 6
    return result


class Prototype:
    """Materialize and audit small episodes using one included Racket bridge."""

    def __init__(self, *, root=None):
        self.root = find_root(__file__) if root is None else Path(root).resolve()
        self.generator, self.generator_path, self.generator_sha256 = load_selected_generator(TASK_ID, root=self.root)
        self.canonical_program = (HERE / "nearest.rkt").read_text(encoding="utf-8")
        canonical_rows = []
        with canonical_path(self.root).open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    canonical_rows.append(row)
        if not canonical_rows or any(row.get("program_solution") != self.canonical_program for row in canonical_rows):
            raise ValueError("prototype default reference differs from a selected canonical authority")
        normalized = text_digest(" ".join(self.canonical_program.split()))[:12]
        if normalized != self.generator.RULE_HASH:
            raise ValueError("prototype canonical reference hash differs from selected generator")
        self.canonical_rows_sha256 = digest(canonical_rows)
        alternative = self.canonical_program
        for before, after in SUBSTITUTIONS:
            if alternative.count(before) != 1:
                raise ValueError(f"expected one canonical side expression: {before}")
            alternative = alternative.replace(before, after, 1)
        self.programs = {"nearest": self.canonical_program, "farthest": alternative}
        prefix = f"generators/{TASK_ID}/workspace/parametric"
        bridge_path = Path(sys.modules[RacketBridge.__module__].__file__).resolve()
        self._source_paths = {
            f"generators/{TASK_ID}/generator.py": self.generator_path,
            **{f"{prefix}/{name}": HERE / name for name in ("prototype.py", "nearest.rkt", "README.md")},
            f"generators/{TASK_ID}/tests/test_parametric_extension.py": self.root / "generators" / TASK_ID / "tests/test_parametric_extension.py",
            "shared/runtime/reviewer_support.py": Path(sys.modules[find_root.__module__].__file__),
            "shared/runtime/puzzle_generators/base.py": Path(sys.modules[self.generator.gen_ctx.__module__].__file__),
            "shared/runtime/puzzle_generators/helpers/grid.py": Path(sys.modules[self.generator.full_grid.__module__].__file__),
            "shared/runtime/arc_repl/racket_bridge.py": bridge_path,
        }
        prelude_root = bridge_path.parent / "racket_prelude"
        self._source_paths.update({
            "shared/runtime/arc_repl/racket_prelude/" + path.relative_to(prelude_root).as_posix(): path
            for path in prelude_root.rglob("*.rkt")
        })
        self._source_hashes = {name: file_digest(path) for name, path in self._source_paths.items()}
        self.bridge = None
        self.runtime_identity = None
        self.racket_outputs_executed = 0

    def __enter__(self):
        self.bridge = RacketBridge(timeout=10.0)
        try:
            for setting, code in self.programs.items():
                if not code.startswith("(rule! (lambda (g)") or not code.endswith(")"):
                    raise ValueError("only this task's explicit rule! lambda contract is supported")
                # rule! is the existing ARC command wrapper; its exact lambda
                # body executes through the same bridge and included prelude.
                expression = code[len("(rule! "):-1]
                self.bridge.eval_text(f"(define parametric_{setting} {expression})")
            self.runtime_identity = {
                "racket_version": self.bridge.eval_text("(version)"),
                "racket_binary": str(self.bridge.racket_binary),
                "racket_binary_sha256": file_digest(self.bridge.racket_binary),
                "python_version": sys.version,
            }
        except BaseException:
            self.bridge.shutdown()
            self.bridge = None
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.bridge is not None:
            self.bridge.shutdown()
            self.bridge = None
        return False

    def program(self, marker_selection=DEFAULT_SETTING):
        if not isinstance(marker_selection, str) or marker_selection not in SETTINGS:
            raise ValueError("marker_selection must be 'nearest' or 'farthest'")
        return self.programs[marker_selection]

    @staticmethod
    def select_parameters(seed, marker_selection=None):
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a nonnegative Python int")
        if marker_selection is None:
            key = f"{TASK_ID}:{VERSION}:marker_selection:{seed}".encode("ascii")
            marker_selection = SETTINGS[hashlib.sha256(key).digest()[0] % len(SETTINGS)]
        if not isinstance(marker_selection, str) or marker_selection not in SETTINGS:
            raise ValueError("marker_selection must be 'nearest' or 'farthest'")
        return {"marker_selection": marker_selection}

    def source_bindings(self):
        sources = {name: file_digest(path) for name, path in self._source_paths.items()}
        if sources != self._source_hashes:
            raise ValueError("prototype source binding changed during execution; start a fresh process")
        sources["canonical_selected_rows"] = self.canonical_rows_sha256
        if sources[f"generators/{TASK_ID}/generator.py"] != self.generator_sha256:
            raise ValueError("selected generator changed during prototype execution")
        return sources

    def apply(self, grid, marker_selection=DEFAULT_SETTING):
        self.program(marker_selection)
        errors = self.generator.self_check(grid)
        if errors:
            raise ValueError(f"input is outside the selected sparse-lattice grammar: {errors}")
        if self.bridge is None:
            raise RuntimeError("use 'with Prototype(...) as family' to activate Racket")
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        output = self.bridge.eval_text(f"(parametric_{marker_selection} {literal})")
        self.racket_outputs_executed += 1
        if output != python_solution(grid, marker_selection):
            raise ValueError(f"Python/Racket parity failure for {marker_selection}; input_sha256={digest(grid)}")
        return output

    def make_episode(self, seed, *, marker_selection=None, mode="teaching", difficulty="medium"):
        parameters = self.select_parameters(seed, marker_selection)
        if mode not in PROFILES:
            raise ValueError(f"mode must be one of {tuple(PROFILES)}")
        setting = parameters["marker_selection"]
        pairs, draws = [], []
        # This draw happens once above. Every example keeps exactly that rule;
        # the following per-pair profile/layout draws never choose parameters.
        for index, profile in enumerate(PROFILES[mode]):
            grid = self.generator.generate(seed, index, difficulty=difficulty, marker_profile=profile)
            pairs.append({"input": grid, "output": self.apply(grid, setting)})
            draws.append({"sample_index": index, "marker_profile": profile, "input_sha256": digest(grid)})
        if len({draw["input_sha256"] for draw in draws}) != len(draws):
            raise ValueError("prototype episode contains duplicate inputs")
        episode = {
            "schema": SCHEMA,
            "task_id": TASK_ID,
            "scope": "unapproved_task_local_prototype",
            "seed": seed,
            "mode": mode,
            "difficulty": difficulty,
            "selection_origin": "seed_draw" if marker_selection is None else "explicit",
            "parameters": parameters,
            "source_bindings": self.source_bindings(),
            "reference": {"racket_text": self.program(setting), "sha256": text_digest(self.program(setting))},
            "sampling": draws,
            "train": pairs[:3],
            "test": pairs[3:],
            "labels": {"backend": "included_racket_bridge", "python_parity_checked": True},
        }
        if mode == "teaching":
            audit = self.audit_episode(episode)
            alternate = "farthest" if setting == "nearest" else "nearest"
            if audit["settings"][alternate]["status"] != "refuted_by_demonstrations":
                raise ValueError("teaching demonstrations do not distinguish the alternate setting")
        return episode

    def audit_episode(self, episode):
        """Score both exact programs; a surviving answer-equivalent rival is safe."""
        if len(episode.get("train", [])) != 3 or len(episode.get("test", [])) != 1:
            raise ValueError("this prototype audit expects three demonstrations and one labeled query")
        settings = {}
        for setting in SETTINGS:
            predictions = {split: [self.apply(pair["input"], setting) for pair in episode[split]] for split in ("train", "test")}
            demo_diff = [i for i, output in enumerate(predictions["train"]) if output != episode["train"][i]["output"]]
            query_diff = [i for i, output in enumerate(predictions["test"]) if output != episode["test"][i]["output"]]
            status = "refuted_by_demonstrations" if demo_diff else "harmful_ambiguity" if query_diff else "survived_all"
            settings[setting] = {
                "status": status,
                "mismatching_demo_positions": demo_diff,
                "mismatching_query_positions": query_diff,
                "query_predictions": predictions["test"],
                "racket_sha256": text_digest(self.program(setting)),
            }
        if not any(result["status"] == "survived_all" for result in settings.values()):
            raise ValueError("no declared setting matches all retained demonstration and query labels")
        ambiguous = any(result["status"] == "harmful_ambiguity" for result in settings.values())
        return {
            "status": "ambiguous" if ambiguous else "no_ambiguity_found",
            "episode_sha256": digest(episode),
            "backend": "included_racket_bridge",
            "settings": settings,
            "limit": "Only the two declared parameter rivals are scored; this is not universal identifiability.",
        }

    @staticmethod
    def public_challenge(episode):
        return {
            "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
        }

    def verify_episode(self, episode):
        if episode.get("source_bindings") != self.source_bindings():
            raise ValueError("private episode source binding differs from the current prototype")
        setting = episode["parameters"]["marker_selection"]
        reference = {"racket_text": self.program(setting), "sha256": text_digest(self.program(setting))}
        if episode.get("reference") != reference:
            raise ValueError("private episode reference text/hash mismatch")
        origin = episode.get("selection_origin")
        if origin not in {"seed_draw", "explicit"}:
            raise ValueError("private episode selection_origin is invalid")
        replay = self.make_episode(
            episode["seed"], marker_selection=None if origin == "seed_draw" else setting,
            mode=episode["mode"], difficulty=episode["difficulty"],
        )
        if replay != episode:
            raise ValueError("private episode deterministic Racket replay mismatch")
        return {"status": "verified", "episode_sha256": digest(episode), "audit": self.audit_episode(episode)}


def all_sides_witness():
    grid = [[0] * 9 for _ in range(9)]
    for row in range(3, 6):
        for column in range(3, 6):
            if row in (3, 5) or column in (3, 5):
                grid[row][column] = 3
    for row, column in ((0, 4), (1, 4), (7, 4), (8, 4), (4, 0), (4, 1), (4, 7), (4, 8)):
        grid[row][column] = 6
    return grid


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run_evidence(family, out, *, seed):
    """Retain two teaching episodes, the negative diagnostic, and a safe control."""
    if out.exists():
        raise ValueError(f"output directory already exists: {out}")
    out.mkdir(parents=True)
    (out / "private/rules").mkdir(parents=True)
    for setting in SETTINGS:
        (out / "private/rules" / f"{setting}.rkt").write_text(family.program(setting), encoding="utf-8")
    configurations = [("teaching", setting) for setting in SETTINGS] + [
        ("ambiguous_diagnostic", DEFAULT_SETTING), ("equivalent_control", DEFAULT_SETTING)
    ]
    episodes = []
    for index, (mode, setting) in enumerate(configurations, 1):
        episode = family.make_episode(seed, marker_selection=setting, mode=mode)
        verified = family.verify_episode(episode)
        expected = "ambiguous" if mode == "ambiguous_diagnostic" else "no_ambiguity_found"
        if verified["audit"]["status"] != expected:
            raise ValueError(f"{mode} produced unexpected ambiguity evidence")
        if mode == "equivalent_control" and any(value["status"] != "survived_all" for value in verified["audit"]["settings"].values()):
            raise ValueError("answer-equivalent control does not preserve both parameter candidates")
        challenge = family.public_challenge(episode)
        name = f"episode-{index:03d}"
        write_json(out / "private" / f"{name}.json", episode)
        write_json(out / "private" / f"{name}.audit.json", verified)
        write_json(out / "public" / f"{name}.json", challenge)
        episodes.append({
            "name": name, "mode": mode, "parameters": episode["parameters"],
            "episode_sha256": digest(episode), "public_challenge_sha256": digest(challenge),
            "verification": verified["status"], "ambiguity_status": verified["audit"]["status"],
            "rivals": {key: value["status"] for key, value in verified["audit"]["settings"].items()},
        })
    witness = all_sides_witness()
    outputs = {setting: family.apply(witness, setting) for setting in SETTINGS}
    differences = sum(a != b for ra, rb in zip(outputs["nearest"], outputs["farthest"]) for a, b in zip(ra, rb))
    if not differences:
        raise ValueError("shared witness fails to distinguish the parameter")
    write_json(out / "private/shared-witness.json", {"input": witness, "outputs": outputs, "differing_cells": differences,
        "input_scope": "lawful structural grammar; not a declared named sampling profile",
        "source_bindings": family.source_bindings(), "backend": "included_racket_bridge"})
    canonical = canonical_pairs(TASK_ID, root=family.root)
    canonical_matches = [family.apply(pair["input"]) == pair["output"] for pair in canonical]
    if not all(canonical_matches):
        raise ValueError("canonical Racket output mismatch")
    auto_parameters = [family.select_parameters(s) for s in range(64)]
    replayed_seed_draw = family.make_episode(seed)
    if family.verify_episode(replayed_seed_draw)["status"] != "verified":
        raise ValueError("seed-selected episode replay failed")
    report = {
        "schema": "9971f3a5882c-parametric-evidence-v1", "status": "prototype_verified",
        "task_id": TASK_ID, "parameter_spec": PARAMETER_SPEC, "seed": seed,
        "source_bindings": family.source_bindings(),
        "runtime_identity": family.runtime_identity,
        "programs": {setting: {"racket_text": family.program(setting), "sha256": text_digest(family.program(setting))} for setting in SETTINGS},
        "episodes": episodes, "canonical_pairs_checked": len(canonical),
        "canonical_matches": sum(canonical_matches), "shared_witness_differing_cells": differences,
        "racket_outputs_executed": family.racket_outputs_executed,
        "seed_draw": {"seed": seed, "parameters": replayed_seed_draw["parameters"], "replay": "verified",
            "bounded_seeds_checked": 64, "settings_seen": sorted({p["marker_selection"] for p in auto_parameters})},
        "invocation": {"cwd": str(Path.cwd()), "argv": sys.argv, "python": sys.executable},
        "limits": [
            "Unapproved task-local prototype; canonical runtime interfaces and rule authority are unchanged.",
            "Four retained episodes use one seed, medium difficulty, three demonstrations, and one query.",
            "The ambiguous diagnostic is intentionally constructed and is not an observed natural solver failure.",
            "The equivalent control identifies query answers while leaving the parameter unresolved.",
            "Only nearest/farthest parameter rivals are checked; no claim covers all possible rules or seeds.",
            "Named generated double-marker profiles cover lateral sides; the separate lawful witness covers all four extrema.",
        ],
    }
    write_json(out / "private/report.json", report)
    files = [{"path": p.relative_to(out).as_posix(), "sha256": file_digest(p)} for p in sorted(out.rglob("*")) if p.is_file()]
    write_json(out / "manifest.json", {"schema": "parametric-files-v1", "files": files})
    return report



# Native promotion delegates to the adjacent, source-bound family module.
def _native_module():
    import importlib.util
    path = HERE / "native.py"
    source = path.read_bytes()
    name = "_9971_native_" + hashlib.sha256(str(path).encode() + source).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load native family {path}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def program(settings):
    return _native_module().program(settings)


def generate(seed, settings, demos, queries):
    return _native_module().generate(seed, settings, demos, queries)


def native_analysis(grid):
    return _native_module().native_analysis(grid)


def native_transform(grid, settings):
    return _native_module().native_transform(grid, settings)


def teaching_certificate(episode):
    return _native_module().teaching_certificate(episode)


def plausible_programs():
    return _native_module().plausible_programs()


def dependency_witness():
    return _native_module().dependency_witness()


def wrong_intermediate_program():
    return _native_module().wrong_intermediate_program()

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("evidence", help="write bounded public/private prototype evidence to a new directory")
    run.add_argument("--seed", type=int, default=19073)
    run.add_argument("--out", type=Path, required=True)
    audit = commands.add_parser("audit", help="verify and score an existing private labeled episode")
    audit.add_argument("episode", type=Path)
    audit.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    with Prototype() as family:
        if args.command == "evidence":
            report = run_evidence(family, args.out.resolve(), seed=args.seed)
            print(json.dumps({key: report[key] for key in ("status", "canonical_pairs_checked", "canonical_matches", "shared_witness_differing_cells", "racket_outputs_executed", "episodes")}, indent=2))
            return 0
        if args.out.exists():
            parser.error("--out must be a new file")
        episode = json.loads(args.episode.read_text(encoding="utf-8"))
        result = family.verify_episode(episode)
        result["source_bindings"] = family.source_bindings()
        result["invocation"] = {"cwd": str(Path.cwd()), "argv": sys.argv, "python": sys.executable}
        write_json(args.out, result)
        print(json.dumps({"verification": result["status"], "ambiguity_status": result["audit"]["status"]}, indent=2))
        return 1 if result["audit"]["status"] == "ambiguous" else 0


if __name__ == "__main__":
    raise SystemExit(main())
