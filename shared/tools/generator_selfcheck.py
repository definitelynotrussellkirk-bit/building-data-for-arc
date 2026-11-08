"""Runtime self-check linter for puzzle generators.

Complements the STATIC `scripts/lint_generator.py` (which checks module shape via
AST). This one IMPORTS a generator and exercises it, catching the class of defect
the reviewer random-audits keep finding:

  * RNG-discipline failures   — non-deterministic output, constant output, or
                                unseeded global randomness (the keyed-draw rule).
  * degenerate-in-default     — a declared DEGENERATE texture leaking into the
                                normal (non-override) generation path.
  * invariant violations      — the generator states an INVARIANT but its default
                                output breaks it (corner count, in-bounds, etc.).

Two layers:

1. GENERIC checks (every generator, no per-generator code required):
   - determinism:        generate(seed, i) twice -> byte-identical (catches
                         hash()/time()/global-random/Math.random-style leaks).
   - seed-sensitivity:   N seeds must not all produce the SAME grid (catches the
                         distinct=1 / constant-output defect).
   - index-sensitivity:  warn if sample_index never changes the output.
   - static RNG scan:    no bare `random.<fn>()` / `numpy.random.*` / `time.*`
                         (draws must go through ctx.draw_* / a seeded Random).

2. PER-GENERATOR self-check (opt-in, the executable invariants):
   A generator may define
       def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
           '''Return invariant-violation strings for ONE default instance
           (empty list = clean).'''
   The engine samples N default instances per difficulty (varying both seed and
   sample_index) and runs self_check on each, failing on any violation. This is
   where a generator encodes its OWN
   rules (e.g. "exactly one corner marker", "median bbox non-square", "every run
   odd-length") so the bug we just hand-fixed can never silently come back.

Usage:
    python3 scripts/generator_selfcheck.py 27bc4c66eed7           # one generator
    python3 scripts/generator_selfcheck.py 27bc4c66eed7 --n 200   # more samples
    python3 scripts/generator_selfcheck.py --all                  # bulk gate
    python3 scripts/generator_selfcheck.py --all --require-selfcheck  # also fail
                                            #   generators that ship no self_check
"""
from __future__ import annotations

import argparse
import ast
import inspect
import signal
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.core.canonical_pairs import load_task_pairs
from scripts.generator_module_loader import load_module_from_path

PER_PUZZLE = REPO / "puzzle_generators" / "per_puzzle"
GENERIC_ROOT = REPO / "puzzle_generators" / "generic" / "concepts"
DEFAULT_SEEDS = list(range(40))
DIFFICULTIES = (None, "easy", "hard")
GENERIC_DIFFICULTIES = ("easy", "medium", "hard")


class _SelfcheckTimeout(TimeoutError):
    pass


def _timeout_handler(signum, frame):
    raise _SelfcheckTimeout("generator self-check timed out")


class _time_limit:
    def __init__(self, seconds: float | None):
        self.seconds = seconds
        self.prev_handler = None
        self.prev_timer = None

    def __enter__(self):
        if not self.seconds or self.seconds <= 0:
            return
        self.prev_handler = signal.getsignal(signal.SIGALRM)
        self.prev_timer = signal.setitimer(signal.ITIMER_REAL, self.seconds)
        signal.signal(signal.SIGALRM, _timeout_handler)

    def __exit__(self, exc_type, exc, tb):
        if self.seconds and self.seconds > 0:
            signal.setitimer(signal.ITIMER_REAL, 0)
            if self.prev_handler is not None:
                signal.signal(signal.SIGALRM, self.prev_handler)
            if self.prev_timer and self.prev_timer[0] > 0:
                signal.setitimer(signal.ITIMER_REAL, *self.prev_timer)
        return False


class Report:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []
        self.has_self_check = False

    def err(self, m: str): self.errors.append(m)
    def warn(self, m: str): self.warnings.append(m)
    def note(self, m: str): self.notes.append(m)

    @property
    def exit_code(self) -> int:
        if self.errors:
            return 2
        if self.warnings:
            return 1
        return 0


def _load(task_id: str):
    path = PER_PUZZLE / task_id / "generator.py"
    if not path.exists():
        raise FileNotFoundError(path)
    mod = load_module_from_path(f"gen_{task_id}", path)
    return mod, path




def _generic_path(task_id: str) -> Path:
    """Map generic_dense_recolor_gen2 -> generic/concepts/dense_recolor/gen2.py."""
    if not task_id.startswith("generic_"):
        raise ValueError(f"not a generic task id: {task_id}")
    tail = task_id[len("generic_"):]
    family, sep, gen = tail.rpartition("_")
    if not sep or not family or not gen.startswith("gen"):
        raise ValueError(f"generic task id must look like generic_<family>_genN: {task_id}")
    return GENERIC_ROOT / family / f"{gen}.py"


def _load_generic(task_id: str):
    path = _generic_path(task_id)
    if not path.exists():
        raise FileNotFoundError(path)
    mod = load_module_from_path(f"gen_{task_id}", path)
    return mod, path


def _signature(obj) -> str:
    # The generator outputs are plain nested dict/list/int/string structures; repr
    # is deterministic for them on modern Python and avoids importing json just for
    # a linter signature.  Keep it small enough for set membership only.
    return repr(obj)


def _grid(out):
    """Normalize a generator return to a 2D grid (generators return a grid or a
    {'input': grid, ...} dict / (input, output) tuple)."""
    if isinstance(out, dict):
        return out.get("input", out)
    if isinstance(out, tuple) and out:
        return out[0]
    return out


def _gen(mod, seed, idx, difficulty):
    return _grid(mod.generate(seed=seed, sample_index=idx, difficulty=difficulty))


# ---------------------------------------------------------------- generic checks
def check_determinism(mod, r: Report, seeds):
    """Same (seed, sample_index, difficulty) must give byte-identical output."""
    for difficulty in DIFFICULTIES:
        for s in seeds[:12]:
            try:
                a = _gen(mod, s, 0, difficulty)
                b = _gen(mod, s, 0, difficulty)
            except Exception as e:
                r.err(f"generate raised at seed={s} difficulty={difficulty}: {type(e).__name__}: {str(e)[:80]}")
                return
            if a != b:
                r.err(f"NON-DETERMINISTIC: seed={s} difficulty={difficulty} gave two different grids "
                      f"(RNG not fully seeded — check for global random/hash()/time()).")
                return


def check_indexed_generation_smoke(mod, r: Report, seeds):
    """Default generation must also survive realistic nonzero sample_index values.

    The older generic checks exercised many seeds at sample_index=0 and a few
    small indices at fixed seeds.  That missed generators whose keyed RNG only
    failed for the common streaming pattern sample_index==seed (for example a
    template with too many cells for the available color palette).
    """
    for difficulty in DIFFICULTIES:
        for s in seeds[:12]:
            for idx in (s, s + 1):
                try:
                    _gen(mod, s, idx, difficulty)
                except Exception as e:
                    r.err(f"generate raised at seed={s} sample_index={idx} difficulty={difficulty}: "
                          f"{type(e).__name__}: {str(e)[:80]}")
                    return


def check_seed_sensitivity(mod, r: Report, seeds):
    """N seeds must not all collapse to one grid (the distinct=1 defect)."""
    grids = []
    for s in seeds:
        try:
            grids.append(tuple(tuple(row) for row in _gen(mod, s, 0, None)))
        except Exception:
            continue
    if not grids:
        r.err("generate produced nothing across all seeds")
        return
    distinct = len(set(grids))
    if distinct == 1:
        r.err(f"CONSTANT OUTPUT: all {len(grids)} seeds produced the SAME grid (distinct=1).")
    elif distinct < max(3, len(grids) // 8):
        r.warn(f"LOW DIVERSITY: only {distinct} distinct grids across {len(grids)} seeds.")


def check_index_sensitivity(mod, r: Report, seeds):
    """A fixed seed across sample_index should usually vary (episodes differ)."""
    for s in seeds[:6]:
        outs = set()
        for i in range(4):
            try:
                outs.add(tuple(tuple(row) for row in _gen(mod, s, i, None)))
            except Exception:
                outs = set()
                break
        if len(outs) > 1:
            return
    r.note("sample_index never changed the output across sampled seeds "
           "(ok if the generator is index-invariant by design).")


_FORBIDDEN_RANDOM = {"random"}          # the global module (random.random(), ...)
_FORBIDDEN_ROOTS = {"time"}             # time.time()-style seeding


def check_rng_discipline_static(src: str, r: Report):
    """AST scan: draws must go through ctx.draw_* or a seeded Random instance,
    never the global `random.<fn>()` module RNG or wall-clock time."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return  # the static linter reports syntax errors
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            val = node.func.value
            # random.random(), random.randint(...) — the global RNG (bad).
            # rng.randint(...) is fine (value is a Name like 'rng', not 'random').
            if isinstance(val, ast.Name) and val.id in _FORBIDDEN_RANDOM:
                r.err(f"uses global `random.{node.func.attr}(...)` (unseeded) — "
                      f"draw via ctx.draw_rng(...)/ctx.draw_* instead (line {node.lineno}).")
            if isinstance(val, ast.Name) and val.id == "np" and node.func.attr.startswith("random"):
                r.err(f"uses numpy global random at line {node.lineno} — seed it or use ctx.")
            if isinstance(val, ast.Attribute) and isinstance(val.value, ast.Name):
                if val.value.id in ("numpy",) and val.attr == "random":
                    r.err(f"uses numpy.random.* (unseeded) at line {node.lineno}.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            root = node.func.value
            if isinstance(root, ast.Name) and root.id in _FORBIDDEN_ROOTS:
                r.warn(f"references `{root.id}.{node.func.attr}` (line {node.lineno}) — "
                       f"wall-clock breaks determinism if used as a seed.")


# --------------------------------------------------------------- per-generator
def run_self_check(mod, r: Report, n: int):
    fn = getattr(mod, "self_check", None)
    if not callable(fn):
        r.note("no self_check() defined — generic checks only. "
               "Add `def self_check(grid, *, difficulty=None, meta=None) -> list[str]` "
               "to assert this generator's invariants.")
        return
    r.has_self_check = True
    total = 0
    violations: dict[str, int] = {}
    examples: dict[str, tuple] = {}
    for difficulty in DIFFICULTIES:
        for s in range(n):
            try:
                # Vary sample_index as well as seed: many generators deliberately
                # alternate pedagogical branches across episode pairs.  Checking
                # only sample_index=0 lets an entire branch rot while still
                # reporting "self_check clean".
                out = mod.generate(seed=s, sample_index=s, difficulty=difficulty)
            except Exception as e:
                r.err(f"generate raised during self_check (seed={s}, diff={difficulty}): "
                      f"{type(e).__name__}: {str(e)[:80]}")
                return
            grid = _grid(out)
            meta = out if isinstance(out, dict) else None
            total += 1
            try:
                msgs = fn(grid, difficulty=difficulty, meta=meta) or []
            except TypeError:
                msgs = fn(grid) or []        # tolerate a 1-arg self_check
            for m in msgs:
                violations[m] = violations.get(m, 0) + 1
                examples.setdefault(m, (s, difficulty))
    if violations:
        for m, cnt in sorted(violations.items(), key=lambda kv: -kv[1]):
            s, d = examples[m]
            r.err(f"self_check FAIL {cnt}/{total}: {m} (first at seed={s}, diff={d})")
    else:
        r.note(f"self_check clean across {total} default instances.")


def _mutations(grid):
    """Generic destructive mutations that a scene grammar should almost surely
    reject. Task-agnostic by necessity: this measures whether self_check is
    SENSITIVE at all, not whether it is correct. Yields (kind, mutated_grid);
    inapplicable kinds are skipped."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w:
        return
    yield "blank_grid", [[0] * w for _ in range(h)]
    cells = [(ri, ci) for ri in range(h) for ci in range(w) if grid[ri][ci]]
    present = {v for row in grid for v in row}
    absent = [c for c in range(1, 10) if c not in present]
    if cells and absent:
        ri, ci = cells[len(cells) // 2]
        g2 = [list(row) for row in grid]
        g2[ri][ci] = absent[0]
        yield "absent_color_cell", g2
    nonzero_counts: dict[int, int] = {}
    for row in grid:
        for v in row:
            if v:
                nonzero_counts[v] = nonzero_counts.get(v, 0) + 1
    if len(nonzero_counts) >= 2:
        minority = min(nonzero_counts, key=lambda c: (nonzero_counts[c], c))
        g3 = [[0 if v == minority else v for v in row] for row in grid]
        yield "drop_minority_color", g3
    if h >= 2 and grid[0] != grid[-1]:
        g4 = [list(row) for row in grid]
        g4[-1] = list(grid[0])
        yield "duplicate_first_row", g4
    # Color-role inversion (EWF-002035): dense inversions can flip which
    # color modal-background reasoning treats as background, hiding impostors
    # from palette/shape-only checkers. Lawful for genuinely palette-symmetric
    # tasks — these kinds only measure sensitivity.
    if len(nonzero_counts) == 1 and cells and len(cells) < h * w:
        (fg,) = nonzero_counts
        yield "invert_fg_bg_roles", [
            [0 if v else fg for v in row] for row in grid]
    elif len(nonzero_counts) == 2:
        first_color, second_color = sorted(nonzero_counts)
        swap = {first_color: second_color, second_color: first_color}
        yield "swap_two_colors", [[swap.get(v, v) for v in row] for row in grid]


def check_mutation_sensitivity(mod, r: Report, *, samples: int = 5,
                               require: bool = False) -> None:
    """ACCEPTANCE-ONLY SELF_CHECK DETECTOR (the 2db1f7f0392d class).

    A self_check that accepts every destructive mutation of its own output
    proves nothing when it stays green — the baseline 2db1f7f0392d checker
    accepted four task-defining malformed mutations while the stage passed.
    Apply generic destructive mutations to default instances and count
    rejections. Zero rejections across every kind and sample = non-probative:
    ERROR when `require` (the battery/monitor path), loud warning otherwise.
    """
    fn = getattr(mod, "self_check", None)
    if not callable(fn):
        return
    tried: dict[str, int] = {}
    rejected: dict[str, int] = {}
    for difficulty in DIFFICULTIES:
        for s in range(samples):
            try:
                out = mod.generate(seed=s, sample_index=s, difficulty=difficulty)
            except Exception:
                continue  # generation failures are reported by earlier checks
            grid = _grid(out)
            if not grid:
                continue
            for kind, mutated in _mutations(grid):
                tried[kind] = tried.get(kind, 0) + 1
                try:
                    try:
                        msgs = fn(mutated, difficulty=difficulty, meta=None) or []
                    except TypeError:
                        msgs = fn(mutated) or []
                    if msgs:
                        rejected[kind] = rejected.get(kind, 0) + 1
                except Exception:
                    # a crash on malformed input still demonstrates sensitivity
                    rejected[kind] = rejected.get(kind, 0) + 1
    if not tried:
        r.note("mutation-sensitivity: no applicable mutations (degenerate grids)")
        return
    total_tried = sum(tried.values())
    total_rejected = sum(rejected.values())
    detail = ", ".join(
        f"{kind} {rejected.get(kind, 0)}/{cnt}" for kind, cnt in sorted(tried.items())
    )
    if total_rejected == 0:
        msg = (f"self_check is ACCEPTANCE-ONLY: 0/{total_tried} destructive "
               f"mutations rejected ({detail}) — a green self_check stage is "
               "non-probative for this generator")
        if require:
            r.err(msg)
        else:
            r.warn(msg)
    else:
        r.note(f"mutation-sensitivity: {total_rejected}/{total_tried} destructive "
               f"mutations rejected ({detail})")


def check_canonical_inputs(task_id: str, mod, r: Report) -> None:
    """Require ``self_check`` to accept every authoritative canonical input."""
    fn = getattr(mod, "self_check", None)
    if not callable(fn):
        return
    try:
        pairs = load_task_pairs(task_id)
    except Exception as exc:
        r.err(
            "could not load canonical inputs for self_check: "
            f"{type(exc).__name__}: {exc}"
        )
        return
    if not pairs:
        r.err("no canonical train/test inputs found for canonical self_check")
        return

    parameters = inspect.signature(fn).parameters
    for pair in pairs:
        kwargs = {}
        if "difficulty" in parameters:
            kwargs["difficulty"] = None
        if "meta" in parameters:
            kwargs["meta"] = {
                "canonical": True,
                "split": pair["split"],
                "row_index": pair["row_index"],
                "pair_index": pair["pair_index"],
            }
        try:
            messages = fn(pair["input"], **kwargs) or []
        except Exception as exc:
            r.err(
                "self_check raised on canonical "
                f"row={pair['row_index']} {pair['split']}"
                f"[{pair['pair_index']}]: {type(exc).__name__}: {exc}"
            )
            continue
        if messages:
            r.err(
                "self_check rejected canonical "
                f"row={pair['row_index']} {pair['split']}"
                f"[{pair['pair_index']}]: {messages}"
            )
    if not any("canonical" in error for error in r.errors):
        r.note(
            f"self_check accepted {len(pairs)} canonical train/test inputs "
            "across all source rows."
        )




def selfcheck_generic(task_id: str, *, n: int = 60, seeds=None,
                      timeout_sec: float | None = 10.0) -> Report:
    """Runtime checks for generic concept generators that emit whole tasks.

    Per-puzzle generators expose generate(seed, sample_index, difficulty) -> grid;
    generic concept generators expose generate_task(seed, difficulty) ->
    {train,test,program,meta}.  The random-audit prompt can assign either, so the
    linter needs to exercise both shapes.
    """
    seeds = seeds or DEFAULT_SEEDS
    r = Report(task_id)
    try:
        with _time_limit(timeout_sec):
            mod, path = _load_generic(task_id)
            check_rng_discipline_static(path.read_text(), r)
            gen_task = getattr(mod, "generate_task", None)
            if not callable(gen_task):
                r.err("generic generator has no generate_task(seed, *, difficulty=...) entrypoint")
                return r

            for difficulty in GENERIC_DIFFICULTIES:
                for s in seeds[:12]:
                    try:
                        a = gen_task(s, difficulty=difficulty)
                        b = gen_task(s, difficulty=difficulty)
                    except Exception as e:
                        r.err(f"generate_task raised at seed={s} difficulty={difficulty}: "
                              f"{type(e).__name__}: {str(e)[:80]}")
                        return r
                    if _signature(a) != _signature(b):
                        r.err(f"NON-DETERMINISTIC generate_task: seed={s} difficulty={difficulty} "
                              "gave two different tasks.")
                        return r

            sigs = []
            for s in seeds:
                try:
                    sigs.append(_signature(gen_task(s, difficulty="medium")))
                except Exception:
                    continue
            distinct = len(set(sigs))
            if not sigs:
                r.err("generate_task produced nothing across all seeds")
            elif distinct == 1:
                r.err(f"CONSTANT TASK: all {len(sigs)} seeds produced the same task.")
            elif distinct < max(3, len(sigs) // 8):
                r.warn(f"LOW TASK DIVERSITY: only {distinct} distinct tasks across {len(sigs)} seeds.")

            fn = getattr(mod, "self_check_task", None)
            if not callable(fn):
                r.note("no self_check_task(task) defined — generic determinism/diversity checks only.")
                return r
            r.has_self_check = True
            total = 0
            violations: dict[str, int] = {}
            examples: dict[str, tuple] = {}
            for difficulty in GENERIC_DIFFICULTIES:
                for s in range(n):
                    task = gen_task(s, difficulty=difficulty)
                    total += 1
                    for msg in fn(task) or []:
                        violations[msg] = violations.get(msg, 0) + 1
                        examples.setdefault(msg, (s, difficulty))
            if violations:
                for m, cnt in sorted(violations.items(), key=lambda kv: -kv[1]):
                    s0, d0 = examples[m]
                    r.err(f"self_check_task FAIL {cnt}/{total}: {m} (first at seed={s0}, diff={d0})")
            else:
                r.note(f"self_check_task clean across {total} generated tasks.")
    except _SelfcheckTimeout:
        r.err(f"TIMEOUT after {timeout_sec:g}s — generic generation/self_check did not finish.")
    except Exception as e:
        r.err(f"could not import/check generic generator: {type(e).__name__}: {str(e)[:120]}")
    return r


def selfcheck_generator(task_id: str, *, n: int = 60, seeds=None,
                        timeout_sec: float | None = 10.0,
                        require_mutation_sensitivity: bool = False) -> Report:
    if task_id.startswith("generic_"):
        return selfcheck_generic(task_id, n=n, seeds=seeds, timeout_sec=timeout_sec)
    seeds = seeds or DEFAULT_SEEDS
    r = Report(task_id)
    try:
        with _time_limit(timeout_sec):
            mod, path = _load(task_id)
            check_rng_discipline_static(path.read_text(), r)
            check_determinism(mod, r, seeds)
            if not r.errors:
                check_indexed_generation_smoke(mod, r, seeds)
            if not r.errors:                      # cheap checks only if it runs cleanly
                check_seed_sensitivity(mod, r, seeds)
                check_index_sensitivity(mod, r, seeds)
            run_self_check(mod, r, n)
            check_canonical_inputs(task_id, mod, r)
            check_mutation_sensitivity(
                mod, r, require=require_mutation_sensitivity)
    except _SelfcheckTimeout:
        r.err(f"TIMEOUT after {timeout_sec:g}s — generation/self_check did not finish; "
              "bulk CI must fail closed instead of hanging on one generator.")
    except Exception as e:
        r.err(f"could not import/check generator: {type(e).__name__}: {str(e)[:120]}")
    return r


def _print(r: Report) -> None:
    tag = "PASS" if r.exit_code == 0 else ("WARN" if r.exit_code == 1 else "FAIL")
    sc = "self_check" if r.has_self_check else "generic-only"
    print(f"[{tag}] {r.task_id} ({sc})")
    for e in r.errors:
        print(f"    ERROR  {e}")
    for w in r.warnings:
        print(f"    warn   {w}")
    for nt in r.notes:
        print(f"    note   {nt}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id", nargs="?", help="per_puzzle or generic_<family>_genN task id (omit with --all)")
    ap.add_argument("--task-id", dest="task_id_option",
                    help="alias for the positional task_id")
    ap.add_argument("--all", action="store_true", help="check every per_puzzle generator")
    ap.add_argument("--n", "--seeds", dest="n", type=int, default=60,
                    help="self_check samples per difficulty")
    ap.add_argument("--timeout-sec", type=float, default=10.0,
                    help="per-generator wall-clock limit; 0 disables. Used for both single and --all runs so a bad generator cannot hang CI.")
    ap.add_argument("--require-selfcheck", action="store_true",
                    help="treat a missing self_check() as an error (rollout gate)")
    ap.add_argument("--require-mutation-sensitivity", action="store_true",
                    help="treat an acceptance-only self_check (rejects zero "
                         "generic destructive mutations) as an error — the "
                         "battery/monitor promotion path sets this")
    a = ap.parse_args(argv)

    if a.task_id and a.task_id_option and a.task_id != a.task_id_option:
        ap.error("positional task_id and --task-id must match")
    task_id = a.task_id_option or a.task_id

    if a.all:
        ids = sorted(p.name for p in PER_PUZZLE.iterdir()
                     if (p / "generator.py").exists())
        fails = warns = no_sc = 0
        for tid in ids:
            r = selfcheck_generator(
                tid, n=a.n, timeout_sec=a.timeout_sec,
                require_mutation_sensitivity=a.require_mutation_sensitivity)
            if a.require_selfcheck and not r.has_self_check and not r.errors:
                r.err("no self_check() (required by --require-selfcheck)")
            if r.exit_code == 2:
                fails += 1
                _print(r)
            elif r.exit_code == 1:
                warns += 1
            if not r.has_self_check:
                no_sc += 1
        print(f"\n{len(ids)} generators: {fails} FAIL, {warns} warn, "
              f"{no_sc} without self_check.")
        return 2 if fails else 0

    if not task_id:
        ap.error("provide a task_id or --all")
    r = selfcheck_generator(
        task_id, n=a.n, timeout_sec=a.timeout_sec,
        require_mutation_sensitivity=a.require_mutation_sensitivity)
    if a.require_selfcheck and not r.has_self_check and not r.errors:
        r.err("no self_check() (required by --require-selfcheck)")
    _print(r)
    return r.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
