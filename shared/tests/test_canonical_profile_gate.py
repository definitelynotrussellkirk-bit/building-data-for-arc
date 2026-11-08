"""Canonical-profile floor gate — failure-class coverage.

Run: python3 -m pytest tests/test_canonical_profile_gate.py -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "cpg", ROOT / "scripts/canonical_profile_gate.py"
)
cpg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpg)

TASK = "fixtureprofile"
CANON_GRID = [[0, 2, 0], [2, 2, 2], [0, 2, 0]]  # 3x3 palette {0,2} -> (3,3,2)


def _install(monkeypatch, tmp_path, generator_module):
    canonical = tmp_path / "puzzles.jsonl"
    canonical.write_text(json.dumps({
        "task_id": TASK,
        "train": [{"input": CANON_GRID, "output": CANON_GRID}, "spurious-str"],
        "test": [{"input": CANON_GRID}],
    }) + "\n")
    monkeypatch.setattr(cpg, "CANONICAL", canonical)
    module_name = f"puzzle_generators.per_puzzle.{TASK}.generator"
    monkeypatch.setitem(sys.modules, module_name, generator_module)


def _gen_module(generate, self_check=lambda g: [], opt_out=None):
    mod = types.ModuleType("fixture_gen")
    mod.generate = generate
    mod.self_check = self_check
    if opt_out:
        mod.CANONICAL_PROFILE_OPT_OUT = opt_out
    return mod


def test_pass_when_draws_anchor_canonical(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path,
             _gen_module(lambda s, i, difficulty=None: CANON_GRID))
    audit = cpg.audit_task(TASK, per_band=5)
    assert audit["status"] == "PASS"
    assert audit["canonical_rejected"] == 0
    assert audit["exact_hits"] == audit["draws_total"]


def test_selfcheck_rejection_is_hard_fail(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path,
             _gen_module(lambda s, i, difficulty=None: CANON_GRID,
                         self_check=lambda g: ["nope"]))
    audit = cpg.audit_task(TASK, per_band=3)
    assert audit["status"] == "FAIL"
    assert audit["canonical_rejected"] == 2  # both canonical inputs
    assert any("REJECTS canonical input" in e for e in audit["errors"])


def test_zero_support_warns_default_fails_strict(monkeypatch, tmp_path):
    off_scale = [[1] * 12 for _ in range(12)]  # 12x12 palette {1}
    _install(monkeypatch, tmp_path,
             _gen_module(lambda s, i, difficulty=None: off_scale))
    default = cpg.audit_task(TASK, per_band=5)
    assert default["status"] == "WARN"
    assert any("ZERO" in w for w in default["warnings"])
    strict = cpg.audit_task(TASK, per_band=5, strict=True)
    assert strict["status"] == "FAIL"
    assert any("ZERO" in e for e in strict["errors"])


def test_opt_out_downgrades_to_loud_warning(monkeypatch, tmp_path):
    off_scale = [[1] * 12 for _ in range(12)]
    _install(monkeypatch, tmp_path,
             _gen_module(lambda s, i, difficulty=None: off_scale,
                         opt_out="intentional scale study, reviewed"))
    audit = cpg.audit_task(TASK, per_band=5, strict=True)
    assert audit["status"] == "WARN"
    assert any("OPT_OUT" in w for w in audit["warnings"])


def test_within_envelope_zero_exact_is_warn_even_strict(monkeypatch, tmp_path):
    # Same dims/palette band as canonical but a profile that never matches
    # exactly is the curriculum case: WARN, not FAIL, in both modes.
    canonical = tmp_path / "puzzles.jsonl"
    grid_a = [[0, 2], [2, 0]]                     # (2,2,2)
    grid_b = [[0, 2, 0, 2], [2, 0, 2, 0], [0, 2, 0, 2], [2, 0, 2, 0]]
    canonical.write_text(json.dumps({
        "task_id": TASK,
        "train": [{"input": grid_a, "output": grid_a},
                  {"input": grid_b, "output": grid_b}],
        "test": [],
    }) + "\n")
    monkeypatch.setattr(cpg, "CANONICAL", canonical)
    inside = [[0, 2, 2], [2, 0, 0], [2, 2, 0]]    # 3x3 inside 2..4 envelope
    monkeypatch.setitem(
        sys.modules, f"puzzle_generators.per_puzzle.{TASK}.generator",
        _gen_module(lambda s, i, difficulty=None: inside))
    audit = cpg.audit_task(TASK, per_band=5, strict=True)
    assert audit["status"] == "WARN"


def test_generation_crashes_are_loud(monkeypatch, tmp_path):
    def explode(s, i, difficulty=None):
        raise RuntimeError("boom")
    _install(monkeypatch, tmp_path, _gen_module(explode))
    audit = cpg.audit_task(TASK, per_band=4)
    assert audit["status"] == "FAIL"
    assert any("crashes" in e for e in audit["errors"])


# --- per-band coverage (v13-z a5df658a2503 WFB-002) ----------------------
#
# The verdict was POOLED-only: `exact_hits == 0` across all bands. A
# generator anchoring canonical scale solely in `easy` passed strict with
# medium 0/200 and hard 0/200 and strict_would_fail=False, and the per-band
# counts it had already collected were never consulted.
#
# Enforcing a floor by default would have been wrong: 35 of 60 sampled
# generators vary band scale, and several repairs document that as
# deliberate. So zero-support bands are always REPORTED and machine-readable,
# and blocking is opt-in via --min-band-support.


def _band_split_gen(easy_grid, other_grid):
    def generate(seed, index, difficulty=None):
        return easy_grid if difficulty == "easy" else other_grid
    return _gen_module(generate)


def test_zero_support_band_is_reported_when_pooled_passes(monkeypatch, tmp_path):
    off = [[0] * 7 for _ in range(7)]
    _install(monkeypatch, tmp_path, _band_split_gen(CANON_GRID, off))
    audit = cpg.audit_task(TASK, per_band=5, strict=True)
    # Pooled support exists, so the old zero-support check stays silent...
    assert audit["exact_hits"] > 0
    # ...but the starved bands are now visible rather than implied.
    assert audit["bands_with_zero_support"] == ["hard", "medium"]
    assert any("ZERO canonical-profile" in w for w in audit["warnings"])


def test_reporting_alone_does_not_fail_the_gate(monkeypatch, tmp_path):
    """Default must not churn the 35/60 of the corpus that varies band scale."""
    off = [[0] * 7 for _ in range(7)]
    _install(monkeypatch, tmp_path, _band_split_gen(CANON_GRID, off))
    audit = cpg.audit_task(TASK, per_band=5, strict=True)
    assert audit["status"] != "FAIL"
    assert not audit["errors"]
    assert audit.get("strict_would_fail") is False


def test_min_band_support_makes_it_blocking(monkeypatch, tmp_path):
    off = [[0] * 7 for _ in range(7)]
    _install(monkeypatch, tmp_path, _band_split_gen(CANON_GRID, off))
    audit = cpg.audit_task(TASK, per_band=5, strict=True, min_band_support=1)
    assert audit["status"] == "FAIL"
    assert audit["bands_below_floor"] == ["hard", "medium"]
    assert audit["strict_would_fail"] is True
    assert any("not cross-band coverage" in e for e in audit["errors"])


def test_min_band_support_warns_without_strict(monkeypatch, tmp_path):
    off = [[0] * 7 for _ in range(7)]
    _install(monkeypatch, tmp_path, _band_split_gen(CANON_GRID, off))
    audit = cpg.audit_task(TASK, per_band=5, strict=False, min_band_support=1)
    assert audit["status"] == "WARN"
    assert any("[FAIL under --strict]" in w for w in audit["warnings"])


def test_full_band_coverage_reports_nothing(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path,
             _gen_module(lambda s, i, difficulty=None: CANON_GRID))
    audit = cpg.audit_task(TASK, per_band=5, strict=True, min_band_support=1)
    assert audit["status"] == "PASS"
    assert audit["bands_with_zero_support"] == []
    assert "bands_below_floor" not in audit


# --- minority census crashes must not be silent (v13-z 80b1344c17c8 WFB-001) --
#
# The gate only errored when MORE THAN HALF the census crashed, so a run with
# 4 crashes and 56 good draws passed --strict saying nothing at all. Those
# seeds produce no training data and the crash never gets fixed.


def _sometimes_crashes(good_grid, crash_every):
    calls = {"n": 0}
    def generate(seed, index, difficulty=None):
        calls["n"] += 1
        if calls["n"] % crash_every == 0:
            raise RuntimeError("synthetic generation failure")
        return good_grid
    return _gen_module(generate)


def test_minority_crashes_fail_under_strict(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path, _sometimes_crashes(CANON_GRID, 5))
    audit = cpg.audit_task(TASK, per_band=5, strict=True)
    assert audit["crashes"] > 0
    assert audit["crashes"] <= audit["draws_total"]      # a MINORITY
    assert audit["status"] == "FAIL"
    assert any("generation crash" in e for e in audit["errors"])


def test_minority_crashes_warn_without_strict(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path, _sometimes_crashes(CANON_GRID, 5))
    audit = cpg.audit_task(TASK, per_band=5, strict=False)
    assert audit["crashes"] > 0
    assert audit["status"] == "WARN"
    assert audit["strict_would_fail"] is True
    assert any("[FAIL under --strict]" in w for w in audit["warnings"])


def test_no_crashes_stays_silent_about_crashes(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path,
             _gen_module(lambda s, i, difficulty=None: CANON_GRID))
    audit = cpg.audit_task(TASK, per_band=5, strict=True)
    assert audit["crashes"] == 0
    assert not any("crash" in m for m in audit["errors"] + audit["warnings"])


def test_require_pass_makes_cli_warning_blocking(monkeypatch, capsys):
    warning = {
        "status": "WARN",
        "canonical_inputs": 1,
        "canonical_rejected": 0,
        "draws_total": 3,
        "exact_hits": 3,
        "envelope_hits": 3,
        "crashes": 0,
        "errors": [],
        "warnings": ["synthetic advisory"],
    }
    monkeypatch.setattr(cpg, "audit_task", lambda *args, **kwargs: warning)

    monkeypatch.setattr(sys, "argv", ["canonical_profile_gate.py", TASK])
    assert cpg.main() == 0

    monkeypatch.setattr(
        sys, "argv",
        ["canonical_profile_gate.py", TASK, "--require-pass"],
    )
    assert cpg.main() == 1
    assert "blocking under --require-pass" in capsys.readouterr().out
