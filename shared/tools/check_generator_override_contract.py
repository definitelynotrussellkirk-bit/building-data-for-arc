#!/usr/bin/env python3
"""Probe declared overrides at boundaries and cross-mode combinations.

Three declarations a generator can make to this checker
=======================================================

1. ``AXES[name]["probe"] = "diagnostic"`` (or ``"exact": False`` /
   ``"diagnostic": True``) — "this axis has no finite probeable domain; do
   not treat its unparsable ``valid`` string as metadata rot".  Without the
   marker an axis whose ``valid`` the parser cannot decode is a hard
   contract error: it is silently absent from the Cartesian matrix, so the
   axis is never exercised while the report still says PASS.

2. ``INCOMPATIBLE_OVERRIDE_COMBINATIONS`` — a module-level sequence
   declaring which override tuples the generator legitimately refuses::

       INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
           {"texture": "full_grid", "hole_count": None},   # None = any value
           ("grid_h", "grid_w"),                           # axis names only
       ]

   A ``ValueError`` raised for a multi-axis case is accepted as an intended
   rejection only when it matches a declared entry, or when the exception
   carries the axis names itself (``exc.incompatible_axes`` / ``exc.axes``).
   Anything else is an unstructured rejection: an ordinary multi-axis bug is
   otherwise indistinguishable from an intentional refusal.  Generators that
   declare nothing stay on the legacy policy (warn, do not fail) so the
   existing corpus is not broken by the new contract.

3. ``observe_overrides(grid) -> dict`` — realized per-draw values for exact
   semantic axes (see ``_required_observer_axes``).

Every generator, regardless of what it declares, is additionally probed with
an unknown override key: ``**overrides`` that silently swallows a typo'd axis
name makes every override claim unfalsifiable.
"""

from __future__ import annotations

import argparse
import hashlib
import time
import importlib
import inspect
import itertools
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, NamedTuple


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from puzzle_generators.base import set_ctx_observer

OVERRIDE_CONTRACT_VERSION = 8
RESULTS_SCHEMA_VERSION = 3
ENUM_PROBE_CAP = 16

#: Override key no generator can legitimately declare. Used by the universal
#: unknown-key probe below.
UNKNOWN_OVERRIDE_PROBE_KEY = "__override_contract_unknown_axis__"

#: Module-level declaration of intentionally-rejected override tuples.
INCOMPATIBILITY_DECLARATION = "INCOMPATIBLE_OVERRIDE_COMBINATIONS"

#: Exception attributes that carry the incompatible axis names.
INCOMPATIBILITY_EXC_ATTRS = ("incompatible_axes", "axes", "override_axes")

#: ``AXES[name]`` markers that opt an axis out of the boundary matrix.
DIAGNOSTIC_PROBE_VALUES = {"diagnostic", "none", "manual", "skip", "no"}
RANGE_RE = re.compile(r"^\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*$")
FLOAT_RANGE_RE = re.compile(
    r"^\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s*\.\.\s*"
    r"(-?(?:\d+(?:\.\d*)?|\.\d+))\s*$"
)
RELATIVE_RANGE_RE = re.compile(
    r"^\s*(-?\d+)\s*\.\.\s*([hw])\s*(?:([+-])\s*(\d+))?\s*$"
)
DIMENSION_AXES = {
    "grid_h": 0,
    "canvas_h": 0,
    "height": 0,
    "grid_w": 1,
    "canvas_w": 1,
    "width": 1,
}
SQUARE_DIMENSION_AXES = {"grid_size", "canvas_size"}


def incompatibility_policy_summary(policy: str) -> str:
    """Explain the rejection policy without implying override quality.

    ``legacy`` is only a compatibility rule for undeclared multi-axis
    ``ValueError`` cases.  A generator can have exact, fully observed
    overrides and still print this policy because it has no incompatibility
    declaration to opt into strict classification.
    """
    if policy == "legacy":
        return (
            "incompatibility_policy=legacy-compat "
            "(undeclared multi-axis ValueErrors are WARN-only, not validated "
            "incompatibilities)"
        )
    return (
        "incompatibility_policy=strict "
        "(multi-axis rejections require structured incompatibility evidence)"
    )


def _is_numeric_square_axis(declared_axes: Any, axis: str) -> bool:
    """Is `axis` a reserved square-dimension name DECLARED AS AN INTEGER?

    The square-dimension shortcut assumes `case[axis]` is an int it can compare
    against `(len(grid), len(grid[0]))`. That assumption is silent, and when a
    generator legitimately declares `grid_size` as a STRING axis it produces
    self-contradictory findings: `expected = ("5x5", "5x5")` never equals
    `actual = (5, 5)`, while the failure message renders both sides the same
    way — "grid_size requested 5x5, got 5x5".

    Reported 2026-07-25 (EWF-000981, task 3e7bc7e83316) with a clean
    reproduction: 441 findings under `grid_size`, the identical 441 under
    `canvas_size`, and **0 findings after renaming the axis to `layout_scale`**.
    A checker whose verdict depends on the NAME rather than the TYPE is
    reserving a namespace it never documented.

    Fixing it by banning the names outright would be worse: `grid_size` is a
    natural name for a categorical scale knob, and a lint that forbids it
    pushes authors toward less descriptive names to appease a checker. So the
    dimension check is applied only when the declaration says the value IS an
    integer; a string-valued axis of the same name falls through to the normal
    `observe_overrides` path and is still verified there.
    """
    if not isinstance(declared_axes, dict) or axis not in declared_axes:
        return False
    spec = declared_axes.get(axis)
    if not isinstance(spec, dict):
        # A bare (non-dict) declaration carries no type; the historical
        # behaviour treated it as numeric, so preserve that rather than
        # silently stop checking a generator that was being checked before.
        return True
    return str(spec.get("type") or "int") == "int"


def _integer_domain(valid: str) -> list[int]:
    """Parse common finite/ranged integer and color declarations.

    The boundary matrix needs every value only for small domains.  Large
    domains intentionally collapse to their surviving endpoints, so never
    materialize them first: ``list(range(0, 7_233_945_600))`` used to exhaust
    memory while *static linting* task ``48fee61713bb`` even though the result
    was immediately reduced to two values.
    """

    # Color declarations sometimes use comma-separated ranges or append a
    # human-readable exclusion, e.g. ``1..9 (≠2)``. Boundaries are enough for
    # this matrix; exclude a boundary itself when the declaration says so.
    prefix = valid.split("(", 1)[0].strip()
    tokens = [
        token.strip()
        for token in re.split(r"[|,]", prefix)
        if token.strip()
    ]
    intervals: list[tuple[int, int]] = []
    small_values: set[int] = set()
    has_large_interval = False
    for token in tokens:
        range_match = RANGE_RE.match(token)
        if range_match:
            lo, hi = int(range_match.group(1)), int(range_match.group(2))
            if hi < lo:
                continue
            intervals.append((lo, hi))
            span = hi - lo + 1
            if span <= 16:
                small_values.update(range(lo, hi + 1))
            else:
                has_large_interval = True
            continue
        try:
            value = int(token)
        except ValueError:
            return []
        intervals.append((value, value))
        small_values.add(value)
    if not intervals:
        return []
    excluded = {
        int(value)
        for value in re.findall(r"(?:!=|≠)\s*(-?\d+)", valid)
    }

    if not has_large_interval and len(small_values) <= 16:
        return sorted(small_values - excluded)

    # Find the outermost surviving values without expanding any interval.
    # Walking past explicitly excluded endpoints costs O(number of exclusions),
    # not O(domain width).
    boundaries: list[int] = []
    for lo, hi in intervals:
        left = lo
        while left <= hi and left in excluded:
            left += 1
        if left > hi:
            continue
        right = hi
        while right >= left and right in excluded:
            right -= 1
        boundaries.extend((left, right))
    if not boundaries:
        return []
    lo, hi = min(boundaries), max(boundaries)
    return [lo] if lo == hi else [lo, hi]


def _dimension_max(symbol: str, axes: dict[str, Any] | None) -> int | None:
    if not isinstance(axes, dict):
        return None
    names = (
        ("grid_h", "canvas_h", "height", "grid_size", "canvas_size")
        if symbol == "h"
        else ("grid_w", "canvas_w", "width", "grid_size", "canvas_size")
    )
    for name in names:
        values = _axis_values(axes.get(name), None)
        numeric = [
            value
            for value in values
            if isinstance(value, int) and not isinstance(value, bool)
        ]
        if numeric:
            return max(numeric)
    return None


def _finite_enum_domain(spec: Any) -> list[str] | None:
    """Parse explicit categorical alternatives without a probe-budget decision."""
    if not isinstance(spec, dict) or str(spec.get("type") or "") not in {"str", "enum"}:
        return None
    raw = spec.get("valid")
    if isinstance(raw, (list, tuple)):
        if not raw or any(not isinstance(value, str) or not value for value in raw):
            return None
        values = list(raw)
    elif isinstance(raw, str) and "|" in raw:
        values = [value.strip() for value in raw.split("|") if value.strip()]
        if not values:
            return None
    else:
        return None
    return list(dict.fromkeys(values))


def _enum_probe_values(values: list[str]) -> list[str]:
    """All small enums; evenly spaced declaration indices for larger enums."""
    if len(values) <= ENUM_PROBE_CAP:
        return values
    return [values[i * (len(values) - 1) // (ENUM_PROBE_CAP - 1)]
            for i in range(ENUM_PROBE_CAP)]


def _axis_values(
    spec: Any, axes: dict[str, Any] | None = None
) -> list[Any]:
    if not isinstance(spec, dict) or axis_is_diagnostic(spec):
        return []
    kind = str(spec.get("type") or "")
    raw_valid = spec.get("valid")
    if kind in {"str", "enum"}:
        values = _finite_enum_domain(spec)
        return _enum_probe_values(values) if values is not None else []
    valid = str(raw_valid or "")
    if kind == "int":
        values = _integer_domain(valid)
        if values:
            return values
        relative = RELATIVE_RANGE_RE.match(valid)
        if relative:
            lo = int(relative.group(1))
            hi = _dimension_max(relative.group(2), axes)
            if hi is None:
                return []
            if relative.group(3) and relative.group(4):
                delta = int(relative.group(4))
                hi += delta if relative.group(3) == "+" else -delta
            if hi < lo:
                return []
            values = list(range(lo, hi + 1))
            return values if len(values) <= 16 else [lo, hi]
        return []
    if kind == "color":
        return _integer_domain(valid)
    if kind == "float":
        match = FLOAT_RANGE_RE.match(valid)
        if not match:
            return []
        lo, hi = float(match.group(1)), float(match.group(2))
        return [lo] if lo == hi else [lo, hi]
    if kind == "bool":
        normalized = {
            value.strip().lower()
            for value in valid.split("|")
            if value.strip()
        }
        if normalized and normalized <= {"0", "false"}:
            return [False]
        if normalized and normalized <= {"1", "true"}:
            return [True]
        return [False, True]
    return []


class AxisDomain(NamedTuple):
    """How the Cartesian boundary matrix actually sees one declared axis.

    ``status`` is the whole point: an axis the parser cannot decode is
    dropped from the matrix, so "0 findings" over a 7-axis generator can
    mean "3 axes were never exercised". Callers (this checker and
    ``scripts/lint_generator.py``) branch on the status instead of
    re-deriving the parse.
    """

    name: str
    status: str
    values: list[Any]
    reason: str

    @property
    def probed(self) -> bool:
        """True only when the matrix actually exercises this axis."""
        return bool(self.values)


def axis_is_diagnostic(spec: Any) -> bool:
    """Whether an axis is explicitly declared non-exact / unprobeable.

    Some domains genuinely cannot be written as boundary values (``n_dots``
    valid ``1..h*w/2``). Declaring that is fine; leaving it unmarked and
    unparsable is not, because the two are indistinguishable in the report.
    """
    if not isinstance(spec, dict):
        return False
    if str(spec.get("probe") or "").strip().lower() in DIAGNOSTIC_PROBE_VALUES:
        return True
    if spec.get("exact") is False:
        return True
    return spec.get("diagnostic") is True


def classify_axis_domain(
    name: str, spec: Any, axes: dict[str, Any]
) -> AxisDomain:
    """Classify one declared axis against the boundary-matrix parser."""
    if not isinstance(spec, dict):
        return AxisDomain(
            name,
            "malformed",
            [],
            f"AXES[{name!r}] is {type(spec).__name__}, not a spec dict",
        )
    if axis_is_diagnostic(spec):
        return AxisDomain(
            name,
            "diagnostic",
            [],
            "declared diagnostic/non-exact; intentionally not probed",
        )
    values = _axis_values(spec, axes)
    enum_values = _finite_enum_domain(spec)
    if enum_values is not None and len(enum_values) > ENUM_PROBE_CAP:
        return AxisDomain(
            name, "finite_enum_too_large", values,
            f"declared finite enum has {len(enum_values)} distinct values; "
            f"probe cap is {ENUM_PROBE_CAP}; deterministic declaration-order "
            f"sample covers {len(values)}/{len(enum_values)} values, including "
            "first and last; untested alternatives are not qualified, and "
            "sampled exact overrides require observe_overrides",
        )
    if len(values) >= 2:
        return AxisDomain(name, "probeable", values, "")
    if len(values) == 1:
        return AxisDomain(
            name,
            "singleton",
            values,
            f"domain collapses to the single value {values[0]!r}; the axis "
            "cannot demonstrate that an override changes anything",
        )
    kind = str(spec.get("type") or "")
    raw_valid = spec.get("valid")
    if (
        kind in {"str", "enum"}
        and isinstance(raw_valid, str)
        and raw_valid.strip()
        and "|" not in raw_valid
    ):
        return AxisDomain(
            name,
            "never_probed",
            [],
            f"single enum token {raw_valid!r} (no '|'); the matrix never "
            "probes it — declare the real alternatives or mark the axis "
            'diagnostic ("probe": "diagnostic")',
        )
    return AxisDomain(
        name,
        "unparsable",
        [],
        f"type={kind!r} valid={raw_valid!r} yields no probeable boundary "
        "value, so the axis is silently absent from the matrix — fix the "
        'declaration or mark it "probe": "diagnostic"',
    )


def axis_domain_report(axes: dict[str, Any]) -> list[AxisDomain]:
    """Classify every declared axis, in declaration order."""
    return [classify_axis_domain(name, spec, axes) for name, spec in axes.items()]


def _axis_domain_result(domain: AxisDomain, spec: Any, case_results: dict) -> dict:
    """Separate declared/planned enum coverage from actual attempted requests."""
    result = {"axis": domain.name, "status": domain.status,
              "probed_values": domain.values, "reason": domain.reason}
    enum_values = _finite_enum_domain(spec)
    if enum_values is not None:
        attempted = {row["case"][domain.name] for row in case_results.values()
                     if row["attempts"] and domain.name in row["case"]}
        result.update(
            enum_declared_cardinality=len(enum_values), enum_probe_cap=ENUM_PROBE_CAP,
            planned_coverage=("diagnostic" if domain.status == "diagnostic" else
                              "sampled" if len(enum_values) > len(domain.values) else
                              "exhaustive"),
            attempted_override_values=[value for value in domain.values if value in attempted],
        )
    return result


def _unprobed_axis_names(axes: dict[str, Any]) -> list[str]:
    """Declared axes the boundary matrix silently never probes.

    Compatibility wrapper over `axis_domain_report` (external reviewer probe
    scripts import this name). `main()` uses the richer report directly so it
    can separate an unparsable declaration (ERROR, stops the run) from a
    single-enum-token domain (still a finding, but not fail-fast). Axes
    explicitly declared diagnostic are excluded: a stated boundary, not rot.
    """
    return sorted(
        domain.name
        for domain in axis_domain_report(axes)
        if domain.status in {"unparsable", "never_probed", "malformed"}
    )


def _case_key(case: dict[str, Any]) -> str:
    return json.dumps(case, sort_keys=True, separators=(",", ":"))


def _build_cases(axes: dict[str, Any]) -> list[dict[str, Any]]:
    values: dict[str, list[Any]] = {}
    for name, spec in axes.items():
        choices = _axis_values(spec, axes)
        if choices:
            values[name] = choices

    cases: list[dict[str, Any]] = [{}]
    for name, choices in values.items():
        cases.extend({name: value} for value in choices)

    numeric = {
        name: choices
        for name, choices in values.items()
        if isinstance(choices[0], (int, float))
        and not isinstance(choices[0], bool)
    }
    discrete = {
        name: choices for name, choices in values.items() if name not in numeric
    }
    for left, right in itertools.combinations(sorted(numeric), 2):
        cases.extend(
            {left: left_value, right: right_value}
            for left_value, right_value in itertools.product(
                numeric[left], numeric[right]
            )
        )
    # Early-return modes such as texture=no_components/full_grid often bypass
    # the normal dimension/count path. Testing each override independently
    # misses combinations that silently ignore one of them, so keep every
    # discrete mode and boolean under the same numeric-boundary contract.
    for mode, number in itertools.product(sorted(discrete), sorted(numeric)):
        cases.extend(
            {mode: mode_value, number: number_value}
            for mode_value, number_value in itertools.product(
                discrete[mode], numeric[number]
            )
        )
    # Conflicting categorical aliases are another common source of silent
    # precedence (for example texture=warm making palette_kind=cool inert).
    # Exercise every pair so the behavioral check below can distinguish
    # "both axes work" from "one silently wins".
    for left, right in itertools.combinations(sorted(discrete), 2):
        cases.extend(
            {left: left_value, right: right_value}
            for left_value, right_value in itertools.product(
                discrete[left], discrete[right]
            )
        )
    if len(numeric) >= 2:
        cases.append({name: choices[0] for name, choices in numeric.items()})
        cases.append({name: choices[-1] for name, choices in numeric.items()})

    unique: dict[str, dict[str, Any]] = {}
    for case in cases:
        unique.setdefault(_case_key(case), case)
    return list(unique.values())


def _inert_pairwise_findings(
    axes: dict[str, Any],
    bands: list[str],
    seeds: range,
    outcomes: dict[tuple[str, int, str], Any],
) -> list[str]:
    """Find axes silently ignored under a second explicit override.

    Keyed generation makes this a strong behavioral test: hold one axis at a
    boundary/mode, sweep every tested value of a second axis with the same
    seed/sample, and compare exact grids. If *every* combination succeeds and
    every sweep is byte-identical across all bands/seeds, the varied axis is
    inert in that context. The generator must either honor it or reject the
    incompatible combination loudly.

    We deliberately require all requested outcomes to exist. Explicit
    ValueError rejections are an accepted contract and are therefore not
    reported as inertness.
    """
    values = {
        name: choices
        for name, spec in axes.items()
        if len(choices := _axis_values(spec, axes)) >= 2
    }
    findings: list[str] = []
    for fixed, varied in itertools.permutations(sorted(values), 2):
        for fixed_value in values[fixed]:
            comparisons = 0
            all_present = True
            all_identical = True
            for band in bands:
                for seed in seeds:
                    grids = []
                    for varied_value in values[varied]:
                        key = (
                            band,
                            seed,
                            _case_key(
                                {
                                    fixed: fixed_value,
                                    varied: varied_value,
                                }
                            ),
                        )
                        if key not in outcomes:
                            all_present = False
                            break
                        grids.append(outcomes[key])
                    if not all_present:
                        break
                    comparisons += 1
                    if any(grid != grids[0] for grid in grids[1:]):
                        all_identical = False
                        break
                if not all_present or not all_identical:
                    break
            if all_present and all_identical and comparisons:
                findings.append(
                    f"axis {varied!r} is inert when {fixed}={fixed_value!r}: "
                    f"all {comparisons} band/seed sweeps over "
                    f"{values[varied]!r} returned identical grids; honor the "
                    "mixed override or reject the combination explicitly"
                )
    return findings


def _partial_float_inert_warnings(
    axes: dict[str, Any],
    bands: list[str],
    seeds: range,
    outcomes: dict[tuple[str, int, str], Any],
    *,
    threshold: float = 0.20,
) -> list[str]:
    """Flag suspicious same-seed equality across float-axis extremes.

    Float controls can legitimately produce the same stochastic outcome for
    some seeds, so this is diagnostic rather than a hard contract failure.
    A large equality cluster often reveals a prior or early-return branch
    that never reads the explicit factor.
    """
    warnings: list[str] = []
    for axis, spec in axes.items():
        if not isinstance(spec, dict) or spec.get("type") != "float":
            continue
        values = _axis_values(spec, axes)
        if len(values) < 2:
            continue
        comparisons = 0
        identical = 0
        band_counts: dict[str, tuple[int, int]] = {}
        for band in bands:
            band_identical = 0
            band_comparisons = 0
            for seed in seeds:
                grids = []
                for value in values:
                    key = (
                        band,
                        seed,
                        _case_key({axis: value}),
                    )
                    if key not in outcomes:
                        grids = []
                        break
                    grids.append(outcomes[key])
                if not grids:
                    continue
                band_comparisons += 1
                if all(grid == grids[0] for grid in grids[1:]):
                    band_identical += 1
            comparisons += band_comparisons
            identical += band_identical
            band_counts[band] = (band_identical, band_comparisons)
        if comparisons < 6 or identical / comparisons < threshold:
            continue
        detail = ", ".join(
            f"{band} {same}/{total}"
            for band, (same, total) in band_counts.items()
            if total
        )
        warnings.append(
            f"float axis {axis!r} returned identical grids across extremes "
            f"{values!r} on {identical}/{comparisons} same-seed sweeps "
            f"({detail}); inspect whether a prior/early return ignores the "
            "explicit value, and explain any legitimate stochastic "
            "coincidence in warnings_disposition"
        )
    return warnings


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return "result is not a non-empty list-of-lists grid"
    width = len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return "result is ragged or has zero width"
    if len(grid) > 30 or width > 30:
        return f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid contains a non-integer or color outside 0..9"
    return None


def _finding_category(message: str) -> str:
    """Return a stable coarse category for machine-readable evidence."""
    lowered = message.lower()
    if "observe_overrides" in lowered or "keyed axis" in lowered:
        return "axis_provenance"
    if "never probed" in lowered:
        return "axis_metadata"
    if "inert" in lowered or "identical grids across extremes" in lowered:
        return "axis_effect"
    if "deterministic replay" in lowered:
        return "determinism"
    if "self_check" in lowered:
        return "self_check"
    if "requested" in lowered and (
        "observed" in lowered or " got " in lowered
    ):
        return "override_mismatch"
    if "raised" in lowered or "rejected" in lowered:
        return "generation_error"
    if "grid" in lowered or "color" in lowered:
        return "grid_validity"
    return "other"


_LABEL_PREFIX_RE = re.compile(r"^band=\S+ seed=\d+ overrides=\{.*?\}: ")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_REQUESTED_GOT_RE = re.compile(
    r"\brequested\s+-?\d+(?:\.\d+)?,\s+got\s+-?\d+(?:\.\d+)?\b"
)


def _normalized_signature(message: str) -> str:
    """Collapse one finding to its shape, so repeats group instead of spam.

    Bands, seeds and the concrete numbers are exactly what makes 5,898
    findings look like 5,898 problems when they are four. Quoted text is
    deliberately NOT normalized: two different ``self_check`` reasons are two
    different root causes, and merging them would hide one of them — the
    failure mode this whole change exists to remove.
    """
    text = _LABEL_PREFIX_RE.sub("", message)
    # Preserve the fact that this is a mismatch before replacing concrete
    # numerals. Otherwise the useful summary becomes the self-equal-looking
    # and misleading phrase ``requested N, got N``.
    text = _REQUESTED_GOT_RE.sub("requested != observed", text)
    text = _NUMBER_RE.sub("N", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:180]


class Finding(NamedTuple):
    message: str
    category: str
    axis: str
    signature: str
    band: str | None
    seed: int | None
    case: dict[str, Any] | None
    sample_index: int | None = None

    @property
    def generate_call(self) -> dict[str, Any] | None:
        """Exact draw arguments, or None for a static/aggregate finding."""
        if self.seed is None or self.sample_index is None or self.band is None:
            return None
        return {
            "seed": self.seed,
            "sample_index": self.sample_index,
            "difficulty": self.band,
            "overrides": dict(self.case or {}),
        }

    def as_report(self) -> dict[str, Any]:
        return {**self._asdict(), "generate_call": self.generate_call}

    @property
    def case_width(self) -> int:
        return len(self.case or {})


class FindingLog:
    """Structured findings that can report root causes before witnesses.

    Behaves enough like the previous ``list[str]`` (``len``, iteration over
    messages) that the call sites read the same, but every entry keeps the
    axis/band/seed/sample_index/case it came from so ``root_causes()`` can group by
    (axis, category, normalized message) and pick a MINIMIZED witness — the
    narrowest override case that reproduces the group.
    """

    def __init__(self) -> None:
        self._items: list[Finding] = []

    def add(
        self,
        message: str,
        *,
        axis: str | None = None,
        category: str | None = None,
        band: str | None = None,
        seed: int | None = None,
        sample_index: int | None = None,
        case: dict[str, Any] | None = None,
    ) -> None:
        if axis is None:
            axis = "+".join(sorted(case)) if case else "(default)"
        self._items.append(
            Finding(
                message=message,
                category=category or _finding_category(message),
                axis=axis,
                signature=_normalized_signature(message),
                band=band,
                seed=seed,
                sample_index=sample_index,
                case=dict(case) if case else None,
            )
        )

    def extend(self, messages, **meta: Any) -> None:
        for message in messages:
            self.add(message, **meta)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    @property
    def messages(self) -> list[str]:
        return [item.message for item in self._items]

    def root_causes(self, *, max_examples: int = 3) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str, str], list[Finding]] = defaultdict(list)
        for item in self._items:
            grouped[(item.axis, item.category, item.signature)].append(item)
        causes: list[dict[str, Any]] = []
        for (axis, category, signature), items in grouped.items():
            ordered = sorted(
                items,
                key=lambda f: (
                    f.case_width,
                    f.seed if f.seed is not None else -1,
                    f.band or "",
                    f.message,
                ),
            )
            witness = ordered[0]
            causes.append(
                {
                    "axis": axis,
                    "category": category,
                    "signature": signature,
                    "count": len(items),
                    "bands": sorted({f.band for f in items if f.band}),
                    "minimized_witness": {
                        "band": witness.band,
                        "seed": witness.seed,
                        "sample_index": witness.sample_index,
                        "generate_call": witness.generate_call,
                        "case": witness.case or {},
                        "message": witness.message,
                    },
                    "examples": [f.message for f in ordered[:max_examples]],
                }
            )
        causes.sort(key=lambda cause: (-cause["count"], cause["axis"], cause["signature"]))
        return causes


def print_condensed_warnings(
    warnings: list[str],
    *,
    prefix: str = "  - WARN: ",
    max_groups: int = 12,
    per_group: int = 2,
) -> None:
    """Terminal-friendly warning output (adopted 2026-07-29, EWF-002042/43/46).

    Thousands of per-seed legacy-compat rejections repeat a handful of
    normalized signatures; print bounded examples per signature with counts.
    Complete counts stay machine-readable in --write-results JSON
    (warning_categories + representative_warnings)."""
    groups: dict[str, list[str]] = {}
    for message in warnings:
        groups.setdefault(_normalized_signature(message), []).append(message)
    ordered = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for _sig, msgs in ordered[:max_groups]:
        print(f"{prefix}x{len(msgs)}  {msgs[0]}")
        for extra in msgs[1:per_group]:
            print(f"{' ' * len(prefix)}also: {extra}")
    hidden = sum(len(msgs) for _sig, msgs in ordered[max_groups:])
    if hidden:
        print(
            f"{prefix}... {hidden} more warning(s) in "
            f"{len(ordered) - max_groups} signature group(s) — complete "
            "counts in --write-results JSON (warning_categories)"
        )


def _normalized_declared_combination(entry: Any) -> dict[str, Any] | None:
    """Normalize one INCOMPATIBLE_OVERRIDE_COMBINATIONS entry.

    Accepts ``{"axis": value, "other": None}`` (None = any value) and bare
    axis-name collections ``("grid_h", "grid_w")`` (any values).
    """
    if isinstance(entry, dict):
        if not entry or not all(isinstance(key, str) for key in entry):
            return None
        return dict(entry)
    if isinstance(entry, (list, tuple, set, frozenset)):
        names = list(entry)
        if not names or not all(isinstance(name, str) for name in names):
            return None
        return {name: None for name in names}
    return None


def declared_incompatibilities(module: Any) -> list[dict[str, Any]] | None:
    """Declared incompatible override tuples, or None when undeclared.

    ``None`` (undeclared) and ``[]`` (declared empty = "no combination is
    ever refused") are deliberately different: the first keeps the legacy
    policy, the second is a real claim the checker can falsify.
    """
    raw = getattr(module, INCOMPATIBILITY_DECLARATION, None)
    if raw is None:
        return None
    if not isinstance(raw, (list, tuple, set, frozenset)):
        return []
    normalized: list[dict[str, Any]] = []
    for entry in raw:
        combination = _normalized_declared_combination(entry)
        if combination is not None:
            normalized.append(combination)
    return normalized


def _matches_declared_combination(
    case: dict[str, Any], combination: dict[str, Any]
) -> bool:
    for axis, value in combination.items():
        if axis not in case:
            return False
        if value is None:
            continue
        allowed = value if isinstance(value, (list, tuple, set, frozenset)) else [value]
        if case[axis] not in allowed:
            return False
    return True


def _exception_axes(exc: BaseException) -> set[str]:
    for attribute in INCOMPATIBILITY_EXC_ATTRS:
        value = getattr(exc, attribute, None)
        if isinstance(value, str):
            return {value}
        if isinstance(value, (list, tuple, set, frozenset)) and all(
            isinstance(item, str) for item in value
        ):
            return set(value)
    return set()


def rejection_disposition(
    case: dict[str, Any],
    exc: BaseException,
    declared: list[dict[str, Any]] | None,
) -> str:
    """Classify a ValueError raised for a multi-axis override case.

    ``declared_matrix`` / ``structured_exception`` are contract-satisfying
    rejections. ``message_names_axes`` is the weakest evidence we accept:
    the message itself names every overridden axis. ``unstructured`` is what
    the old check silently counted as an intentional rejection — any
    nonempty ValueError — which made an ordinary multi-axis bug look like a
    declared incompatibility.
    """
    if len(case) < 2:
        return "single_axis"
    for combination in declared or ():
        if _matches_declared_combination(case, combination):
            return "declared_matrix"
    exc_axes = _exception_axes(exc)
    if exc_axes and exc_axes <= set(case) and len(exc_axes) >= 2:
        return "structured_exception"
    text = str(exc)
    if text.strip() and all(axis in text for axis in case):
        return "message_names_axes"
    return "unstructured"


def unknown_key_probe(
    generate: Any,
    *,
    band: str,
    seed: int = 0,
    sample_index: int = 3,
) -> tuple[str, str]:
    """Probe one unknown override key. Returns (verdict, detail).

    ``**overrides`` that ignores an unrecognized key makes every override
    claim unfalsifiable: a typo'd axis name in a reviewer's matrix, a renamed
    axis, or a stale battery command all read as PASS.

    A baseline draw runs first: if the generator cannot produce anything at
    this band/seed, a raised exception says nothing about the unknown key,
    and the probe reports ``inconclusive`` rather than crediting a rejection
    it did not earn.
    """
    try:
        generate(seed, sample_index, difficulty=band)
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        return (
            "inconclusive",
            f"baseline draw (no overrides) already failed with "
            f"{type(exc).__name__}: {exc}",
        )
    probe = {UNKNOWN_OVERRIDE_PROBE_KEY: 123}
    try:
        result = generate(seed, sample_index, difficulty=band, **probe)
    except TypeError as exc:
        return "rejected", f"TypeError: {exc}"
    except ValueError as exc:
        return "rejected", f"ValueError: {exc}"
    except KeyError as exc:
        return "rejected", f"KeyError: {exc}"
    except Exception as exc:  # noqa: BLE001 - any loud failure is a rejection
        return "rejected_other", f"{type(exc).__name__}: {exc}"
    error = _grid_error(result)
    if error:
        # It did NOT reject the key — it took it and returned something
        # invalid, which is a strictly worse outcome than either.
        return "accepted_invalid_grid", error
    return "accepted", "generate() returned a grid for an unknown override key"


def _observed_override_errors(
    module: Any,
    grid: Any,
    case: dict[str, Any],
    label: str,
    required_axes: set[str] | None = None,
) -> list[str]:
    """Compare exact semantic axes exposed by an optional generator observer.

    Dimensions are universally observable and handled above. Task-specific
    quantities such as opening counts, marker counts, wall positions, and
    match roles are not safely inferable from arbitrary ARC grids, so reviewed
    generators can expose:

        def observe_overrides(grid) -> dict[str, int | float | str | bool]

    Every returned axis that was explicitly requested is exact-or-loud.
    """
    required = set(required_axes or ()) & set(case)
    observer = getattr(module, "observe_overrides", None)
    if not callable(observer) or not case:
        return []
    try:
        observed = observer(grid)
    except Exception as exc:
        return [
            f"{label}: observe_overrides raised "
            f"{type(exc).__name__}: {exc}"
        ]
    if not isinstance(observed, dict):
        return [f"{label}: observe_overrides must return a dict"]
    errors: list[str] = []
    for axis in sorted(required - set(observed)):
        errors.append(
            f"{label}: observe_overrides omitted required exact axis {axis!r}"
        )
    for axis, requested in case.items():
        if axis not in observed:
            continue
        actual = observed[axis]
        if (
            getattr(module, "AXES", {}).get(axis, {}).get("type") == "float"
            and isinstance(requested, float)
            and isinstance(actual, (int, float))
            and not isinstance(actual, bool)
        ):
            equal = math.isclose(
                float(actual), requested, rel_tol=1e-9, abs_tol=1e-9
            )
        else:
            equal = type(actual) is type(requested) and actual == requested
        if not equal:
            errors.append(
                f"{label}: {axis} requested {requested!r}, observed "
                f"{actual!r}"
            )
    return errors


def _default_drawn_vs_returned(
    module: Any,
    grid: Any,
    ctx: Any,
    required_axes: set[str],
) -> tuple[list[tuple[str, Any, Any]], list[str]]:
    """Compare free keyed semantic draws with values in the returned grid.

    Explicit-override checks alone cannot catch a generator that draws (say)
    ``hole_count=8`` and silently shrinks it after placement.  GenCtx keeps
    the keyed values, while ``observe_overrides`` and dimensions expose the
    realized values.  Compare only exact semantic axes that are observable;
    distribution controls such as density are intentionally excluded.
    """
    # Public GenCtx provenance API (contract v14); raw-store fallback for
    # pre-API ctx objects.
    if hasattr(ctx, "recorded_draws"):
        drawn = ctx.recorded_draws()
    else:
        drawn = getattr(ctx, "_drawn", None)
    if not isinstance(drawn, dict):
        return [], ["captured GenCtx has no draw-provenance mapping"]

    declared_axes = getattr(module, "AXES", {})
    required_draw_axes = set(required_axes)
    if isinstance(declared_axes, dict):
        required_draw_axes.update(
            axis
            for axis in set(DIMENSION_AXES) | SQUARE_DIMENSION_AXES
            if axis in declared_axes
        )

    errors: list[str] = []
    observed: dict[str, Any] = {}
    for axis, dimension in DIMENSION_AXES.items():
        if isinstance(declared_axes, dict) and axis in declared_axes:
            observed[axis] = len(grid) if dimension == 0 else len(grid[0])
    for axis in SQUARE_DIMENSION_AXES:
        if isinstance(declared_axes, dict) and axis in declared_axes:
            observed[axis] = (
                len(grid)
                if len(grid) == len(grid[0])
                else (len(grid), len(grid[0]))
            )

    observer = getattr(module, "observe_overrides", None)
    if callable(observer):
        try:
            semantic = observer(grid)
        except Exception as exc:
            errors.append(
                "observe_overrides raised during default-axis audit: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            if not isinstance(semantic, dict):
                errors.append(
                    "observe_overrides must return a dict during "
                    "default-axis audit"
                )
            else:
                # Returning an AXES key from observe_overrides is an explicit
                # declaration that the value is exact and recoverable from
                # the grid. That declaration supersedes the generic
                # min_/max_ naming heuristic: e.g. max_arm_len may be an
                # exact realized maximum rather than a loose upper bound.
                observer_axes = (
                    set(semantic) & set(declared_axes)
                    if isinstance(declared_axes, dict)
                    else set()
                )
                required_draw_axes.update(observer_axes)
                observed.update(
                    {
                        axis: value
                        for axis, value in semantic.items()
                        if axis in required_draw_axes
                    }
                )

    errors.extend(
        f"default path omitted keyed draw provenance for exact axis {axis!r}"
        for axis in sorted(required_draw_axes - set(drawn))
    )

    comparisons = [
        (axis, drawn[axis], actual)
        for axis, actual in observed.items()
        if axis in drawn
    ]
    return comparisons, errors


def _required_observer_axes(axes: dict[str, Any]) -> set[str]:
    """Semantic axes whose accepted override must be observed per draw.

    Grid dimensions are checked universally. Floats and ``min_``/``max_``
    knobs are usually distribution controls or bounds rather than exact
    realized values. In contrast, multi-valued integer counts/positions,
    colors, and booleans are exact instance claims: a generator must expose
    their actual realized value so post-draw clamping/fallback cannot hide.
    """
    required: set[str] = set()
    dimensions = set(DIMENSION_AXES) | SQUARE_DIMENSION_AXES
    for name, spec in axes.items():
        if not isinstance(spec, dict) or axis_is_diagnostic(spec):
            continue
        enum_values = _finite_enum_domain(spec)
        if enum_values is not None and len(enum_values) > ENUM_PROBE_CAP:
            required.add(name)
            continue
        if name in dimensions:
            continue
        kind = str(spec.get("type") or "")
        choices = _axis_values(spec, axes)
        if len(choices) < 2:
            continue
        if kind == "bool" or kind == "color":
            required.add(name)
        elif (
            kind == "int"
            and not name.startswith(("min_", "max_"))
            and not name.endswith(("_min", "_max", "_limit"))
        ):
            required.add(name)
    return required


def _load_module(task_id: str):
    if task_id.startswith("generic_"):
        raise ValueError(
            "generic generators require a task-level manual boundary matrix; "
            "this checker currently targets per-puzzle generate(...) modules"
        )
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{task_id}.generator"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument(
        "--bands",
        default="easy,medium,hard",
        help="comma-separated difficulty bands",
    )
    parser.add_argument("--max-findings", type=int, default=80)
    parser.add_argument(
        "--max-root-causes",
        type=int,
        default=20,
        help="how many grouped root causes to print before the witnesses",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=3,
        help="capped examples kept per root-cause group",
    )
    parser.add_argument(
        "--incompatibility-policy",
        choices=("auto", "strict", "legacy"),
        default="auto",
        help=(
            "how to treat a multi-axis ValueError: strict = only a declared "
            f"{INCOMPATIBILITY_DECLARATION} entry or an exception carrying "
            "axis names counts as an intended rejection; legacy = any "
            "nonempty message counts (warn only); auto = strict when the "
            "module declares the constant, legacy otherwise"
        ),
    )
    parser.add_argument(
        "--strict-unknown-key",
        action="store_true",
        help=(
            "promote the universal unknown-override-key probe from WARNING "
            "to a finding. Measured 2026-07-25: 68/80 sampled per-puzzle "
            "generators silently accept an unknown key, so this is a "
            "warning by default and opt-in per generator"
        ),
    )
    parser.add_argument(
        "--no-fail-fast",
        action="store_true",
        help=(
            "run the full Cartesian matrix even when a declared axis is "
            "unparsable (default: report the dead axes and stop, instead of "
            "burning thousands of draws whose findings all trace back to "
            "the same broken declarations)"
        ),
    )
    parser.add_argument(
        "--write-cases",
        type=Path,
        help="write the exact generated override-case matrix as a JSON list",
    )
    parser.add_argument(
        "--write-results",
        type=Path,
        help=(
            "write a compact machine-readable per-case result artifact with "
            "attempts, accepted draws, rejections, observations, and findings"
        ),
    )
    parser.add_argument(
        "--case-shard",
        metavar="I/N",
        help=(
            "run only shard I of N of the deterministic case matrix "
            "(1-indexed, e.g. 1/4) so constrained/foreground transports can "
            "finish in bounded slices and merge JSON results "
            "(adopted 2026-07-29, EWF-002063)"
        ),
    )
    parser.add_argument("--full-results", "--verbose-results", action="store_true", help="retain every case and finding instead of the default root-cause summary")
    parser.add_argument("--compact-results", action="store_true",
                        help="retain totals and failure witnesses, omit successful case detail")
    parser.add_argument("--progress-every", type=int, default=1000,
                        help="print progress every N attempted matrix draws (default: 1000)")
    args = parser.parse_args()
    if args.full_results and args.compact_results:
        parser.error("--full-results and --compact-results are mutually exclusive")
    audit_summary = not args.full_results and not args.compact_results
    if args.seeds < 1 or args.progress_every < 1:
        parser.error("--seeds and --progress-every must be positive")

    try:
        module = _load_module(args.task_id)
    except Exception as exc:
        print(f"override-contract: ERROR {args.task_id}: {exc}")
        return 2

    axes = getattr(module, "AXES", None)
    generate = getattr(module, "generate", None)
    if not isinstance(axes, dict) or not callable(generate):
        print(f"override-contract: ERROR {args.task_id}: missing AXES or generate")
        return 2

    cases = _build_cases(axes)
    full_case_count = len(cases)
    if args.case_shard:
        try:
            shard_index, shard_total = (
                int(part) for part in args.case_shard.split("/", 1))
        except ValueError:
            print(f"override-contract: ERROR {args.task_id}: --case-shard "
                  f"must be I/N, got {args.case_shard!r}")
            return 2
        if not 1 <= shard_index <= shard_total:
            print(f"override-contract: ERROR {args.task_id}: shard index "
                  f"{shard_index} outside 1..{shard_total}")
            return 2
        full = len(cases)
        cases = cases[shard_index - 1::shard_total]
        # LOUD partial-coverage banner: a sharded run must never read as the
        # complete matrix.
        print(f"override-contract: CASE SHARD {shard_index}/{shard_total} — "
              f"{len(cases)} of {full} cases this run; merge all shards "
              "before claiming full coverage")
    required_observer_axes = _required_observer_axes(axes)
    if args.write_cases:
        path = (
            args.write_cases
            if args.write_cases.is_absolute()
            else ROOT / args.write_cases
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cases, indent=2, sort_keys=True) + "\n")
    bands = [band.strip() for band in args.bands.split(",") if band.strip()]
    if not bands:
        parser.error("--bands must contain at least one band")
    findings = FindingLog()
    warnings: list[str] = []

    # ---- axis domains: fail fast BEFORE the Cartesian matrix ------------
    # A dead axis is not one finding among thousands: it is the reason the
    # thousands exist. Report the broken declarations first, and (by
    # default) do not spend 18k draws whose every finding traces back here.
    domains = axis_domain_report(axes)
    dead_domains = [d for d in domains if d.status in {"unparsable", "malformed"}]
    never_probed = [d for d in domains if d.status == "never_probed"]
    singleton_domains = [d for d in domains if d.status == "singleton"]
    sampled_enum_domains = [d for d in domains if d.status == "finite_enum_too_large"]
    for domain in dead_domains + never_probed:
        findings.add(
            f"axis {domain.name!r} is silently never probed: {domain.reason}",
            axis=domain.name,
            category="axis_metadata",
        )
    for domain in singleton_domains:
        warnings.append(
            f"axis {domain.name!r} has a singleton domain: {domain.reason}"
        )
    for domain in sampled_enum_domains:
        warnings.append(
            f"finite_enum_too_large: axis {domain.name!r}: {domain.reason}"
        )
    fail_fast = bool(dead_domains) and not args.no_fail_fast

    # ---- incompatibility policy ----------------------------------------
    declared_combinations = declared_incompatibilities(module)
    if args.incompatibility_policy == "auto":
        policy = "strict" if declared_combinations is not None else "legacy"
    else:
        policy = args.incompatibility_policy
    # NOTE: no unconditional "you declared nothing" warning. Every generator
    # in the corpus currently declares nothing, and a warning that fires on
    # every run is a warning reviewers learn to skip. The legacy policy only
    # matters once the generator ACTUALLY rejects a multi-axis case, which is
    # warned about below with the offending example attached.

    plan = {"axis_sizes": {domain.name: len(domain.values) for domain in domains},
            "sampled_enum_axes": {domain.name: {
                "declared_cardinality": len(_finite_enum_domain(axes[domain.name])),
                "planned_cardinality": len(domain.values)} for domain in sampled_enum_domains},
            "case_count": len(cases), "full_case_count": full_case_count,
            "bands": bands, "seeds_per_case": args.seeds,
            "estimated_matrix_draws": 0 if fail_fast else len(cases) * len(bands) * args.seeds,
            "unknown_key_probe_calls_max": 2,
            "replay_calls_max": 0 if fail_fast else len(cases) * len(bands) * args.seeds}
    print("override-contract: PLAN " + json.dumps(plan, sort_keys=True), flush=True)
    started = time.monotonic()

    # ---- universal unknown-key probe (independent of declared AXES) -----
    unknown_verdict, unknown_detail = unknown_key_probe(
        generate, band=bands[0] if bands else "medium", seed=0, sample_index=3
    )
    unknown_message = (
        f"unknown override key {UNKNOWN_OVERRIDE_PROBE_KEY!r} was accepted "
        f"({unknown_detail}); **overrides silently swallows unrecognized "
        "axis names, so a typo'd or renamed axis reads as PASS"
    )
    if unknown_verdict.startswith("accepted"):
        if args.strict_unknown_key:
            findings.add(
                unknown_message, axis="(unknown-key probe)", category="unknown_key",
                band=bands[0] if bands else "medium", seed=0, sample_index=3,
                case={UNKNOWN_OVERRIDE_PROBE_KEY: 123},
            )
        else:
            warnings.append(unknown_message)

    outcomes: dict[tuple[str, int, str], Any] = {}
    case_results: dict[tuple[str, str], dict[str, Any]] = {}
    default_totals: Counter[str] = Counter()
    default_mismatches: Counter[str] = Counter()
    default_band_mismatches: dict[str, Counter[str]] = defaultdict(Counter)
    default_examples: dict[str, list[str]] = defaultdict(list)
    rejection_dispositions: Counter[str] = Counter()
    rejection_examples: dict[str, list[str]] = defaultdict(list)
    draws = 0
    accepted_draws = 0
    explicit_rejections = 0
    if required_observer_axes and not callable(
        getattr(module, "observe_overrides", None)
    ):
        findings.add(
            "missing observe_overrides(grid) for exact semantic axes: "
            + ", ".join(sorted(required_observer_axes))
            + "; report the realized per-draw values so accepted overrides "
              "cannot clamp or fall back silently",
            axis="+".join(sorted(required_observer_axes)),
            category="axis_provenance",
        )

    for band in [] if fail_fast else bands:
        for case in cases:
            case_key = _case_key(case)
            case_result = {
                "band": band,
                "case": case,
                "attempts": 0,
                "accepted": 0,
                "explicit_rejections": 0,
                "errors": 0,
                "finding_count": 0,
                "realized_observations": Counter(),
            }
            case_results[(band, case_key)] = case_result
            for seed in range(args.seeds):
                findings_before = len(findings)
                case_result["attempts"] += 1
                if draws and draws % args.progress_every == 0:
                    print(f"override-contract: PROGRESS {draws}/{plan['estimated_matrix_draws']} "
                          f"draws completed, accepted={accepted_draws}, findings={len(findings)}, "
                          f"elapsed_seconds={time.monotonic() - started:.1f}", flush=True)
                draws += 1
                sample_index = seed * 17 + 3
                label = f"band={band} seed={seed} overrides={case}"
                captured_contexts: list[Any] = []
                if not case:
                    set_ctx_observer(captured_contexts.append)
                try:
                    grid = generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        **case,
                    )
                except ValueError as exc:
                    disposition = rejection_disposition(
                        case, exc, declared_combinations
                    )
                    if disposition != "single_axis" and str(exc).strip():
                        rejection_dispositions[disposition] += 1
                        if len(rejection_examples[disposition]) < 3:
                            rejection_examples[disposition].append(
                                f"{label}: {exc}"
                            )
                    if disposition in {
                        "declared_matrix",
                        "structured_exception",
                    } or (
                        disposition in {"message_names_axes", "unstructured"}
                        and policy == "legacy"
                        and str(exc).strip()
                    ):
                        # Accepted as an intended incompatibility. Under the
                        # legacy policy that acceptance is weak evidence —
                        # it is counted and surfaced as a warning below.
                        explicit_rejections += 1
                        case_result["explicit_rejections"] += 1
                        continue
                    if disposition == "message_names_axes":
                        # Strict policy: the message names every overridden
                        # axis. Weakest accepted evidence; counted, and the
                        # generator is told to declare the tuple.
                        explicit_rejections += 1
                        case_result["explicit_rejections"] += 1
                        continue
                    case_result["errors"] += 1
                    if disposition == "unstructured":
                        findings.add(
                            f"{label}: multi-axis case rejected without a "
                            f"declared incompatibility: {exc}; add the tuple "
                            f"to {INCOMPATIBILITY_DECLARATION} or attach "
                            "incompatible_axes to the exception so an "
                            "ordinary bug cannot pass as an intended "
                            "rejection",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            case=case,
                            category="undeclared_rejection",
                        )
                    else:
                        findings.add(
                            f"{label}: declared/default case rejected: {exc}",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            case=case,
                        )
                    case_result["finding_count"] += (
                        len(findings) - findings_before
                    )
                    continue
                except Exception as exc:
                    case_result["errors"] += 1
                    findings.add(
                        f"{label}: raised {type(exc).__name__}: {exc}",
                        band=band,
                        seed=seed,
                        sample_index=sample_index,
                        case=case,
                    )
                    case_result["finding_count"] += (
                        len(findings) - findings_before
                    )
                    continue
                finally:
                    if not case:
                        set_ctx_observer(None)

                error = _grid_error(grid)
                if error:
                    case_result["errors"] += 1
                    findings.add(
                        f"{label}: {error}", band=band, seed=seed,
                        sample_index=sample_index, case=case,
                    )
                    case_result["finding_count"] += (
                        len(findings) - findings_before
                    )
                    continue
                accepted_draws += 1
                case_result["accepted"] += 1
                outcomes[(band, seed, _case_key(case))] = grid

                observer = getattr(module, "observe_overrides", None)
                if callable(observer):
                    try:
                        realized = observer(grid)
                    except Exception as exc:
                        realized = {
                            "__observer_error__": (
                                f"{type(exc).__name__}: {exc}"
                            )
                        }
                    case_result["realized_observations"][
                        json.dumps(
                            realized,
                            sort_keys=True,
                            separators=(",", ":"),
                            default=repr,
                        )
                    ] += 1

                if not case:
                    if not captured_contexts:
                        findings.add(
                            f"{label}: generate did not construct a GenCtx; "
                            "default keyed-axis honesty cannot be audited",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            case=case,
                        )
                    else:
                        comparisons, default_errors = (
                            _default_drawn_vs_returned(
                                module,
                                grid,
                                captured_contexts[-1],
                                required_observer_axes,
                            )
                        )
                        findings.extend(
                            (
                                f"{label}: {message}"
                                for message in default_errors
                            ),
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            case=case,
                        )
                        for axis, drawn_value, returned_value in comparisons:
                            default_totals[axis] += 1
                            if drawn_value == returned_value:
                                continue
                            default_mismatches[axis] += 1
                            default_band_mismatches[axis][band] += 1
                            if len(default_examples[axis]) < 3:
                                default_examples[axis].append(
                                    f"{band}/seed {seed}: drew "
                                    f"{drawn_value!r}, returned "
                                    f"{returned_value!r}"
                                )

                replay = generate(
                    seed,
                    sample_index,
                    difficulty=band,
                    **case,
                )
                if replay != grid:
                    findings.add(
                        f"{label}: deterministic replay mismatch",
                        band=band,
                        seed=seed,
                        sample_index=sample_index,
                        case=case,
                    )

                for axis, dimension in DIMENSION_AXES.items():
                    if axis not in case:
                        continue
                    actual = len(grid) if dimension == 0 else len(grid[0])
                    if actual != case[axis]:
                        findings.add(
                            f"{label}: {axis} requested {case[axis]}, got {actual}",
                            axis=axis,
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            case=case,
                        )
                for axis in SQUARE_DIMENSION_AXES:
                    if axis not in case:
                        continue
                    # Only when the axis is DECLARED numeric — see
                    # _is_numeric_square_axis. A string-valued grid_size used to
                    # fail here unconditionally with a message that printed the
                    # same value on both sides of "requested X, got X".
                    if not _is_numeric_square_axis(axes, axis):
                        continue
                    actual = (len(grid), len(grid[0]))
                    expected = (case[axis], case[axis])
                    if type(actual) is not type(expected) or actual != expected:
                        findings.add(
                            f"{label}: {axis} requested {case[axis]}, got "
                            f"{actual[0]}x{actual[1]}",
                            axis=axis,
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            case=case,
                        )
                findings.extend(
                    _observed_override_errors(
                        module,
                        grid,
                        case,
                        label,
                        required_axes=required_observer_axes,
                    ),
                    band=band,
                    seed=seed,
                    sample_index=sample_index,
                    case=case,
                )

                self_check = getattr(module, "self_check", None)
                if callable(self_check):
                    try:
                        parameters = inspect.signature(self_check).parameters
                        kwargs = {}
                        if "difficulty" in parameters:
                            kwargs["difficulty"] = band
                        if "meta" in parameters:
                            kwargs["meta"] = {
                                **case,
                                "overrides": dict(case),
                                "override_contract_version":
                                    OVERRIDE_CONTRACT_VERSION,
                            }
                        errors = self_check(grid, **kwargs)
                    except Exception as exc:
                        findings.add(
                            f"{label}: self_check raised "
                            f"{type(exc).__name__}: {exc}",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            case=case,
                        )
                    else:
                        if errors:
                            findings.add(
                                f"{label}: self_check failed: {errors}",
                                band=band,
                                seed=seed,
                                sample_index=sample_index,
                                case=case,
                            )
                case_result["finding_count"] += (
                    len(findings) - findings_before
                )

    for axis in sorted(default_mismatches):
        detail = ", ".join(
            f"{band} {default_band_mismatches[axis][band]}/{args.seeds}"
            for band in bands
        )
        examples = "; ".join(default_examples[axis])
        findings.add(
            f"default keyed axis {axis!r} drifted on "
            f"{default_mismatches[axis]}/{default_totals[axis]} returned "
            f"grids ({detail}; examples: {examples}); choose a feasible "
            "domain before drawing instead of silently clamping, shrinking, "
            "or replacing the recorded value",
            axis=axis,
            category="axis_provenance",
        )

    for message in _inert_pairwise_findings(
        axes, bands, range(args.seeds), outcomes
    ):
        inert_axis = re.match(r"axis '([^']+)'", message)
        findings.add(
            message,
            axis=inert_axis.group(1) if inert_axis else None,
            category="axis_effect",
        )
    warnings.extend(
        _partial_float_inert_warnings(
            axes, bands, range(args.seeds), outcomes
        )
    )
    if policy == "legacy" and rejection_dispositions["unstructured"]:
        warnings.append(
            f"{rejection_dispositions['unstructured']} multi-axis rejections "
            "were accepted on the legacy policy with no declared "
            f"incompatibility (e.g. {rejection_examples['unstructured'][0]}); "
            f"declare {INCOMPATIBILITY_DECLARATION} to make them falsifiable"
        )
    if unknown_verdict == "rejected_other":
        warnings.append(
            "unknown override key was rejected, but not with "
            f"TypeError/ValueError/KeyError: {unknown_detail}"
        )
    elif unknown_verdict == "inconclusive":
        warnings.append(
            f"unknown-key probe inconclusive: {unknown_detail}"
        )

    print(f"override-contract: PROGRESS {draws}/{plan['estimated_matrix_draws']} "
          f"draws completed, accepted={accepted_draws}, findings={len(findings)}, "
          f"elapsed_seconds={time.monotonic() - started:.1f}", flush=True)
    root_causes = findings.root_causes(max_examples=args.max_examples)
    if findings:
        status = "FAIL_FAST" if fail_fast else "FAIL"
    elif warnings:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"

    if args.write_results:
        path = (
            args.write_results
            if args.write_results.is_absolute()
            else ROOT / args.write_results
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for result in case_results.values():
            observations = [
                {
                    "value": json.loads(value),
                    "count": count,
                }
                for value, count in result.pop(
                    "realized_observations"
                ).most_common()
            ]
            rows.append({**result, "realized_observations": observations})
        case_digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        band_totals = {}
        for band in bands:
            band_totals[band] = {key: sum(row[key] for row in rows if row['band'] == band)
                                 for key in ('attempts', 'accepted', 'explicit_rejections', 'errors', 'finding_count')}
        original_row_count = len(rows)
        if args.compact_results:
            rows = [row for row in rows if row['errors'] or row['finding_count']]
        if audit_summary:
            rows = []  # root_causes retain exact minimized replay calls and counts
        source_path = getattr(module, '__file__', None)
        source_digest = hashlib.sha256(Path(source_path).read_bytes()).hexdigest() if source_path else None
        runtime_manifest = ROOT / 'RUNTIME_MANIFEST.json'
        path.write_text(
            json.dumps(
                {
                    "schema_version": RESULTS_SCHEMA_VERSION,
                    "report_mode": "summary" if audit_summary else "compact" if args.compact_results else "full",
                    "cases_complete": not args.compact_results and not audit_summary,
                    "case_result_rows_total": original_row_count,
                    "case_result_rows_omitted": original_row_count - len(rows),
                    "case_results_sha256": case_digest,
                    "source_sha256": source_digest,
                    "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "runtime_manifest_sha256": hashlib.sha256(runtime_manifest.read_bytes()).hexdigest() if runtime_manifest.exists() else None,
                    "settings": {key: value for key, value in vars(args).items()
                                 if key not in {'write_results', 'write_cases'}},
                    "plan": plan,
                    "band_totals": band_totals,
                    "override_contract_version": OVERRIDE_CONTRACT_VERSION,
                    "task_id": args.task_id,
                    # ---- top-level verdict: no consumer should have to
                    # infer PASS from finding_count == 0 and then separately
                    # interpret explicit_rejections.
                    "status": status,
                    "draws_total": draws,
                    "accepted_total": accepted_draws,
                    "explicit_rejections_total": explicit_rejections,
                    "incompatibility_policy": policy,
                    "bands": bands,
                    "seeds_per_case": args.seeds,
                    "draws": draws,
                    "case_count": len(cases),
                    # non-null ONLY on a partial sharded run — a merged reader
                    # must be able to tell a slice from the full matrix
                    "case_shard": args.case_shard or None,
                    "fail_fast": fail_fast,
                    "finding_count": len(findings),
                    "findings_complete": not audit_summary,
                    "findings": ([{**root["minimized_witness"], "category":root["category"], "axis":root["axis"], "count":root["count"]} for root in root_causes] if audit_summary else [finding.as_report() for finding in findings]),
                    "replay_recipe": "Replay each root_causes[].minimized_witness.generate_call against source_sha256; --full-results retains every case.",
                    "warning_count": len(warnings),
                    "axis_domains": [_axis_domain_result(domain, axes[domain.name], case_results)
                                     for domain in domains],
                    "unknown_key_probe": {
                        "key": UNKNOWN_OVERRIDE_PROBE_KEY,
                        "verdict": unknown_verdict,
                        "detail": unknown_detail,
                        "severity": (
                            "ok"
                            if not unknown_verdict.startswith("accepted")
                            else (
                                "finding"
                                if args.strict_unknown_key
                                else "warning"
                            )
                        ),
                    },
                    "rejection_dispositions": dict(
                        sorted(rejection_dispositions.items())
                    ),
                    "rejection_examples": {
                        key: list(value)
                        for key, value in sorted(rejection_examples.items())
                    },
                    "declared_incompatibilities": declared_combinations,
                    "root_causes": root_causes,
                    "finding_categories": dict(
                        sorted(
                            Counter(
                                finding.category for finding in findings
                            ).items()
                        )
                    ),
                    "warning_categories": dict(
                        sorted(
                            Counter(
                                _finding_category(message)
                                for message in warnings
                            ).items()
                        )
                    ),
                    "representative_findings": [
                        finding.as_report()
                        for finding in list(findings)[:20]
                    ],
                    "representative_warnings": [
                        {
                            "category": _finding_category(message),
                            "message": message,
                        }
                        for message in warnings[:20]
                    ],
                    "explicit_rejections": explicit_rejections,
                    "cases": rows,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    if findings:
        policy_summary = incompatibility_policy_summary(policy)
        print(
            f"override-contract: {status} {args.task_id}: {len(findings)} "
            f"findings across {draws} draws / {len(cases)} override cases "
            f"({explicit_rejections} explicit combination rejections "
            f"accepted; {policy_summary})"
        )
        if fail_fast:
            print(
                "  STOPPED BEFORE THE CARTESIAN MATRIX: "
                f"{len(dead_domains)} declared axis/axes cannot be probed, so "
                "every downstream finding would trace back to these "
                "declarations. Fix them (or pass --no-fail-fast) before "
                "reading per-seed output."
            )
        # ---- root causes FIRST. The per-seed witnesses below are the same
        # handful of causes multiplied by bands x seeds x cases; printing
        # them first is what turned 5,898 findings into "3 dead axes".
        print(
            f"  ROOT CAUSES ({len(root_causes)} groups, by axis / category / "
            "normalized message):"
        )
        for index, cause in enumerate(root_causes[: args.max_root_causes], 1):
            witness = cause["minimized_witness"]
            print(
                f"    [{index}] x{cause['count']}  axis={cause['axis']}  "
                f"category={cause['category']}"
            )
            print(f"        signature: {cause['signature']}")
            print(
                f"        minimized witness: band={witness['band']} "
                f"seed={witness['seed']} sample_index={witness['sample_index']} "
                f"overrides={witness['case']}"
            )
            for example in cause["examples"][1:]:
                print(f"        also: {example}")
        if len(root_causes) > args.max_root_causes:
            print(
                f"    ... {len(root_causes) - args.max_root_causes} more "
                "root-cause groups (full list in --write-results JSON)"
            )
        print("  PER-SEED WITNESSES:")
        for finding in list(findings)[: args.max_findings]:
            print(f"  - {finding.message}")
        if len(findings) > args.max_findings:
            print(f"  ... {len(findings) - args.max_findings} more findings")
        print_condensed_warnings(warnings)
        return 1

    print_condensed_warnings(
        warnings, prefix=f"override-contract: WARN {args.task_id}: ")
    policy_summary = incompatibility_policy_summary(policy)
    print(
        f"override-contract: {status} {args.task_id}: {draws} draws, "
        f"{accepted_draws} accepted, {len(cases)} override cases, "
        f"{len(bands)} bands, {explicit_rejections} explicit combination "
        f"rejections; {policy_summary}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
