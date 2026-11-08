"""
ARC REPL Executor — S-expression driven, modeled after rack/core.

The model emits S-expressions:
  (feature! "diff pair 0" (diff @1 @2))
  (rule! (pipe (recolor-map {8 7}) (remove-color 1)))
  (test! 0)
  (apply! 0)
  (submit! _1)

The executor parses, evaluates inner expressions, manages artifacts,
and returns formatted ENV output.
"""

import numpy as np
import hashlib
import platform
from collections import Counter
from pathlib import Path

from .parser import parse, Symbol, StrLit
from .evaluator import evaluate, Env, Closure, EvalError
from .builtins import make_global_env, Grid, _unwrap, _wrap
from .registry import (TRANSFORM_REGISTRY, FEATURE_REGISTRY,
                       list_transforms, list_features, help_for, list_categories)
from .templates import TEMPLATE_REGISTRY
from .features import PAIR_FEATURES, GRID_FEATURES, TASK_FEATURES
from .shape import Shape
from .spec import COST_GUARDS


class ArcExecutor:
    """S-expression REPL executor for ARC task solving."""

    def __init__(self, task: dict, auto_scan_on_load: bool = False,
                 use_racket: bool = False):
        self.task = task
        self.use_racket = use_racket

        # Artifact stores
        self._grids = {}       # @N -> Grid
        self._features = {}    # #N -> feature result
        self._results = {}     # _N -> Grid (transform results)
        self._checks = {}      # !N -> bool
        self._objects = {}     # ~N -> object list
        self._notes = {}       # *N -> string
        self._shapes = {}      # $N -> Shape
        self._rules = {}       # &N -> callable (or str name for Racket)

        # Counters
        self._grid_n = 0
        self._feat_n = 0
        self._result_n = 0
        self._check_n = 0
        self._obj_n = 0
        self._note_n = 0
        self._shape_n = 0
        self._rule_n = 0
        self._turns = 0
        self._test_count = 0

        # Rule state
        self._rule_fn = None

        # Snapshots
        self._snapshots = {}
        self._snapshot_n = 0

        # Error log
        self._errors = []

        # Result bookkeeping for faithful scoring / trace replay
        self._result_meta = {}      # _N -> metadata dict
        self._applied_results = {}  # test_idx -> [result refs]
        self._submitted = None      # [[attempt refs for test0], [.. for test1], ...]
        self._last_test_pair = None
        self._last_test_pass = None
        # Machine-readable counterpart to `(test! N)`, populated only from
        # the currently visible training pair.
        self._last_test_detail = None

        # Evaluator environment — Python (legacy) or Racket bridge
        if use_racket:
            from .racket_bridge import RacketBridge
            self._bridge = RacketBridge()
            self._env = None  # Not used in Racket mode
        else:
            self._bridge = None
            self._env = make_global_env()

        # Auto-load grids
        self._auto_load()

        # Wire artifact references into the environment
        self._sync_env()

        # Auto-scan if enabled (inference mode)
        if auto_scan_on_load:
            self._run_auto_scan()

    def close(self):
        """Release any subprocess resources owned by this executor."""
        if self._bridge is not None:
            try:
                self._bridge.shutdown()
            finally:
                self._bridge = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _auto_load(self):
        """Load all training pair grids and test inputs as artifacts."""
        for pair in self.task["train"]:
            self._grid_n += 1
            self._grids[f"@{self._grid_n}"] = Grid(pair["input"])
            self._grid_n += 1
            self._grids[f"@{self._grid_n}"] = Grid(pair["output"])
        for pair in self.task["test"]:
            self._grid_n += 1
            self._grids[f"@{self._grid_n}"] = Grid(pair["input"])

    def _sync_env(self):
        """Push all artifacts into the evaluator environment."""
        if self.use_racket:
            for ref, val in self._grids.items():
                self._bridge.define_grid(ref, _unwrap(val))
            for ref, val in self._results.items():
                if isinstance(val, Grid):
                    self._bridge.define_grid(ref, _unwrap(val))
                else:
                    self._bridge.define_value(ref, val)
            for ref, val in self._features.items():
                if isinstance(val, Grid):
                    self._bridge.define_grid(ref, _unwrap(val))
            for ref, val in self._checks.items():
                self._bridge.define_value(ref, val)
        else:
            for ref, val in self._grids.items():
                self._env.define(ref, val)
            for ref, val in self._features.items():
                self._env.define(ref, val)
            for ref, val in self._results.items():
                self._env.define(ref, val)
            for ref, val in self._objects.items():
                self._env.define(ref, val)
            for ref, val in self._shapes.items():
                self._env.define(ref, val)
            for ref, val in self._checks.items():
                self._env.define(ref, val)
            for ref, val in self._rules.items():
                self._env.define(ref, val)
            # Make task available for task-level features
            self._env.define('_task', self.task)

    def _eval(self, expr):
        """Evaluate an expression in the current environment."""
        if self.use_racket:
            return self._eval_racket(expr)
        return evaluate(expr, self._env)

    def _eval_racket(self, expr):
        """Evaluate an expression via the Racket bridge."""
        from .racket_bridge import RacketBridgeError
        from .security import validate_candidate_expression
        try:
            validate_candidate_expression(expr)
        except ValueError as exc:
            raise EvalError(f"safety: {exc}") from exc
        sexpr_text = self._expr_to_text(expr)
        try:
            result = self._bridge.eval_text(sexpr_text)
        except RacketBridgeError as e:
            raise EvalError(str(e))
        return self._racket_result_to_python(result)

    # For-loop forms that need Racket syntax translation
    _FOR_FORMS = {'for/list', 'for/or', 'for/and', 'for/first', 'for/sum'}

    # Symbol renames for Racket compatibility
    _RACKET_RENAMES = {
        # Operators are now rebound in the Racket namespace directly
        # (see racket_bridge.py boot script)
    }

    def _expr_to_text(self, expr):
        """Convert parsed AST to Racket-compatible S-expression text."""
        if isinstance(expr, Symbol):
            return self._RACKET_RENAMES.get(expr.name, expr.name)
        if isinstance(expr, StrLit):
            return f'"{expr.value}"'
        if isinstance(expr, bool):
            return "#t" if expr else "#f"
        if isinstance(expr, (int, float)):
            return str(expr)
        if isinstance(expr, dict):
            # Convert {k1: v1, k2: v2} to Racket hash
            pairs = " ".join(
                f"(cons {self._expr_to_text(k)} {self._expr_to_text(v)})"
                for k, v in expr.items())
            return f"(make-immutable-hash (list {pairs}))"
        if isinstance(expr, list):
            if not expr:
                return "'()"
            # Check if it's a grid literal (list of lists of ints)
            if (all(isinstance(row, list) for row in expr)
                and all(isinstance(v, (int, float)) for row in expr for v in row)):
                rows = " ".join(
                    "(" + " ".join(str(v) for v in row) + ")"
                    for row in expr)
                return f"'({rows})"
            # Check for for/list, for/or etc. — translate binding syntax
            if (isinstance(expr[0], Symbol)
                and expr[0].name in self._FOR_FORMS
                and len(expr) >= 3
                and isinstance(expr[1], list)
                and len(expr[1]) == 2):
                form = expr[0].name
                var = self._expr_to_text(expr[1][0])
                seq = self._expr_to_text(expr[1][1])
                body = " ".join(self._expr_to_text(e) for e in expr[2:])
                return f"({form} ([{var} (in-list {seq})]) {body})"
            # An empty list is normally data and therefore needs quoting, but
            # in binding/parameter position it is Racket syntax.  Re-emitting
            # `(let ())` as `(let '())` corrupts valid rule bodies before they
            # reach the live bridge (notably the canonical 2b34f380ed25 rule).
            if (isinstance(expr[0], Symbol)
                and expr[0].name in {"let", "let*", "letrec", "lambda"}
                and len(expr) >= 2
                and expr[1] == []):
                head = self._expr_to_text(expr[0])
                tail = " ".join(self._expr_to_text(e) for e in expr[2:])
                return f"({head} (){(' ' + tail) if tail else ''})"
            # Normal list expression
            parts = [self._expr_to_text(e) for e in expr]
            return "(" + " ".join(parts) + ")"
        if isinstance(expr, Grid):
            rows = " ".join(
                "(" + " ".join(str(v) for v in row) + ")"
                for row in _unwrap(expr))
            return f"'({rows})"
        return str(expr)

    def _racket_result_to_python(self, result):
        """Convert Racket JSON result to Python Grid/value."""
        if result is None:
            return None
        if isinstance(result, list) and result and isinstance(result[0], list):
            # Looks like a grid (list of lists of ints)
            if all(isinstance(v, (int, float)) for row in result for v in row):
                return Grid(result)
        return result

    def _store_grid(self, grid):
        """Store a grid and return its ref."""
        self._grid_n += 1
        ref = f"@{self._grid_n}"
        if not isinstance(grid, Grid):
            grid = Grid(grid) if isinstance(grid, list) else grid
        self._grids[ref] = grid
        if self.use_racket:
            self._bridge.define_grid(ref, _unwrap(grid))
        else:
            self._env.define(ref, grid)
        return ref

    def _store_feature(self, result):
        self._feat_n += 1
        ref = f"#{self._feat_n}"
        self._features[ref] = result
        if self.use_racket:
            if isinstance(result, Grid):
                self._bridge.define_grid(ref, _unwrap(result))
        else:
            self._env.define(ref, result)
        return ref

    def _store_result(self, grid, *, meta=None):
        """Store a result as _N. Does NOT create a duplicate @N —
        @N is reserved for immutable dataset artifacts."""
        self._result_n += 1
        ref = f"_{self._result_n}"
        if not isinstance(grid, Grid):
            grid = Grid(grid) if isinstance(grid, list) else grid
        self._results[ref] = grid
        self._result_meta[ref] = dict(meta or {})
        if self.use_racket:
            self._bridge.define_grid(ref, _unwrap(grid))
        else:
            self._env.define(ref, grid)
        return ref

    def _store_check(self, val):
        self._check_n += 1
        ref = f"!{self._check_n}"
        self._checks[ref] = val
        if not self.use_racket:
            self._env.define(ref, val)
        return ref

    # ============================================================
    # Main step
    # ============================================================

    def step(self, command: str) -> str:
        """Process one S-expression command. Returns formatted ENV output."""
        self._turns += 1
        if self._turns > COST_GUARDS["max_turns"]:
            return "ERROR: max turns exceeded"

        try:
            parsed = parse(command.strip())
        except SyntaxError as e:
            return f"ERROR: parse: {e}"

        if parsed is None:
            return "ERROR: empty command"

        # Non-macro expression: just evaluate and show result
        if not isinstance(parsed, list) or not isinstance(parsed[0], Symbol):
            try:
                result = self._eval(parsed)
                return self._compact(result)
            except Exception as e:
                self._errors.append({"turn": self._turns, "error": str(e)})
                return f"ERROR: {e}"

        macro = parsed[0].name
        args = parsed[1:]

        try:
            handler = self._HANDLERS.get(macro)
            if handler:
                return handler(self, args)

            # Not a macro — treat as expression
            result = self._eval(parsed)
            return self._compact(result)

        except Exception as e:
            self._errors.append({"turn": self._turns, "macro": macro, "error": str(e)})
            return f"ERROR: {e}"

    def set_rule(self, fn):
        """Set rule as a Python callable directly."""
        self._rule_fn = fn
        self._rule_n += 1
        ref = f"&{self._rule_n}"
        self._rules[ref] = fn
        self._env.define(ref, fn)

    # ============================================================
    # Macro handlers
    # ============================================================

    def _handle_feature(self, args):
        """(feature! "desc" expr)"""
        desc = self._eval(args[0]) if len(args) > 1 else ""
        expr = args[-1]

        # Task-level features get the task passed in
        if isinstance(expr, list) and isinstance(expr[0], Symbol):
            fname = expr[0].name.replace("-", "_")
            if fname in TASK_FEATURES:
                result = TASK_FEATURES[fname](self.task)
                ref = self._store_feature(result)
                return f"{ref} = {self._compact(result)} \u2014 Feature: {desc}"
            if fname in PAIR_FEATURES:
                eval_args = [_unwrap(self._eval(a)) for a in expr[1:]]
                result = PAIR_FEATURES[fname](*eval_args)
                ref = self._store_feature(result)
                return f"{ref} = {self._compact(result)} \u2014 Feature: {desc}"
            if fname in GRID_FEATURES:
                eval_args = [_unwrap(self._eval(a)) for a in expr[1:]]
                result = GRID_FEATURES[fname](*eval_args)
                ref = self._store_feature(result)
                return f"{ref} = {self._compact(result)} \u2014 Feature: {desc}"

        result = self._eval(expr)
        ref = self._store_feature(result)
        return f"{ref} = {self._compact(result)} \u2014 Feature: {desc}"

    def _handle_observe(self, args):
        """(observe! "text")"""
        text = self._eval(args[0]) if args else ""
        if isinstance(text, StrLit):
            text = text.value
        self._note_n += 1
        ref = f"*{self._note_n}"
        self._notes[ref] = str(text)
        if not self.use_racket:
            self._env.define(ref, str(text))
        else:
            self._bridge.define_value(ref, str(text))
        return f"{ref} \u2192 {text}"

    def _handle_objects(self, args):
        """(objects! grid-ref)"""
        grid = self._eval(args[0])
        from .grid_ops import find_objects
        objs = find_objects(_unwrap(grid))
        self._obj_n += 1
        ref = f"~{self._obj_n}"
        self._objects[ref] = objs
        if not self.use_racket:
            self._env.define(ref, objs)
        summary = ", ".join(f"c{o['color']}({o['size']}px)" for o in objs[:8])
        if len(objs) > 8:
            summary += f" +{len(objs)-8}"
        return f"{ref} = {len(objs)} objects: {summary}"

    def _handle_inspect(self, args):
        """(inspect! ref [r1 c1 r2 c2])"""
        grid = self._eval(args[0])
        g = np.array(_unwrap(grid))
        if len(args) == 5:
            r1, c1 = self._eval(args[1]), self._eval(args[2])
            r2, c2 = self._eval(args[3]), self._eval(args[4])
            sub = g[r1:r2+1, c1:c2+1]
            lines = [f"region [{r1}:{r2+1}, {c1}:{c2+1}] {list(sub.shape)}"]
            for row in sub:
                lines.append(" ".join(f"{v:2d}" for v in row))
            return "\n".join(lines)
        return f"shape={list(g.shape)}, colors={sorted(set(g.flatten().tolist()))}"

    def _handle_compare(self, args):
        """(compare! ref1 ref2)"""
        a = np.array(_unwrap(self._eval(args[0])))
        b = np.array(_unwrap(self._eval(args[1])))
        if a.shape != b.shape:
            return f"shape mismatch: {list(a.shape)} vs {list(b.shape)}"
        n = int((a != b).sum())
        return f"{n}/{a.size} cells differ ({round(100*n/a.size) if a.size else 0}%)"

    def _handle_show(self, args):
        """(show! ref [r1 c1 r2 c2])"""
        grid = self._eval(args[0])
        g = np.array(_unwrap(grid))
        if len(args) == 5:
            r1, c1 = self._eval(args[1]), self._eval(args[2])
            r2, c2 = self._eval(args[3]), self._eval(args[4])
            g = g[r1:r2+1, c1:c2+1]
        lines = [f"{list(g.shape)}"]
        for row in g:
            lines.append(" ".join(f"{v:2d}" for v in row))
        return "\n".join(lines)

    def _handle_diff(self, args):
        """(diff! ref1 ref2)"""
        a = np.array(_unwrap(self._eval(args[0])))
        b = np.array(_unwrap(self._eval(args[1])))
        if a.shape != b.shape:
            return f"shape mismatch: {list(a.shape)} vs {list(b.shape)}"
        mask = a != b
        n = int(mask.sum())
        if n == 0:
            return "IDENTICAL"
        rows, cols = np.where(mask)
        bbox = f"rows {rows.min()}-{rows.max()}, cols {cols.min()}-{cols.max()}"
        trans = Counter((int(a[r, c]), int(b[r, c])) for r, c in zip(rows, cols))
        trans_str = ", ".join(f"{k[0]}\u2192{k[1]}:{v}" for k, v in trans.most_common(5))
        h = min(a.shape[0], 15)
        vis = []
        for r in range(h):
            vis.append(" ".join("X" if mask[r, c] else "." for c in range(a.shape[1])))
        lines = [f"{n}/{a.size} cells differ", f"  region: {bbox}",
                 f"  transitions: {trans_str}", "  visual:"] + ["  " + v for v in vis]
        return "\n".join(lines)

    def _handle_diagnose(self, args):
        """(diagnose! [pair-index]) — compact task or pair diagnostics."""
        if args:
            pair_idx = self._eval(args[0])
            return "\n".join(self._diagnose_pair(pair_idx, detail=True))

        n_train = len(self.task.get("train", []))
        n_test = len(self.task.get("test", []))
        lines = [f"Task diagnostics: {n_train} train pair(s), {n_test} test input(s)"]

        train_shapes = []
        for pair in self.task.get("train", []):
            inp = np.array(pair["input"])
            out = np.array(pair["output"]) if "output" in pair else None
            in_shape = f"{inp.shape[0]}x{inp.shape[1]}"
            out_shape = f"{out.shape[0]}x{out.shape[1]}" if out is not None else "?"
            train_shapes.append(f"{in_shape}->{out_shape}")
        if train_shapes:
            lines.append(f"  train shapes: {', '.join(train_shapes)}")

        test_shapes = []
        for pair in self.task.get("test", []):
            inp = np.array(pair["input"])
            test_shapes.append(f"{inp.shape[0]}x{inp.shape[1]}")
        if test_shapes:
            lines.append(f"  test input shapes: {', '.join(test_shapes)}")

        role_lines = self._task_color_role_lines()
        if role_lines:
            lines.append("  color roles across train:")
            lines.extend(f"    {line}" for line in role_lines)

        for i in range(n_train):
            lines.extend(self._diagnose_pair(i, detail=False))

        lines.append("  next: use (diagnose! N) for pair detail, (render! task), or (render! pair N)")
        return "\n".join(lines)

    def _handle_render(self, args):
        """(render! [task|pair|diff] [pair-index]) — save a PNG under /tmp."""
        from .render import task_image, pair_image, diff_image

        kind = "task"
        if args:
            if isinstance(args[0], Symbol):
                kind = args[0].name
            else:
                kind = str(self._eval(args[0]))

        out_dir = Path("/tmp")
        if kind == "task":
            path = out_dir / "arc_repl_task.png"
            task_image(self.task, cell_size=14).save(path)
            return f"rendered task -> {path}"

        if len(args) < 2:
            pair_idx = 0
        else:
            pair_idx = self._eval(args[1])
        if pair_idx >= len(self.task.get("train", [])):
            return f"ERROR: pair {pair_idx} out of range ({len(self.task.get('train', []))} pairs)"

        pair = self.task["train"][pair_idx]
        if kind == "pair":
            path = out_dir / f"arc_repl_pair_{pair_idx}.png"
            pair_image(pair["input"], pair["output"], cell_size=16).save(path)
            return f"rendered pair {pair_idx} -> {path}"

        if kind == "diff":
            if self._rule_fn is None:
                return "ERROR: no rule set. Use (rule! ...) before (render! diff N)."
            try:
                got = _unwrap(self._apply_rule(Grid(pair["input"])))
            except Exception as e:
                return f"ERROR: rule error while rendering diff: {e}"
            path = out_dir / f"arc_repl_diff_{pair_idx}.png"
            diff_image(got, pair["output"], cell_size=16).save(path)
            return f"rendered rule diff for pair {pair_idx} -> {path}"

        return "ERROR: render! kind must be task, pair, or diff"

    def _handle_transform(self, args):
        """(transform! "desc" expr)"""
        desc = self._eval(args[0]) if len(args) > 1 else ""
        result = self._eval(args[-1])
        if isinstance(result, Grid):
            ref = self._store_result(result, meta={"kind": "transform", "desc": str(desc)})
            return f"{ref} = Grid({result.height}x{result.width}) \u2014 Transform: {desc}"
        ref = self._store_result(result, meta={"kind": "transform", "desc": str(desc)})
        return f"{ref} = {self._compact(result)}"

    # Heads whose value is already a callable (grid → grid). `rule!`
    # leaves these untouched. Anything else is treated as a BODY using
    # the auto-bound names g, h, w (see _handle_rule).
    _RULE_CALLABLE_HEADS = frozenset({
        "lambda", "pipe", "compose", "fork", "power",
    })

    @staticmethod
    def _rule_arg_head(expr):
        """Return the first symbol of a parsed S-expression list, or
        None if the expr is a bare symbol / atom."""
        if isinstance(expr, list) and expr and isinstance(expr[0], Symbol):
            return expr[0].name
        return None

    def _handle_rule(self, args):
        """(rule! expr) — expr is either:
          * a callable-producing form (lambda / pipe / compose / fork /
            power / a bare symbol bound to a function), or
          * a BODY expression that uses the auto-bound names `g`, `h`,
            `w`. Body form is the canonical post-cleanup shape.

        Auto-binding fires for body form and for lambda forms that close over
        the conventional free names h/w.  Other callable forms are passed
        through unchanged.  Binding h/w in an enclosing scope is semantics-
        preserving for existing lambdas that do not reference them, and fixes
        the corpus lambdas that do.
        """
        if len(args) != 1:
            return "ERROR: safety: rule! requires exactly one expression"
        from .security import validate_candidate_expression
        try:
            validate_candidate_expression(args[0])
        except ValueError as exc:
            return f"ERROR: safety: {exc}"
        if self.use_racket:
            self._rule_n += 1
            rule_name = f"__arc_rule_{self._rule_n}"
            head = self._rule_arg_head(args[0])
            sexpr = self._expr_to_text(args[0])
            is_lambda_form = head in {"lambda", "λ"}
            is_callable_form = (
                isinstance(args[0], Symbol)
                or (head in self._RULE_CALLABLE_HEADS)
            )
            if is_lambda_form:
                # A legacy `(lambda (g) ...)` may refer to h/w as free vars
                # under the rule! g/h/w convention.  When replaying through a
                # bare bridge, bind h/w in the lambda's lexical closure and
                # then apply the lambda to the actual grid.
                wrapped = (
                    f"(lambda (g) "
                    f"(let* ((h (rows g)) (w (cols g))) "
                    f"({sexpr} g)))"
                )
            elif is_callable_form:
                wrapped = sexpr
            else:
                # Body form: wrap with the auto-bind preamble. We only
                # bind g/h/w by default — `bg` is intentionally NOT
                # auto-bound because the semantic background is task-
                # specific (sometimes 0, sometimes mode, sometimes the
                # frame color). Add other bindings only when the body
                # asks for them via local let.
                wrapped = (
                    f"(lambda (g) "
                    f"(let* ((h (rows g)) (w (cols g))) "
                    f"{sexpr}))"
                )
            try:
                self._bridge.eval_text(f"(define {rule_name} {wrapped})")
            except Exception as e:
                return f"ERROR: {e}"
            self._rule_fn = rule_name
            ref = f"&{self._rule_n}"
            self._rules[ref] = rule_name
            return f"{ref} = rule set. Use (test! N) to verify."
        else:
            # Python evaluator (legacy fallback). Mirror the Racket-side
            # auto-bind: if the user passed a body expression rather
            # than a callable form, wrap it in a synthetic lambda that
            # auto-binds g, h, w before evaluation.
            head = self._rule_arg_head(args[0])
            is_lambda_form = head in {"lambda", "λ"}
            is_callable_form = (
                isinstance(args[0], Symbol)
                or (head in self._RULE_CALLABLE_HEADS)
            )
            if is_lambda_form:
                rule_expr = [
                    Symbol("lambda"), [Symbol("g")],
                    [Symbol("let*"),
                     [[Symbol("h"), [Symbol("rows"), Symbol("g")]],
                      [Symbol("w"), [Symbol("cols"), Symbol("g")]]],
                     [args[0], Symbol("g")]],
                ]
            elif is_callable_form:
                rule_expr = args[0]
            else:
                rule_expr = [
                    Symbol("lambda"), [Symbol("g")],
                    [Symbol("let*"),
                     [[Symbol("h"), [Symbol("rows"), Symbol("g")]],
                      [Symbol("w"), [Symbol("cols"), Symbol("g")]]],
                     args[0]],
                ]
            fn = self._eval(rule_expr)
            if not callable(fn) and not isinstance(fn, Closure):
                return "ERROR: rule! expression must evaluate to a callable"
            self._rule_fn = fn
            self._rule_n += 1
            ref = f"&{self._rule_n}"
            self._rules[ref] = fn
            self._env.define(ref, fn)
            return f"{ref} = rule set. Use (test! N) to verify."

    def _handle_template(self, args):
        """(template! name args...)"""
        name = args[0].name if isinstance(args[0], Symbol) else str(self._eval(args[0]))
        if name not in TEMPLATE_REGISTRY:
            return f"ERROR: unknown template '{name}'. Try (list! templates)"
        factory = TEMPLATE_REGISTRY[name]
        eval_args = [self._eval(a) for a in args[1:]]
        if not eval_args:
            fn = factory()
        elif len(eval_args) == 1:
            fn = factory(eval_args[0])
        else:
            fn = factory(*eval_args)
        # Wrap to handle Grid
        raw_fn = fn
        def wrapped(grid):
            return _wrap(raw_fn(_unwrap(grid)))
        self._rule_fn = wrapped
        self._rule_n += 1
        ref = f"&{self._rule_n}"
        self._rules[ref] = wrapped
        self._env.define(ref, wrapped)
        return f"{ref} = rule via template: {name}. Use (test! N) to verify."

    def _handle_test(self, args):
        """(test! pair-index)"""
        self._test_count += 1
        self._last_test_pair = None
        self._last_test_pass = None
        self._last_test_detail = None
        if self._test_count > COST_GUARDS["max_test_pairs"]:
            return "ERROR: max test! calls exceeded"
        pair_idx = self._eval(args[0]) if args else 0
        if pair_idx >= len(self.task["train"]):
            return f"ERROR: pair {pair_idx} out of range ({len(self.task['train'])} pairs)"
        if self._rule_fn is None:
            return "ERROR: no rule set. Use (rule! ...) or (template! ...) first."

        pair = self.task["train"][pair_idx]
        inp = Grid(pair["input"])
        expected = pair["output"]

        try:
            result = self._apply_rule(inp)
        except Exception as e:
            self._last_test_pair = pair_idx
            self._last_test_pass = False
            self._last_test_detail = {
                "kind": "runtime",
                "pair_index": int(pair_idx),
                "message": str(e),
            }
            ref = self._store_check(False)
            return f"{ref} = FAIL \u2014 pair {pair_idx}: rule error: {e}"

        got = _unwrap(result)
        passed = (got == expected)
        self._last_test_pair = pair_idx
        self._last_test_pass = passed
        ref = self._store_check(passed)

        if passed:
            height = len(expected)
            width = len(expected[0]) if height else 0
            self._last_test_detail = {
                "kind": "demo_diff",
                "pair_index": int(pair_idx),
                "match": True,
                "actual_shape": [height, width],
                "expected_shape": [height, width],
                "differing_cells": 0,
                "total_cells": height * width,
                "region": None,
                "color_deltas": [],
                "recolors": [],
            }
            return f"{ref} = PASS \u2014 pair {pair_idx} matches"

        ga, ea = np.array(got), np.array(expected)
        if ga.shape != ea.shape:
            self._last_test_detail = {
                "kind": "demo_diff",
                "pair_index": int(pair_idx),
                "match": False,
                "actual_shape": [int(value) for value in ga.shape],
                "expected_shape": [int(value) for value in ea.shape],
                "differing_cells": None,
                "total_cells": int(ea.size),
                "region": None,
                "color_deltas": [],
                "recolors": [],
            }
            return f"{ref} = FAIL \u2014 pair {pair_idx}: shape {list(ga.shape)} vs {list(ea.shape)}"

        mask = ga != ea
        n = int(mask.sum())
        rows, cols = np.where(mask)
        bbox = f"rows {int(rows.min())}-{int(rows.max())}, cols {int(cols.min())}-{int(cols.max())}"

        # Layer-aware diff: show per-color changes
        layer_lines = []
        color_deltas = []
        all_colors = sorted(set(ga.flatten().tolist()) | set(ea.flatten().tolist()))
        for color in all_colors:
            got_cells = set(zip(*np.where(ga == color))) if (ga == color).any() else set()
            exp_cells = set(zip(*np.where(ea == color))) if (ea == color).any() else set()
            added = exp_cells - got_cells
            removed = got_cells - exp_cells
            if not added and not removed:
                continue  # invariant layer — skip
            parts = []
            if removed:
                parts.append(f"-{len(removed)}")
            if added:
                parts.append(f"+{len(added)}")
                # Show WHERE (up to 5 positions)
                sample = sorted(added)[:5]
                pos_str = ",".join(f"({r},{c})" for r, c in sample)
                if len(added) > 5:
                    pos_str += "..."
                parts.append(f"at {pos_str}")
            layer_lines.append(f"  color {color}: {' '.join(parts)}")
            color_deltas.append({
                "color": int(color),
                "surplus_in_prediction": len(removed),
                "deficit_in_prediction": len(added),
                "expected_not_predicted_sample": [
                    [int(r), int(c)] for r, c in sorted(added)[:5]
                ],
            })

        # Detect recolor pattern: if one color lost N cells and another gained same N
        trans = Counter((int(ga[r, c]), int(ea[r, c])) for r, c in zip(rows, cols))
        recolor_hints = []
        recolors = []
        for (src, dst), count in trans.most_common(5):
            if count >= 2:
                recolor_hints.append(f"{src}→{dst}({count})")
                recolors.append({
                    "from": int(src),
                    "to": int(dst),
                    "count": int(count),
                })

        self._last_test_detail = {
            "kind": "demo_diff",
            "pair_index": int(pair_idx),
            "match": False,
            "actual_shape": [int(value) for value in ga.shape],
            "expected_shape": [int(value) for value in ea.shape],
            "differing_cells": n,
            "total_cells": int(ga.size),
            "region": {
                "rows": [int(rows.min()), int(rows.max())],
                "cols": [int(cols.min()), int(cols.max())],
            },
            "color_deltas": color_deltas,
            "recolors": recolors,
        }

        lines = [f"{ref} = FAIL \u2014 pair {pair_idx}: {n}/{ga.size} differ"]
        lines.append(f"  region: {bbox}")
        if layer_lines:
            lines.extend(layer_lines)
        if recolor_hints:
            lines.append(f"  recolors: {', '.join(recolor_hints)}")
        return "\n".join(lines)

    def _handle_test_all(self, args):
        """(test-all!) — test rule on ALL training pairs in one turn."""
        if self._rule_fn is None:
            return "ERROR: no rule set."
        results = []
        all_pass = True
        for i in range(len(self.task["train"])):
            obs = self._handle_test([i])
            passed = "PASS" in obs
            results.append(f"pair {i}: {'PASS' if passed else 'FAIL'}")
            if not passed:
                all_pass = False
        summary = f"{'ALL PASS' if all_pass else 'SOME FAILED'} ({sum(1 for r in results if 'PASS' in r)}/{len(results)})"
        return summary + "\n  " + "\n  ".join(results)

    def _handle_test_until_fail(self, args):
        """(test-until-fail!) — test pairs sequentially, stop at first failure."""
        if self._rule_fn is None:
            return "ERROR: no rule set."
        for i in range(len(self.task["train"])):
            obs = self._handle_test([i])
            if "FAIL" in obs:
                return f"STOPPED at pair {i}/{len(self.task['train'])}\n  {obs}"
        return f"ALL {len(self.task['train'])} PAIRS PASS"

    def _handle_verify(self, args):
        """(verify! expr)"""
        result = self._eval(args[0])
        ref = self._store_check(bool(result))
        return f"{ref} = {result}"

    def _handle_apply(self, args):
        """(apply! test-index)"""
        test_idx = self._eval(args[0]) if args else 0
        if test_idx >= len(self.task["test"]):
            return f"ERROR: test {test_idx} out of range"
        if self._rule_fn is None:
            return "ERROR: no rule set."

        inp = Grid(self.task["test"][test_idx]["input"])
        result = self._apply_rule(inp)
        attempt_n = len(self._applied_results.get(test_idx, [])) + 1
        ref = self._store_result(
            result,
            meta={"kind": "apply", "test_idx": test_idx, "attempt": attempt_n},
        )
        self._applied_results.setdefault(test_idx, []).append(ref)
        g = _unwrap(result)
        h = len(g)
        w = len(g[0]) if g else 0
        return f"{ref} = Grid({h}x{w}) \u2014 applied rule to test {test_idx} (attempt {attempt_n})"

    def _result_ref_from_arg(self, arg):
        """Resolve a submit! argument to a result ref like _1."""
        if isinstance(arg, Symbol) and arg.name in self._results:
            return arg.name
        val = self._eval(arg)
        if isinstance(val, Grid):
            for ref, grid in self._results.items():
                if grid is val or _unwrap(grid) == _unwrap(val):
                    return ref
        raise EvalError("submit! expects result refs like _1, _2, ...")

    def _handle_submit(self, args):
        """(submit! _1 [_2 ...]) — expects results in test order.

        Backward-compatible mode:
          len(args) == n_tests      -> duplicate each ref into both attempts
          len(args) == 2 * n_tests  -> pass@2 mode (two refs per test input)

        For n test inputs, refs are interpreted in test order:
          (submit! _1 _2 _3 _4)  => test0:[_1,_2], test1:[_3,_4]
        """
        n_tests = len(self.task["test"])
        if n_tests == 0:
            self._submitted = []
            return "SUBMITTED 0 test input(s)"

        refs = [self._result_ref_from_arg(a) for a in args]
        if len(refs) not in (n_tests, 2 * n_tests):
            return (f"ERROR: submit! expects {n_tests} ref(s) for single-attempt "
                    f"mode or {2 * n_tests} ref(s) for pass@2 mode; got {len(refs)}")

        if len(refs) == n_tests:
            groups = [[ref, ref] for ref in refs]
            attempts_each = 1
        else:
            groups = [refs[i * 2:(i + 1) * 2] for i in range(n_tests)]
            attempts_each = 2

        self._submitted = groups
        return (f"SUBMITTED {n_tests} test input(s), "
                f"{attempts_each} attempt(s) each")

    def _handle_compose(self, args):
        """(compose! expr1 expr2 ...) — compose transforms into a rule."""
        fns = [self._eval(a) for a in args]
        def composed(grid):
            result = grid
            for fn in fns:
                result = fn(result)
            return result
        self._rule_fn = composed
        self._rule_n += 1
        ref = f"&{self._rule_n}"
        self._rules[ref] = composed
        self._env.define(ref, composed)
        return f"{ref} = composed {len(fns)} transforms into rule."

    def _handle_shape(self, args):
        """(shape! subcommand ...)"""
        sub = args[0].name if isinstance(args[0], Symbol) else str(self._eval(args[0]))
        if sub == "extract":
            grid = self._eval(args[1])
            objs = self._eval(args[2])
            idx = self._eval(args[3]) if len(args) > 3 else 0
            shape = Shape.from_object(_unwrap(grid), objs[idx])
            self._shape_n += 1
            ref = f"${self._shape_n}"
            self._shapes[ref] = shape
            self._env.define(ref, shape)
            return f"{ref} = {shape}"
        elif sub == "show":
            shape = self._eval(args[1])
            g = shape.as_grid()
            lines = [str(shape)]
            for row in g:
                lines.append(" ".join(f"{v:2d}" if v else " ." for v in row))
            return "\n".join(lines)
        elif sub == "upscale":
            shape = self._eval(args[1])
            factor = self._eval(args[2])
            new_shape = shape.upscale(factor)
            self._shape_n += 1
            ref = f"${self._shape_n}"
            self._shapes[ref] = new_shape
            self._env.define(ref, new_shape)
            return f"{ref} = {new_shape}"
        elif sub == "place":
            shape = self._eval(args[1])
            grid = self._eval(args[2])
            r, c = self._eval(args[3]), self._eval(args[4])
            result = Grid(shape.place(_unwrap(grid), r, c))
            ref = self._store_result(result)
            return f"{ref} = Grid({result.height}x{result.width}) \u2014 placed shape at ({r},{c})"
        return f"ERROR: unknown shape subcommand '{sub}'"

    def _handle_undo(self, args):
        """(undo!)"""
        self._rule_fn = None
        return "Rule cleared."

    def _handle_reset_rule(self, args):
        """(reset-rule!)"""
        self._rule_fn = None
        return "Rule cleared."

    def _handle_list(self, args):
        """(list! [kind] [category])"""
        if not args:
            return list_categories() + "\nUse: (list! transforms [cat]) | (list! features [level]) | (list! templates)"
        kind = args[0].name if isinstance(args[0], Symbol) else str(self._eval(args[0]))
        sub = args[1].name if len(args) > 1 and isinstance(args[1], Symbol) else (str(self._eval(args[1])) if len(args) > 1 else None)
        if kind == "transforms":
            return list_transforms(sub)
        elif kind == "features":
            return list_features(sub)
        elif kind == "templates":
            lines = ["=== TEMPLATES ==="]
            for name, fn in sorted(TEMPLATE_REGISTRY.items()):
                doc = (fn.__doc__ or "").strip().split("\n")[0]
                lines.append(f"  {name:<25s} {doc}")
            return "\n".join(lines)
        return f"Unknown kind: {kind}"

    def _handle_help(self, args):
        """(help! [name])"""
        if not args:
            return ("Macros: (feature!) (observe!) (objects!) (inspect!) (compare!) (show!) (diff!)\n"
                    "  (diagnose!) (render!)\n"
                    "  (transform!) (rule!) (template!) (test!) (verify!) (compose!) (shape!)\n"
                    "  (apply!) (submit!) (undo!) (reset-rule!) (list!) (help!)\n"
                    "  (auto-scan!) (suggest!) (status!) (snapshot!) (restore!)\n"
                    "Try: (list! transforms) | (list! features) | (list! templates)")
        name = args[0].name if isinstance(args[0], Symbol) else str(self._eval(args[0]))
        # help_for handles both kebab-case and snake_case lookups internally
        return help_for(name)

    def _handle_auto_scan(self, args):
        """(auto-scan!)"""
        return self._run_auto_scan()

    def _handle_suggest(self, args):
        """(suggest!)"""
        from .auto_scan import suggest
        sugs = suggest(self.task)
        if not sugs:
            return "No suggestions available."
        lines = ["Candidates:"]
        for i, (expr, conf, desc) in enumerate(sugs[:5]):
            lines.append(f"  [{i+1}] {desc} ({conf:.2f}): {expr}")
        return "\n".join(lines)

    def _handle_snapshot(self, args):
        """(snapshot! [name]) / (save-rule! [name]) — saves current rule only.
        Does NOT save full session state (results, objects, etc.)."""
        self._snapshot_n += 1
        name = str(self._eval(args[0])) if args else f"snap_{self._snapshot_n}"
        if isinstance(name, StrLit):
            name = name.value
        self._snapshots[name] = {
            "rule_fn": self._rule_fn,
        }
        return f"Rule saved as '{name}'. ({len(self._snapshots)} saved)"

    def _handle_restore(self, args):
        """(restore! name) / (load-rule! name) — restores a saved rule."""
        name = str(self._eval(args[0])) if args else ""
        if isinstance(name, StrLit):
            name = name.value
        if name not in self._snapshots:
            return f"ERROR: no saved rule '{name}'. Have: {', '.join(self._snapshots.keys())}"
        snap = self._snapshots[name]
        self._rule_fn = snap["rule_fn"]
        return f"Loaded rule '{name}'."

    def _handle_status(self, args):
        """(status!)"""
        passes = sum(1 for v in self._checks.values() if v)
        fails = sum(1 for v in self._checks.values() if not v)
        applied = sum(len(v) for v in self._applied_results.values())
        submitted = 0 if self._submitted is None else sum(len(v) for v in self._submitted)
        lines = [
            f"Turns: {self._turns}/{COST_GUARDS['max_turns']}",
            f"Grids: {len(self._grids)} | Features: {len(self._features)} | Results: {len(self._results)}",
            f"Objects: {len(self._objects)} | Shapes: {len(self._shapes)} | Rules: {len(self._rules)}",
            f"Rule: {'set' if self._rule_fn else 'none'}",
            f"Tests: {passes} pass, {fails} fail" if self._checks else "Tests: none",
            f"Applied results: {applied} | Submitted refs: {submitted}",
            f"Snapshots: {len(self._snapshots)} | Errors: {len(self._errors)}",
        ]
        return "\n".join(lines)

    # ============================================================
    # Fast feedback — try ideas without committing to a rule
    # ============================================================

    def _handle_try(self, args):
        """(try! expr [pair-idx])
        Apply expr (a lambda or function) to a training input, compare to expected output.
        Does NOT set a rule — lets you test ideas quickly.
        """
        fn = self._eval(args[0])
        pair_idx = self._eval(args[1]) if len(args) > 1 else 0

        if pair_idx >= len(self.task["train"]):
            return f"ERROR: pair {pair_idx} out of range"

        pair = self.task["train"][pair_idx]
        inp = Grid(pair["input"])
        expected = pair["output"]

        try:
            if isinstance(fn, Closure):
                from .evaluator import apply_fn
                result = apply_fn(fn, [inp], fn.env)
            else:
                result = fn(inp)
        except Exception as e:
            return f"TRY pair {pair_idx}: ERROR — {e}"

        got = _unwrap(result)

        if got == expected:
            return f"TRY pair {pair_idx}: MATCH ✓"

        ga, ea = np.array(got), np.array(expected) if isinstance(got, list) else (np.array(got), np.array(expected))
        if ga.shape != ea.shape:
            gh, gw = ga.shape
            eh, ew = ea.shape
            return f"TRY pair {pair_idx}: WRONG SIZE — got {gh}x{gw}, want {eh}x{ew}"

        mask = ga != ea
        n = int(mask.sum())
        total = int(ga.size)
        pct = 100 * n / total if total > 0 else 0
        trans = Counter((int(ga[r, c]), int(ea[r, c])) for r, c in zip(*np.where(mask)))
        trans_str = ", ".join(f"{k[0]}→{k[1]}({v})" for k, v in trans.most_common(5))
        return f"TRY pair {pair_idx}: {n}/{total} wrong ({pct:.0f}%) — {trans_str}"

    def _handle_try_all(self, args):
        """(try-all! expr)
        Try expr on ALL training pairs. Quick way to see how well an idea works.
        """
        fn = self._eval(args[0])
        results = []
        matches = 0
        for i in range(len(self.task["train"])):
            pair = self.task["train"][i]
            inp = Grid(pair["input"])
            expected = pair["output"]
            try:
                if isinstance(fn, Closure):
                    from .evaluator import apply_fn
                    result = apply_fn(fn, [inp], fn.env)
                else:
                    result = fn(inp)
                got = _unwrap(result)
                if got == expected:
                    matches += 1
                    results.append(f"pair {i}: MATCH ✓")
                else:
                    ga, ea = np.array(got), np.array(expected)
                    if ga.shape != ea.shape:
                        gh, gw = ga.shape
                        eh, ew = ea.shape
                        results.append(f"pair {i}: WRONG SIZE {gh}x{gw} vs {eh}x{ew}")
                    else:
                        n = int((ga != ea).sum())
                        results.append(f"pair {i}: {n}/{ga.size} wrong")
            except Exception as e:
                results.append(f"pair {i}: ERROR — {e}")

        header = f"{matches}/{len(self.task['train'])} match"
        return header + "\n  " + "\n  ".join(results)

    def _handle_peek(self, args):
        """(peek! expr [pair-idx])
        Evaluate expr on a training input and show summary (size, colors, nonzero count).
        Useful for debugging intermediate steps.
        """
        expr_result = self._eval(args[0])
        # If it's a function, apply to training pair
        if isinstance(expr_result, (Closure,)) or callable(expr_result):
            pair_idx = self._eval(args[1]) if len(args) > 1 else 0
            inp = Grid(self.task["train"][pair_idx]["input"])
            try:
                if isinstance(expr_result, Closure):
                    from .evaluator import apply_fn
                    result = apply_fn(expr_result, [inp], expr_result.env)
                else:
                    result = expr_result(inp)
            except Exception as e:
                return f"PEEK: ERROR — {e}"
        else:
            result = expr_result

        if isinstance(result, Grid):
            data = _unwrap(result)
            h, w = len(data), len(data[0])
            colors = sorted(set(v for row in data for v in row))
            nonzero = sum(1 for row in data for v in row if v != 0)
            return f"PEEK: Grid({h}x{w}) colors={colors} nonzero={nonzero}/{h*w}"
        else:
            return f"PEEK: {self._compact(result)}"

    # ============================================================
    # Rule application
    # ============================================================

    def _apply_rule(self, grid):
        """Apply current rule to a grid."""
        if self._rule_fn is None:
            raise EvalError("No rule set")

        if self.use_racket and isinstance(self._rule_fn, str):
            # Racket mode: rule_fn is a string (Racket binding name)
            from .racket_bridge import RacketBridgeError
            # Define the input grid in Racket, call the rule
            self._bridge.define_grid("__arc_input__", _unwrap(grid))
            try:
                result = self._bridge.eval_text(f"({self._rule_fn} __arc_input__)")
            except RacketBridgeError as e:
                raise EvalError(str(e))
            return self._racket_result_to_python(result)
        elif isinstance(self._rule_fn, Closure):
            from .evaluator import apply_fn
            result = apply_fn(self._rule_fn, [grid], self._rule_fn.env)
        else:
            result = self._rule_fn(grid)
        return result

    # ============================================================
    # Helpers
    # ============================================================

    def _compact(self, val, max_len=200):
        """Compact display of a value."""
        if isinstance(val, Grid):
            return f"Grid({val.height}x{val.width})"
        if isinstance(val, Shape):
            return str(val)
        if isinstance(val, Closure):
            return repr(val)
        if isinstance(val, StrLit):
            return f'"{val.value}"'
        s = str(val)
        if len(s) > max_len:
            return s[:max_len] + "..."
        return s

    def _format_counts(self, values, max_items=10):
        counts = Counter(int(v) for v in values)
        items = sorted(counts.items())
        if len(items) > max_items:
            shown = items[:max_items]
            rest = sum(v for _, v in items[max_items:])
            return " ".join(f"{k}:{v}" for k, v in shown) + f" +{rest} cells"
        return " ".join(f"{k}:{v}" for k, v in items)

    def _format_counter(self, counter, max_items=6):
        if not counter:
            return "none"
        parts = []
        for key, count in counter.most_common(max_items):
            if isinstance(key, tuple) and len(key) == 2:
                parts.append(f"{key[0]}->{key[1]}({count})")
            else:
                parts.append(f"{key}({count})")
        if len(counter) > max_items:
            parts.append(f"+{len(counter) - max_items} more")
        return ", ".join(parts)

    def _bbox_from_cells(self, cells):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        return int(min(rs)), int(min(cs)), int(max(rs)), int(max(cs))

    def _bbox_text(self, cells_or_bbox):
        if not cells_or_bbox:
            return "none"
        if len(cells_or_bbox) == 4 and all(isinstance(v, (int, np.integer)) for v in cells_or_bbox):
            r1, c1, r2, c2 = cells_or_bbox
        else:
            r1, c1, r2, c2 = self._bbox_from_cells(cells_or_bbox)
        return f"r{int(r1)}-{int(r2)} c{int(c1)}-{int(c2)}"

    def _mask_components(self, mask, connectivity=8):
        mask = np.array(mask, dtype=bool)
        h, w = mask.shape
        seen = np.zeros_like(mask, dtype=bool)
        if connectivity == 4:
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        else:
            deltas = [
                (dr, dc)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            ]
        comps = []
        for r in range(h):
            for c in range(w):
                if seen[r, c] or not mask[r, c]:
                    continue
                stack = [(r, c)]
                seen[r, c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in deltas:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and mask[nr, nc] and not seen[nr, nc]:
                            seen[nr, nc] = True
                            stack.append((nr, nc))
                comps.append(cells)
        return sorted(comps, key=lambda cells: (-len(cells), self._bbox_from_cells(cells)))

    def _object_digest(self, grid, *, multicolor=False, connectivity=4, max_items=6):
        from .grid_ops import find_objects, find_objects_multicolor
        if multicolor:
            objs = find_objects_multicolor(grid, bg=0, connectivity=connectivity)
        else:
            objs = find_objects(grid, bg=0, connectivity=connectivity)
        objs = sorted(objs, key=lambda o: (-o["size"], o["bbox"]))
        parts = []
        for obj in objs[:max_items]:
            r1, c1, r2, c2 = obj["bbox"]
            h = r2 - r1 + 1
            w = c2 - c1 + 1
            density = obj["size"] / (h * w) if h * w else 0
            if multicolor:
                label = "c" + "/".join(str(c) for c in sorted(obj["colors"]))
            else:
                label = f"c{obj['color']}"
            parts.append(
                f"{label} {obj['size']}px {self._bbox_text(obj['bbox'])} {h}x{w} d={density:.2f}"
            )
        if len(objs) > max_items:
            parts.append(f"+{len(objs) - max_items} more")
        return f"{len(objs)}: " + ("; ".join(parts) if parts else "none")

    def _task_color_role_lines(self):
        stats = {}
        for pair in self.task.get("train", []):
            if "output" not in pair:
                continue
            inp = np.array(pair["input"])
            out = np.array(pair["output"])
            if inp.shape != out.shape:
                continue
            colors = set(int(v) for v in inp.flatten()) | set(int(v) for v in out.flatten())
            for color in colors:
                entry = stats.setdefault(color, {"kept": 0, "lost": 0, "gained": 0})
                entry["kept"] += int(((inp == color) & (out == color)).sum())
                entry["lost"] += int(((inp == color) & (out != color)).sum())
                entry["gained"] += int(((inp != color) & (out == color)).sum())

        lines = []
        for color in sorted(stats):
            entry = stats[color]
            if entry["lost"] == 0 and entry["gained"] == 0:
                role = "invariant"
            elif entry["lost"] > 0 and entry["gained"] == 0:
                role = "source"
            elif entry["lost"] == 0 and entry["gained"] > 0:
                role = "target"
            else:
                role = "mixed"
            if role == "invariant" and entry["kept"] == 0:
                continue
            lines.append(
                f"c{color}: {role} kept={entry['kept']} lost={entry['lost']} gained={entry['gained']}"
            )
        return lines

    def _diagnose_pair(self, pair_idx, *, detail):
        if pair_idx < 0 or pair_idx >= len(self.task.get("train", [])):
            return [f"ERROR: pair {pair_idx} out of range ({len(self.task.get('train', []))} pairs)"]

        pair = self.task["train"][pair_idx]
        inp = np.array(pair["input"])
        out = np.array(pair["output"])
        in_ref = f"@{pair_idx * 2 + 1}"
        out_ref = f"@{pair_idx * 2 + 2}"
        lines = [
            f"pair {pair_idx} {in_ref}->{out_ref}: "
            f"{inp.shape[0]}x{inp.shape[1]} -> {out.shape[0]}x{out.shape[1]}"
        ]

        if detail:
            lines.append(f"  input colors: {self._format_counts(inp.flatten())}")
            lines.append(f"  output colors: {self._format_counts(out.flatten())}")

        if inp.shape != out.shape:
            lines.append("  shape changes; inspect extraction/upscale/tile relationship")
            return lines

        mask = inp != out
        changed = int(mask.sum())
        total = int(mask.size)
        if changed == 0:
            lines.append("  unchanged")
            return lines

        rows, cols = np.where(mask)
        bbox = f"r{int(rows.min())}-{int(rows.max())} c{int(cols.min())}-{int(cols.max())}"
        transitions = Counter((int(inp[r, c]), int(out[r, c])) for r, c in zip(rows, cols))
        src_colors = sorted(set(int(inp[r, c]) for r, c in zip(rows, cols)))
        dst_colors = sorted(set(int(out[r, c]) for r, c in zip(rows, cols)))
        pct = 100 * changed / total if total else 0
        lines.append(
            f"  changed: {changed}/{total} ({pct:.1f}%) bbox {bbox}; "
            f"sources {src_colors} -> targets {dst_colors}"
        )
        lines.append(f"  transitions: {self._format_counter(transitions)}")

        comps = self._mask_components(mask, connectivity=8)
        comp_bits = []
        for comp in comps[:5]:
            comp_set = set(comp)
            comp_trans = Counter(
                (int(inp[r, c]), int(out[r, c]))
                for r, c in comp_set
            )
            comp_bits.append(
                f"{len(comp)}px {self._bbox_text(comp)} {self._format_counter(comp_trans, max_items=3)}"
            )
        if comps:
            suffix = f"; +{len(comps) - 5} more" if len(comps) > 5 else ""
            lines.append(f"  diff clusters 8c ({len(comps)}): " + "; ".join(comp_bits) + suffix)

        if detail:
            changed_rows = sorted(set(int(r) for r in rows))
            changed_cols = sorted(set(int(c) for c in cols))
            lines.append(f"  changed rows: {changed_rows}")
            lines.append(f"  changed cols: {changed_cols}")
            lines.append(f"  input objects 4c: {self._object_digest(inp, connectivity=4)}")
            lines.append(f"  input blobs 8c: {self._object_digest(inp, multicolor=True, connectivity=8)}")

        return lines

    def _run_auto_scan(self):
        """Run auto-scan and store results."""
        from .auto_scan import auto_scan
        ranked, results = auto_scan(self.task)
        ref = self._store_feature(results)
        lines = [f"{ref} = Auto-scan: {len(ranked)} features ranked"]
        for i, (fname, score, summary) in enumerate(ranked[:8]):
            lines.append(f"  [{i+1}] ({score:.2f}) {summary}")
        # Run Racket-side automatic feature detection if bridge is available
        if self.use_racket and self._bridge is not None:
            try:
                rk_lines = self._racket_auto_features()
                if rk_lines:
                    lines.append("")
                    lines.append("  Racket auto-features:")
                    lines.extend(rk_lines)
            except Exception as e:
                lines.append(f"  (racket auto-features skipped: {e})")
        return "\n".join(lines)

    def _racket_auto_features(self):
        """Run Racket primitives that compute task-wide structural facts.

        Returns a list of formatted lines suitable for printing in auto-scan.
        Anything that returns #f / [] is omitted.
        """
        from .racket_bridge import RacketBridgeError
        out = []

        def call(sexpr):
            try:
                return self._bridge.eval_text(sexpr)
            except (RacketBridgeError, Exception):
                return None

        def fmt(label, val):
            if val is None or val == [] or val is False:
                return None
            return f"    {label}: {val}"

        # First-pair input grid is always @1
        # Helper: try a per-pair query and report values across pairs
        n_train = len(self.task.get('train', []))

        # Symmetry of input grid (@1)
        v = call("(detect-mirror-symmetry @1 '(0))")
        line = fmt("input mirror axes", v)
        if line: out.append(line)

        v = call("(detect-rotational-symmetry @1 '(0))")
        if v and v != 1:
            out.append(f"    input rotational fold: {v}")

        # Translational period of @1
        v = call("(detect-translational-period @1 '(0))")
        line = fmt("input period (dr,dc)", v)
        if line: out.append(line)

        # Same for output (@2) if exists
        if n_train >= 1 and 'output' in self.task['train'][0]:
            v = call("(detect-mirror-symmetry @2 '(0))")
            line = fmt("output mirror axes", v)
            if line: out.append(line)
            v = call("(detect-translational-period @2 '(0))")
            line = fmt("output period (dr,dc)", v)
            if line: out.append(line)

        # Frontiers in input
        v = call("(frontiers @1 '(0))")
        if v and isinstance(v, list) and len(v) > 0:
            out.append(f"    input frontiers: {len(v)} found — {v[:3]}{'...' if len(v) > 3 else ''}")

        # Color majority
        v = call("(color-majority @1)")
        if v: out.append(f"    input color majority: {v}")

        # diff-recolor-map across pairs (consistent recolor only, by definition)
        if n_train >= 1 and 'output' in self.task['train'][0]:
            v = call("(diff-recolor-map @1 @2)")
            if v and isinstance(v, list):
                # Filter out identity mappings
                non_id = [m for m in v if isinstance(m, list) and len(m) == 2 and m[0] != m[1]]
                if non_id:
                    out.append(f"    pair0 pure recolor map: {non_id}")

            # diff-translation
            v = call("(diff-translation @1 @2)")
            if v: out.append(f"    pair0 pure translation (dr,dc): {v}")

            # diff-positions count
            v = call("(length (diff-positions @1 @2))")
            if isinstance(v, int) and v > 0:
                out.append(f"    pair0 changed cells: {v}")

        # Object shape predicates: are inputs full of squares / lines?
        v = call("(map (lambda (o) (square? o)) (objects @1 0))")
        if isinstance(v, list) and len(v) > 0 and all(v):
            out.append(f"    input has {len(v)} objects, ALL squares")
        v = call("(map (lambda (o) (or (vline? o) (hline? o))) (objects @1 0))")
        if isinstance(v, list) and len(v) > 0 and all(v):
            out.append(f"    input has {len(v)} objects, ALL lines")

        # Object hole counts
        v = call("(map (lambda (o) (topo-count-holes @1 o)) (objects-multicolor @1 0))")
        if isinstance(v, list) and any((isinstance(x, int) and x > 0) for x in v):
            out.append(f"    input objects hole counts: {v}")

        return out

    @property
    def runtime_identity(self):
        """Describe the evaluator actually attached to this executor."""

        if self.use_racket:
            if self._bridge is None:
                raise RuntimeError("protected Racket bridge is closed")
            return self._bridge.runtime_identity
        source_path = Path(__file__).resolve()
        return {
            "schema": "arc-python-test-runtime-v1",
            "backend": "python-test-only",
            "protected": False,
            "deterministic": True,
            "python": platform.python_version(),
            "executor_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        }


    @property
    def state_summary(self):
        return {
            "turns": self._turns,
            "grids": len(self._grids),
            "features": len(self._features),
            "results": len(self._results),
            "checks": len(self._checks),
            "rule": self._rule_fn is not None,
            "errors": len(self._errors),
            "applied_results": {k: list(v) for k, v in self._applied_results.items()},
            "submitted": None if self._submitted is None else [list(v) for v in self._submitted],
        }

    @property
    def last_test_pair(self):
        return self._last_test_pair

    @property
    def last_test_pass(self):
        return self._last_test_pass

    @property
    def submitted(self):
        return None if self._submitted is None else [list(v) for v in self._submitted]

    # ============================================================
    # Handler dispatch table
    # ============================================================

    _HANDLERS = {
        # Observe
        'feature!': _handle_feature,
        'observe!': _handle_observe,
        'objects!': _handle_objects,
        'inspect!': _handle_inspect,
        'compare!': _handle_compare,
        'show!': _handle_show,
        'diff!': _handle_diff,
        'diagnose!': _handle_diagnose,
        'render!': _handle_render,
        'auto-scan!': _handle_auto_scan,
        'suggest!': _handle_suggest,

        # Fast feedback — try ideas without committing
        'try!': _handle_try,
        'try-all!': _handle_try_all,
        'peek!': _handle_peek,

        # Solve
        'transform!': _handle_transform,
        'rule!': _handle_rule,
        'template!': _handle_template,
        'test!': _handle_test,
        'verify!': _handle_verify,
        'test-all!': _handle_test_all,
        'test-until-fail!': _handle_test_until_fail,
        'compose!': _handle_compose,  # NOTE: applies left-to-right (pipe semantics)
        'pipe!': _handle_compose,    # alias — same behavior, clearer name
        'shape!': _handle_shape,
        'undo!': _handle_undo,
        'reset-rule!': _handle_reset_rule,

        # Submit
        'apply!': _handle_apply,
        'submit!': _handle_submit,

        # Meta
        'status!': _handle_status,
        'list!': _handle_list,
        'help!': _handle_help,
        'snapshot!': _handle_snapshot,
        'restore!': _handle_restore,
        'save-rule!': _handle_snapshot,   # clearer name (only saves rule)
        'load-rule!': _handle_restore,    # clearer name (only loads rule)
    }
