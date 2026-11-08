#!/usr/bin/env python3
"""Static lint for a candidate puzzle-instance generator.

Use case: an offline-authored generator (paste into ChatGPT / etc., get
a Python file back) needs a sanity check before being committed. This
script validates the file against the spec WITHOUT running it. Call
with `--validate` to also run 20 instances through the runner.

Usage:
    # Lint a file at a specific path:
    python3 scripts/lint_generator.py path/to/generator.py

    # Lint by task_id (resolves to puzzle_generators/per_puzzle/<id>/generator.py):
    python3 scripts/lint_generator.py 952a094c

    # Also actually run the generator:
    python3 scripts/lint_generator.py 952a094c --validate

Checks:
  1. File parses as Python.
  2. Required module constants present and well-typed:
     GENERATOR_ID, VERSION, TASK_ID, RULE_HASH, SUMMARY,
     INVARIANTS (non-empty list[str]), AXES (dict). CONCEPT_HASH is optional.
  3. TASK_ID matches dirname (with `:` ↔ `__` mangling).
  4. Optional CONCEPT_HASH matches the canonicalized rule (warning if mismatched).
  5. Has `def generate(seed, sample_index, *, difficulty=None, **overrides)`.
  6. No `import random` or bare `random.*` calls (use ctx.draw_*).
  7. No suspicious "rule reimplementation": rule's primitive heads
     (find-color, recolor, etc.) appearing as Python function names is
     a smell — likely the model translated the rule into Python.
  8. Returns from `generate` exit type-compatible (return statements
     present, not just falling off end).
  9. AXES domains are actually probeable. Every declared axis is run
     through the OVERRIDE CHECKER'S OWN domain parser
     (`check_generator_override_contract.axis_domain_report`) so a dead
     axis is caught here, in milliseconds, instead of silently dropping
     out of a multi-thousand-draw Cartesian matrix that then reports
     PASS. ERROR for an unparsable declaration; WARNING for a singleton
     or single-enum-token domain the matrix never probes. Opt out for a
     genuinely unexpressible domain with `{"probe": "diagnostic"}`.
 10. (--validate only) Realized-axis honesty over a small cohort:
     axes `observe_overrides` cannot recover, and ALIAS axes whose
     realized values are perfectly locked to another axis (two names,
     one degree of freedom — the matrix pays for both).

Exit codes:
  0 — all checks pass
  1 — at least one warning (yellow) but nothing fatal
  2 — at least one error (red) — do not integrate
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PER_PUZZLE_DIR = ROOT / "puzzle_generators" / "per_puzzle"

GREEN = "\033[32m"; RED = "\033[31m"; YELLOW = "\033[33m"; RESET = "\033[0m"


# Heads from the Racket prelude that, if they appear as Python identifiers,
# suggest the author tried to translate the rule into Python instead of
# using the bridge. Soft signal — emit a warning, not a fatal error.
RACKET_PRIMITIVE_NAMES = {
    "find_color", "find-color", "recolor", "objects", "objects_8",
    "obj_color", "obj_size", "obj_bbox", "obj_cells", "crop_to_content",
    "self_tile", "kaleidoscope", "rotate_cw", "flip_lr",
}

PLACE_NO_OVERLAP_SUPPRESSION = "lint: place-no-overlap-postcondition"


def _primitive_name_diagnostics(tree):
    """Classify a naming smell, not semantic rule equivalence.

    Only isolated locally bound names without callable syntax become advisory.
    Definitions, calls, lambdas/aliases, imports, nonlocal/global names, module/class
    names and primitive-name clusters keep warnings. No alias/dataflow proof.
    """
    scopes = []

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = self.new_scope("module", False)

        def new_scope(self, label, local):
            scope = dict(label=label, local=local, names={}, bound=set(),
                         strong={}, external=set())
            scopes.append(scope)
            return scope

        def record(self, name, node, reason=None, bound=False):
            if name not in RACKET_PRIMITIVE_NAMES:
                return
            self.scope['names'].setdefault(name, node.lineno)
            if bound:
                self.scope['bound'].add(name)
            if reason:
                self.scope['strong'].setdefault(name, reason)

        def visit_Name(self, node):
            self.record(node.id, node, bound=isinstance(node.ctx, ast.Store))

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                self.record(node.func.id, node, 'direct call')
            self.generic_visit(node)

        def visit_Assign(self, node):
            if isinstance(node.value, (ast.Lambda, ast.Name, ast.Attribute)):
                reason = 'lambda binding' if isinstance(node.value, ast.Lambda) else 'alias binding'
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.record(target.id, target, reason)
            self.generic_visit(node)

        def visit_AnnAssign(self, node):
            if isinstance(node.value, (ast.Lambda, ast.Name, ast.Attribute)) and isinstance(node.target, ast.Name):
                reason = 'lambda binding' if isinstance(node.value, ast.Lambda) else 'alias binding'
                self.record(node.target.id, node.target, reason)
            self.generic_visit(node)

        def visit_Global(self, node):
            self.scope['external'].update(node.names)

        visit_Nonlocal = visit_Global

        def visit_Import(self, node):
            for alias in node.names:
                self.record(alias.asname or alias.name.split('.')[0], node, 'import binding')

        visit_ImportFrom = visit_Import

        def visit_FunctionDef(self, node):
            self.record(node.name, node, 'function definition')
            # Decorators/defaults execute in the enclosing scope.
            for part in [*node.decorator_list, *node.args.defaults,
                         *[x for x in node.args.kw_defaults if x is not None]]:
                self.visit(part)
            parent = self.scope
            self.scope = self.new_scope(parent['label'] + '.' + node.name, True)
            for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                        *[x for x in (node.args.vararg, node.args.kwarg) if x is not None]]:
                self.record(arg.arg, arg, bound=True)
            for part in node.body:
                self.visit(part)
            self.scope = parent

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.record(node.name, node, 'class definition')
            for part in [*node.decorator_list, *node.bases, *node.keywords]:
                self.visit(part)
            parent = self.scope
            self.scope = self.new_scope(parent['label'] + '.' + node.name, False)
            for part in node.body:
                self.visit(part)
            self.scope = parent

    Visitor().visit(tree)
    for scope in scopes:
        for name, line in sorted(scope['names'].items()):
            reason = scope['strong'].get(name)
            if not reason and (name in scope['external'] or name not in scope['bound']):
                reason = 'nonlocal/global or unresolved name'
            if not reason and not scope['local']:
                reason = 'module/class binding'
            if not reason and len(scope['names']) > 1:
                reason = 'multiple primitive names in one scope'
            context = f"scope {scope['label']}, line {line}"
            if reason:
                yield 'warning', (f"identifier `{name}` echoes a Racket primitive "
                                  f"({reason}; {context}); inspect possible rule reimplementation")
            else:
                yield 'note', (f"identifier `{name}` echoes a Racket primitive "
                               f"(isolated local name without callable syntax; {context}); naming advisory only")


def _ignored_place_no_overlap_lines(
    tree: ast.AST,
    source_lines: list[str],
) -> list[int]:
    """Find unchecked calls whose Optional placement result is discarded."""
    ignored: list[int] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "place_no_overlap"
        ):
            continue
        line_number = getattr(node, "lineno", 0)
        source_line = (
            source_lines[line_number - 1]
            if 0 < line_number <= len(source_lines)
            else ""
        )
        if PLACE_NO_OVERLAP_SUPPRESSION in source_line:
            continue
        ignored.append(line_number)
    return ignored


def _safe_constant_eval(node: ast.AST, env: dict[str, object]) -> object:
    """Evaluate the tiny, side-effect-free subset used by generator metadata.

    Many generators keep AXES readable by deriving valid strings from literal
    tuples, e.g. ``"|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)``.
    ``ast.literal_eval`` rejects that expression even though it is completely
    static, which makes clean generators fail the lint gate.  This evaluator is
    deliberately narrow: literals, names already resolved to literals, ``+`` for
    same-kind sequences/strings, and ``str.join`` over a literal string sequence.
    It never executes generator code.
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_safe_constant_eval(e, env) for e in node.elts)
    if isinstance(node, ast.List):
        return [_safe_constant_eval(e, env) for e in node.elts]
    if isinstance(node, ast.Set):
        return {_safe_constant_eval(e, env) for e in node.elts}
    if isinstance(node, ast.Dict):
        return {
            _safe_constant_eval(k, env): _safe_constant_eval(v, env)
            for k, v in zip(node.keys, node.values)
        }
    if isinstance(node, ast.Name) and node.id in env and env[node.id] != "<non-literal>":
        return env[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _safe_constant_eval(node.left, env)
        right = _safe_constant_eval(node.right, env)
        if isinstance(left, tuple) and isinstance(right, tuple):
            return left + right
        if isinstance(left, list) and isinstance(right, list):
            return left + right
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join" and len(node.args) == 1
            and not node.keywords):
        sep = _safe_constant_eval(node.func.value, env)
        vals = _safe_constant_eval(node.args[0], env)
        if isinstance(sep, str) and isinstance(vals, (list, tuple)) and all(isinstance(v, str) for v in vals):
            return sep.join(vals)
    raise ValueError("not a safe static metadata expression")


class LintReport:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def err(self, msg: str): self.errors.append(msg)
    def warn(self, msg: str): self.warnings.append(msg)
    def note(self, msg: str): self.notes.append(msg)

    @property
    def exit_code(self) -> int:
        if self.errors: return 2
        if self.warnings: return 1
        return 0


def _covers_declared_output_codomain(expected: object, observed: int) -> bool:
    """Whether a sampled output alphabet exhausts a declared finite space."""
    return (
        isinstance(expected, int)
        and not isinstance(expected, bool)
        and expected > 0
        and observed >= expected
    )


#: Cohort used by the --validate axis-honesty probe. Small on purpose: it
#: only has to expose a LOCKED relation, not estimate a distribution.
_COHORT_BANDS = ("easy", "medium", "hard")
_COHORT_SEEDS = 4
#: Distinct realized values a pair must show before "perfectly locked" is
#: evidence of aliasing rather than a small-sample coincidence.
_ALIAS_MIN_DISTINCT = 3


def _check_axis_domains(axes: dict, r: LintReport) -> None:
    """Run the override checker's own domain parser over declared AXES.

    Why this lives here and not only in the override checker: the checker
    reaches this conclusion AFTER building the Cartesian matrix, by which
    point a 7-axis generator has already produced thousands of draws whose
    findings all trace back to the dead declarations. Blast radius measured
    2026-07-25 over 3887 generators with parsable non-empty AXES:
    231 (5.9%) would newly ERROR, 2537 (65.3%) hit the single-enum-token
    WARNING. The 65% class is a WARNING precisely because a gate that fails
    two thirds of the corpus gets ignored.
    """
    from scripts.check_generator_override_contract import axis_domain_report

    diagnostic: list[str] = []
    for domain in axis_domain_report(axes):
        if domain.status in {"unparsable", "malformed"}:
            r.err(f"AXES[{domain.name!r}] is never probed: {domain.reason}")
        elif domain.status == "never_probed":
            r.warn(f"AXES[{domain.name!r}] is never probed: {domain.reason}")
        elif domain.status == "singleton":
            r.warn(f"AXES[{domain.name!r}] singleton domain: {domain.reason}")
        elif domain.status == "finite_enum_too_large":
            r.warn(f"AXES[{domain.name!r}] finite_enum_too_large: {domain.reason}")
        elif domain.status == "diagnostic":
            diagnostic.append(domain.name)
    if diagnostic:
        r.note(
            "axes declared diagnostic (exempt from the boundary matrix): "
            + ", ".join(sorted(diagnostic))
        )


def _locked_axis_pairs(
    samples: list[dict], axes_of_interest: list[str]
) -> list[tuple[str, str, int]]:
    """Axis pairs whose realized values are 1:1 locked across the cohort.

    An alias axis is not a harmless duplicate: it doubles the axis count
    (and therefore the pairwise matrix) while adding zero degrees of
    freedom, and it makes an override look honored when the other name is
    what actually drove the draw.
    """
    locked: list[tuple[str, str, int]] = []
    for index, left in enumerate(axes_of_interest):
        for right in axes_of_interest[index + 1:]:
            try:
                pairs = {
                    (sample[left], sample[right])
                    for sample in samples
                    if left in sample and right in sample
                }
                lefts = {pair[0] for pair in pairs}
                rights = {pair[1] for pair in pairs}
            except TypeError:  # unhashable realized value — cannot judge
                continue
            if len(pairs) < _ALIAS_MIN_DISTINCT:
                continue
            if len(lefts) == len(rights) == len(pairs):
                locked.append((left, right, len(pairs)))
    return locked


def _check_realized_axis_honesty(module, axes: dict, r: LintReport) -> None:
    """Cohort probe: which exact axes can observe_overrides actually recover?"""
    from scripts.check_generator_override_contract import (
        _required_observer_axes,
    )

    required = sorted(_required_observer_axes(axes))
    if not required:
        return
    observer = getattr(module, "observe_overrides", None)
    if not callable(observer):
        r.warn(
            f"no observe_overrides(grid): {len(required)} exact axis/axes "
            f"({', '.join(required)}) cannot be recovered from a returned "
            "grid, so an accepted override cannot be falsified"
        )
        return

    generate = getattr(module, "generate", None)
    samples: list[dict] = []
    failures = 0
    for band in _COHORT_BANDS:
        for seed in range(_COHORT_SEEDS):
            try:
                grid = generate(seed, seed * 17 + 3, difficulty=band)
                observed = observer(grid)
            except Exception as e:  # noqa: BLE001 — counted, never silent
                failures += 1
                if failures == 1:
                    r.warn(
                        "axis-honesty cohort draw failed "
                        f"({band}/seed {seed}): {type(e).__name__}: {e}"
                    )
                continue
            if isinstance(observed, dict):
                samples.append(observed)
            else:
                failures += 1
    if failures:
        r.note(f"axis-honesty cohort: {failures}/"
               f"{len(_COHORT_BANDS) * _COHORT_SEEDS} draws unusable")
    if not samples:
        return

    unrecoverable = [
        axis for axis in required
        if not any(axis in sample for sample in samples)
    ]
    if unrecoverable:
        r.warn(
            "observe_overrides never reports exact axis/axes "
            f"{', '.join(unrecoverable)} over {len(samples)} cohort draws — "
            "the override checker cannot verify those overrides were honored"
        )
    recoverable = [
        axis for axis in required
        if all(axis in sample for sample in samples)
    ]
    suspected = _locked_axis_pairs(samples, recoverable)
    if suspected:
        # The 12-row cohort links seed and sample_index and repeats each draw
        # across bands. Recheck suspected locks on an independent grid before
        # treating that small sample as evidence of aliasing.
        expanded = []
        for seed in range(8):
            for sample_index in range(8):
                try:
                    observed = observer(generate(seed, sample_index, difficulty="medium"))
                except Exception:  # an unusable probe cannot refute the warning
                    continue
                if isinstance(observed, dict):
                    expanded.append(observed)
        from scripts.check_generator_override_contract import axis_domain_report
        domains = {domain.name: domain.values for domain in axis_domain_report(axes)}
        for left, right, distinct in suspected:
            pairs = {(item[left], item[right]) for item in expanded
                     if left in item and right in item}
            if pairs and (len({a for a, _ in pairs}) < len(pairs)
                          or len({b for _, b in pairs}) < len(pairs)):
                r.note(f"axes {left!r} and {right!r}: expanded seed/index draws refute cohort lock")
                continue
            left_values, right_values = domains.get(left, []), domains.get(right, [])
            independent = False
            if len(left_values) >= 2 and len(right_values) >= 2:
                probes = ((left_values[0], right_values[0]),
                          (left_values[-1], right_values[0]),
                          (left_values[0], right_values[-1]))
                try:
                    independent = all(
                        (actual := observer(generate(0, 3, difficulty="medium",
                                                     **{left: a, right: b}))).get(left) == a
                        and actual.get(right) == b
                        for a, b in probes
                    )
                except Exception:
                    pass
            if independent:
                r.warn(f"axes {left!r} and {right!r} have independently honored overrides "
                       f"but their default draws remain 1:1 locked; vary the default schedule")
            else:
                r.warn(
                    f"axes {left!r} and {right!r} look like aliases: realized values "
                    f"are 1:1 locked across all {len(samples)} cohort draws "
                    f"({distinct} distinct pairs) — collapse them or document why "
                    "both names exist"
                )


def _rule_hash_pin_hint(constants: dict) -> str:
    """The exact pin to add, read from the selected canonical rule; empty when unavailable."""
    task = constants.get("RULE_TASK_ID") or constants.get("TASK_ID")
    if not isinstance(task, str) or not task:
        return ""
    try:
        from scripts.canonical_profile_gate import canonical_rule_source, normalized_rule_hash
        current = normalized_rule_hash(canonical_rule_source(task))
    except Exception:
        return ""
    return (f'pin RULE_HASH = "{current}" (current canonical rule hash for {task}; '
            "re-verify the generator against that rule before pinning)")


def lint_generator(path: Path, *, validate: bool = False) -> LintReport:
    r = LintReport()
    if not path.exists():
        r.err(f"file not found: {path}")
        return r

    src = path.read_text()

    # 1. Parses as Python
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        r.err(f"Python syntax error: {e}")
        return r

    # 2. Required module constants
    constants: dict[str, object] = {}
    has_generate = False
    generate_node = None
    self_check_nodes: list[ast.FunctionDef] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    try:
                        constants[tgt.id] = _safe_constant_eval(node.value, constants)
                    except Exception:
                        constants[tgt.id] = "<non-literal>"
        elif isinstance(node, ast.FunctionDef) and node.name == "generate":
            has_generate = True
            generate_node = node
        if isinstance(node, ast.FunctionDef) and node.name == "self_check":
            self_check_nodes.append(node)

    required = {
        "GENERATOR_ID":  str,
        "VERSION":       str,
        "TASK_ID":       str,
        "SUMMARY":       str,
        "INVARIANTS":    list,
        "AXES":          dict,
        "RULE_HASH":     str,
    }
    optional = {
        # CONCEPT_HASH was once required; now optional. Round-7 audit
        # found 1356/2616 generators shipped CONCEPT_HASH = "" (empty)
        # which is worse than absent because it looks filled. Treat
        # empty as "not yet computed" (warn), absent as "not relevant".
        "CONCEPT_HASH":  str,
    }
    for name, t in required.items():
        if name not in constants:
            r.err(f"missing required module constant: {name}")
            if name == "RULE_HASH":
                hint = _rule_hash_pin_hint(constants)
                if hint:
                    r.note(hint)
        elif constants[name] == "<non-literal>":
            r.warn(f"{name} is not a literal — can't validate type")
        elif not isinstance(constants[name], t):
            r.err(f"{name} should be {t.__name__}, got {type(constants[name]).__name__}")
        elif name == "RULE_HASH" and not re.fullmatch(r"[0-9a-f]{12}", constants[name]):
            r.err("RULE_HASH must be exactly 12 lowercase hexadecimal characters")
            hint = _rule_hash_pin_hint(constants)
            if hint:
                r.note(hint)
        elif t is list and not constants[name]:
            r.err(f"INVARIANTS must be a non-empty list of strings")
        elif t is dict and not constants[name]:
            r.warn(f"AXES is empty — generator has no documented free parameters")
    for name, t in optional.items():
        if name in constants:
            v = constants[name]
            if v == "<non-literal>":
                r.warn(f"{name} is not a literal — can't validate type")
            elif not isinstance(v, t):
                r.warn(f"{name} should be {t.__name__}, got {type(v).__name__}")
            elif t is str and v == "":
                r.warn(f"{name} is empty string — refresh via "
                       f"scripts/concept_inventory.py or remove the constant")

    # 2b. AXES domains must be probeable by the override checker's parser.
    # Static, ~microseconds, and it runs BEFORE any expensive gate.
    declared_axes = constants.get("AXES")
    if isinstance(declared_axes, dict) and declared_axes:
        _check_axis_domains(declared_axes, r)

    if len(self_check_nodes) != 1:
        r.err(
            "expected exactly one top-level self_check() definition, "
            f"found {len(self_check_nodes)}"
        )

    # 3. TASK_ID matches dirname
    task_id = constants.get("TASK_ID", "")
    if isinstance(task_id, str):
        expected_dir = task_id.replace(":", "__").replace("/", "__").replace("-", "_")
        # Determine the candidate dirname from the file's parent
        if path.parent.name != expected_dir and path.parent.parent == PER_PUZZLE_DIR:
            r.err(f"TASK_ID={task_id!r} but file is in directory "
                   f"{path.parent.name!r} (expected {expected_dir!r})")

    # 4. CONCEPT_HASH matches canonicalized rule. Only canonicalize when there
    # IS a claimed hash to verify — with a blank hash the (potentially slow)
    # rule canonicalization can prove nothing (reviewer 466).
    claimed_hash = constants.get("CONCEPT_HASH")
    if isinstance(task_id, str) and task_id and isinstance(claimed_hash, str) and claimed_hash:
        try:
            from puzzle_generators.runner import _load_rule
            from scripts.canonicalize_rule import canonicalize_rule
            rule_src, _ = _load_rule(task_id)
            info = canonicalize_rule(rule_src)
            real_hash = info.get("concept_hash")
            if real_hash and claimed_hash != real_hash:
                r.warn(f"CONCEPT_HASH mismatch: claimed {claimed_hash!r}, actual {real_hash!r}")
        except Exception as e:
            r.note(f"could not canonicalize rule for verification: {e}")

    # 5. generate signature
    if not has_generate:
        r.err("missing required function: generate(...)")
    else:
        args = generate_node.args
        # Required positional: seed, sample_index
        pos = [a.arg for a in args.args]
        if pos[:2] != ["seed", "sample_index"]:
            r.err(f"generate() should start with positional args (seed, sample_index), got {pos}")
        # difficulty must be keyword-only
        kw_args = [a.arg for a in args.kwonlyargs]
        if "difficulty" not in kw_args:
            r.warn("generate() should accept `difficulty` as a keyword-only arg")
        if args.kwarg is None or args.kwarg.arg != "overrides":
            r.warn("generate() should accept `**overrides`")

    # 6. No bare random.* usage
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "random":
                    r.err("`import random` not allowed — use ctx.draw_rng(label) instead")
        if isinstance(node, ast.ImportFrom) and node.module == "random":
            r.err("`from random import …` not allowed — use ctx.draw_rng(label)")

    # 7. Preserve suspicious callable/cluster naming warnings without making
    # ordinary isolated local vocabulary a failing lint gate.
    for severity, message in _primitive_name_diagnostics(tree):
        (r.warn if severity == 'warning' else r.note)(message)

    # 8. A failed placement returns None and leaves the grid unchanged. Calls
    # whose result is thrown away can therefore silently omit required
    # objects. A narrow suppression is available only for generators whose
    # immediately following structural postcondition proves the exact object
    # count; the reviewer must document that proof on the call line.
    ignored_placements = _ignored_place_no_overlap_lines(
        tree, src.splitlines()
    )
    for line_number in ignored_placements:
        r.warn(
            "discarded Optional result from place_no_overlap at line "
            f"{line_number}; assign/check the result or document an exact "
            "structural postcondition with "
            f"`# {PLACE_NO_OVERLAP_SUPPRESSION}`"
        )

    # 9. generate() must have at least one return
    if generate_node is not None:
        if not any(isinstance(n, ast.Return) for n in ast.walk(generate_node)):
            r.err("generate() never executes a `return` — must return a grid")

    # 9b. Optional: realized-axis honesty (needs to run the generator).
    if validate and not r.errors and isinstance(declared_axes, dict) and declared_axes:
        try:
            from puzzle_generators.runner import _load_generator_module
            _check_realized_axis_honesty(
                _load_generator_module(str(task_id)), declared_axes, r
            )
        except Exception as e:  # noqa: BLE001 — counted, never silent
            r.warn(
                "axis-honesty probe skipped: "
                f"{type(e).__name__}: {e}"
            )

    # 10. Optional: actually run validation
    if validate and not r.errors:
        try:
            from puzzle_generators.runner import run_batch
            batch = run_batch(task_id, n=20, n_train=4, n_test=1)
            pass_n = len(batch)
            if pass_n >= 18:
                r.note(f"validation: {pass_n}/20 instances passed")
            elif pass_n >= 10:
                r.warn(f"validation: only {pass_n}/20 instances passed")
            else:
                r.err(f"validation FAILED: only {pass_n}/20 instances passed")
        except Exception as e:
            r.err(f"validation crashed: {type(e).__name__}: {e}")

    # 11. Diversity / training-poison gate (only under --validate, after the
    #     rule actually ran). Catches what `--validate` alone cannot: a generator
    #     that is "valid" but feeds the model near-constant outputs (shortcut
    #     poison) or barely transforms its inputs (no-op / wrong-rule). Runs only
    #     here, never in the bulk validate=False path, so it can't trip regen_all.
    if validate and not r.errors:
        try:
            from scripts.gen_diversity_probe import probe_task
            pr = probe_task(task_id, episodes=24, base_seed=0)
            if pr.get("pairs", 0) >= 8:
                uo = pr["uniq_out"]; fi = pr.get("frac_identity", 0.0)
                nd = pr.get("n_distinct_out", round(uo * pr["pairs"]))
                r.note(f"diversity: distinct_out={nd} uniq_out={uo:.0%} "
                       f"frac_identity={fi:.0%} out_shapes={pr['out_shapes']} "
                       f"n_colors={pr['n_colors']}")
                # near-constant output => model learns a constant, not the rule.
                # Use the ABSOLUTE distinct-output count, not the ratio: a
                # counting/classification rule legitimately has a tiny output
                # alphabet (one grid per class) -> low uniq_out RATIO but the
                # output still varies with the input. Only <=2 distinct outputs
                # across the whole probe means the model could learn a constant —
                # UNLESS the generator declares that finite codomain (a binary
                # classifier's whole alphabet IS 2 grids; same contract the
                # defect lint honors via EXPECTED_OUTPUT_CODOMAIN).
                expected_cod = None
                try:
                    from puzzle_generators.runner import _load_generator_module
                    expected_cod = getattr(
                        _load_generator_module(task_id),
                        "EXPECTED_OUTPUT_CODOMAIN",
                        None,
                    )
                except Exception:
                    pass
                if _covers_declared_output_codomain(expected_cod, nd):
                    r.note(f"output alphabet {nd} covers the declared "
                           f"EXPECTED_OUTPUT_CODOMAIN={expected_cod} "
                           f"(finite-state task)")
                elif nd <= 2:
                    r.err(f"POISON: near-constant output ({nd} distinct grids over "
                          f"{pr['pairs']} pairs) — the model would learn a constant; "
                          "for a finite alphabet, justify EXPECTED_OUTPUT_CODOMAIN "
                          "from the selected canonical rule and verify sampled outputs "
                          "cover that entire alphabet; a collapsed sample is not a justification")
                elif uo < 0.35:
                    r.warn(f"low output diversity (uniq_out={uo:.0%}, {nd} distinct) "
                           f"— widen the generator unless the rule's output alphabet "
                           f"is intrinsically small (counting/classification); justify "
                           "EXPECTED_OUTPUT_CODOMAIN from the selected canonical rule "
                           "and verify sampled outputs cover that entire alphabet")
                # rule barely changes the input => no-op / wrong-rule generator
                if fi >= 0.90:
                    r.err(f"POISON: rule is a no-op on {fi:.0%} of generated inputs "
                          f"— likely wrong-rule or degenerate generator")
                elif fi > 0.30:
                    r.warn(f"rule unchanged on {fi:.0%} of inputs — many examples "
                           f"are identity (check the generator matches the rule)")
        except Exception as e:
            r.warn(f"diversity gate skipped: {type(e).__name__}: {e}")

    return r


def _print(r: LintReport, path: Path) -> None:
    if r.errors:
        for m in r.errors: print(f"  {RED}ERR {RESET}{m}")
    if r.warnings:
        for m in r.warnings: print(f"  {YELLOW}WARN{RESET}{m}")
    if r.notes:
        for m in r.notes: print(f"  {GREEN}NOTE{RESET}{m}")
    if not (r.errors or r.warnings):
        print(f"  {GREEN}OK  {RESET}all checks passed")
    print(f"\n{path}: {len(r.errors)} error(s), {len(r.warnings)} warning(s), "
          f"exit {r.exit_code}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="Path to generator.py or a task_id")
    ap.add_argument("--validate", action="store_true",
                    help="Also run 20 instances through the runner")
    args = ap.parse_args()

    # Resolve target → path
    p = Path(args.target)
    if not p.exists() and not args.target.endswith(".py"):
        # treat as task_id
        d = PER_PUZZLE_DIR / args.target.replace(":", "__").replace("/", "__").replace("-", "_")
        p = d / "generator.py"

    print(f"linting {p.relative_to(ROOT) if p.is_relative_to(ROOT) else p}")
    r = lint_generator(p, validate=args.validate)
    _print(r, p)
    return r.exit_code


if __name__ == "__main__":
    sys.exit(main())
