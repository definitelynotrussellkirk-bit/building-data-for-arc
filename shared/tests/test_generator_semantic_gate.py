"""Task-linked semantic gate — failure-class coverage.

Every fixture here is a SYNTHETIC generator module injected into sys.modules.
The gate is deliberately not exercised against the real per-puzzle corpus: those
files are edited concurrently, and a gate test that depends on them measures the
corpus, not the gate.

Run: python3 -m pytest tests/test_generator_semantic_gate.py -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "gsg", ROOT / "scripts/generator_semantic_gate.py"
)
gsg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gsg)

TASK = "fixturesemantic"
GRID = [[0, 2, 0], [2, 2, 2], [0, 2, 0]]


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

_DEFAULT_CANONICAL = [GRID]


def _install(monkeypatch, module, canonical=_DEFAULT_CANONICAL) -> None:
    """Inject a synthetic generator, and (by default) synthetic canonical inputs.

    `canonical=None` leaves the real `canonical_inputs` reader in place — used by
    the test that exercises the shared `_as_pairs` / `_norm_grid` normalizers
    end-to-end against a temp canonical file.
    """
    monkeypatch.setitem(
        sys.modules, f"puzzle_generators.per_puzzle.{TASK}.generator", module
    )
    if canonical is not None:
        monkeypatch.setattr(gsg, "canonical_inputs", lambda task_id: list(canonical))


def _gen_module(generate=None, **attrs):
    mod = types.ModuleType("fixture_semantic_gen")
    mod.generate = generate or (lambda seed, sample_index, difficulty=None: GRID)
    for name, value in attrs.items():
        setattr(mod, name, value)
    return mod


def _band_grid(seed, sample_index, difficulty=None):
    """A draw whose single cell encodes the band — lets a witness be band-local."""
    return [[{"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 0)]]


# ---------------------------------------------------------------------------
# 1. no declared hooks -> NO_CONTRACT, exit 0, LOUD advisory
# ---------------------------------------------------------------------------

def test_no_hooks_is_loud_advisory_not_a_failure(monkeypatch, capsys):
    _install(monkeypatch, _gen_module())
    audit = gsg.audit_task(TASK, per_band=3, lessons=2)
    assert audit["status"] == "NO_CONTRACT"
    assert audit["errors"] == []
    assert audit["hooks_declared"] == {
        "strict_canonical_like": False,
        "SEMANTIC_WITNESSES": False,
        "lesson_identifiable": False,
    }
    assert any(
        "no semantic contract declared" in a and a.startswith("LOUD:")
        for a in audit["advisories"]
    )

    code = gsg.main([TASK, "--per-band", "3", "--lessons", "2"])
    out = capsys.readouterr().out
    assert code == 0
    assert "LOUD: fixturesemantic: no semantic contract declared" in out
    assert "no-contract" in out


def test_no_hooks_exits_1_under_strict(monkeypatch, capsys):
    _install(monkeypatch, _gen_module())
    code = gsg.main([TASK, "--per-band", "3", "--lessons", "2", "--strict"])
    assert code == 1
    assert "no semantic contract declared" in capsys.readouterr().out


def test_empty_witness_dict_is_not_a_declaration(monkeypatch):
    _install(monkeypatch, _gen_module(SEMANTIC_WITNESSES={}))
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["status"] == "NO_CONTRACT"


# ---------------------------------------------------------------------------
# 2. strict_canonical_like with a pooled rate of 0 -> FAIL
# ---------------------------------------------------------------------------

def test_strict_canonical_like_zero_pooled_rate_fails(monkeypatch, capsys):
    _install(monkeypatch, _gen_module(
        strict_canonical_like=lambda g: ["wrong separator color", "wrong panel count"]
    ))
    audit = gsg.audit_task(TASK, per_band=5)
    assert audit["status"] == "FAIL"
    assert audit["strict_canonical"]["draws"] == 15
    assert audit["strict_canonical"]["hits"] == 0
    assert audit["strict_canonical"]["rate"] == 0.0
    assert any("ZERO of 15 census draws" in e for e in audit["errors"])
    # count-backed: the top reasons are carried, not just a verdict
    reasons = dict(tuple(r) for r in audit["strict_canonical"]["top_reasons"])
    assert reasons["wrong separator color"] == 15

    code = gsg.main([TASK, "--per-band", "5"])
    assert code == 2
    assert "ERROR:" in capsys.readouterr().out


def test_strict_canonical_like_all_lawful_passes(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: []))
    audit = gsg.audit_task(TASK, per_band=4)
    assert audit["status"] == "PASS"
    assert audit["strict_canonical"]["hits"] == 12
    assert audit["strict_canonical"]["rate"] == 1.0
    assert audit["census"]["per_band"] == {
        "easy": {"planned": 4, "draws": 4, "crashes": 0},
        "medium": {"planned": 4, "draws": 4, "crashes": 0},
        "hard": {"planned": 4, "draws": 4, "crashes": 0},
    }


def test_strict_canonical_like_partial_rate_passes(monkeypatch):
    # Support > 0 anywhere is the floor; a rate under 1.0 is not a failure.
    _install(monkeypatch, _gen_module(
        generate=_band_grid,
        strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["not easy-band"],
    ), canonical=[[[1]]])
    audit = gsg.audit_task(TASK, per_band=4)
    assert audit["status"] == "PASS"
    assert audit["strict_canonical"]["hits"] == 4
    assert audit["strict_canonical"]["per_band"]["hard"]["hits"] == 0


# ---------------------------------------------------------------------------
# 3. a declared witness that never fires -> FAIL
# ---------------------------------------------------------------------------

def test_declared_witness_that_never_fires_fails(monkeypatch):
    _install(monkeypatch, _gen_module(SEMANTIC_WITNESSES={
        "always": lambda g: True,
        "zero_length_ray": lambda g: False,
    }))
    audit = gsg.audit_task(TASK, per_band=6)
    assert audit["status"] == "FAIL"
    assert audit["witnesses"]["zero_length_ray"]["hits"] == 0
    assert audit["witnesses"]["zero_length_ray"]["draws"] == 18
    assert audit["witnesses"]["always"]["hits"] == 18
    assert any(
        "declared witness 'zero_length_ray' NEVER fires" in e
        for e in audit["errors"]
    )
    # the firing witness must NOT be reported as a problem
    assert not any("'always'" in e for e in audit["errors"])


# ---------------------------------------------------------------------------
# 4. a witness firing in some bands but not others -> WARN
# ---------------------------------------------------------------------------

def test_witness_missing_from_a_band_is_a_warning(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_band_grid,
        SEMANTIC_WITNESSES={"easy_only": lambda g: g[0][0] == 1},
    ))
    # per_band=15: pooled rate 1/3, so a missing band expected 5.0 firings —
    # comfortably above MIN_EXPECTED_FIRINGS, i.e. a judgeable gap.
    audit = gsg.audit_task(TASK, per_band=15)
    assert audit["status"] == "WARN"
    assert audit["errors"] == []
    stats = audit["witnesses"]["easy_only"]
    assert stats["hits"] == 15
    assert stats["bands_fired"] == ["easy"]
    assert stats["bands_missing"] == ["hard", "medium"]
    assert stats["bands_missing_judged"] == ["hard", "medium"]
    assert any("never in ['hard', 'medium']" in w for w in audit["warnings"])


def _rare_in_hard(rate_by_band):
    """Witness fires on a deterministic 1-in-k schedule per band.

    Uses the pinned seed itself, so the firing pattern is reproducible and the
    per-band rate is exactly controllable.
    """
    def _generate(seed, sample_index, difficulty=None):
        k = rate_by_band[difficulty]
        return [[1 if k and seed % k == 0 else 0]]
    return _generate


def test_rare_witness_missing_a_band_is_a_NOTE_not_a_warning(monkeypatch):
    """The 796907d6d950/template_size_6 class: lawful but rare -> no WARN.

    Fires ~1/3 of easy draws, ~1/4 of medium, never in hard at this census.
    Pooled rate is low enough that a hard-band zero is unsurprising, so the
    gate must NOT warn — no affordable census would ever clear it otherwise.
    """
    _install(monkeypatch, _gen_module(
        generate=_rare_in_hard({"easy": 3, "medium": 4, "hard": 0}),
        SEMANTIC_WITNESSES={"rare_branch": lambda g: g[0][0] == 1},
    ))
    audit = gsg.audit_task(TASK, per_band=6)
    stats = audit["witnesses"]["rare_branch"]
    assert stats["hits"] > 0                      # fires somewhere
    assert stats["per_band"]["hard"]["hits"] == 0  # but never in hard
    assert stats["bands_missing"] == ["hard"]
    assert stats["bands_missing_judged"] == []
    assert stats["bands_missing_underpowered"] == ["hard"]
    assert stats["per_band"]["hard"]["expected"] < 3.0
    assert audit["status"] == "PASS"
    assert audit["warnings"] == []
    assert any("too rare to judge per-band" in n for n in audit["notes"])
    # the NOTE must quote the census that WOULD test it
    assert any("raise --per-band to ~" in n for n in audit["notes"])


def test_a_note_never_changes_status_or_exit_code(monkeypatch, capsys):
    _install(monkeypatch, _gen_module(
        generate=_rare_in_hard({"easy": 3, "medium": 4, "hard": 0}),
        SEMANTIC_WITNESSES={"rare_branch": lambda g: g[0][0] == 1},
    ))
    assert gsg.main([TASK, "--per-band", "6"]) == 0
    assert gsg.main([TASK, "--per-band", "6", "--strict"]) == 0
    out = capsys.readouterr().out
    assert "NOTE:" in out
    assert "WARN:" not in out


def test_common_witness_absent_from_one_band_still_warns(monkeypatch):
    """Common elsewhere, absent in one band = a real gap. Must still WARN."""
    _install(monkeypatch, _gen_module(
        generate=_band_grid,
        SEMANTIC_WITNESSES={"not_hard": lambda g: g[0][0] in (1, 2)},
    ))
    # 150 is the census the battery actually runs; 30 is a cheaper one. A real
    # band gap must warn at BOTH — the guard suppresses rarity, never absence.
    for per_band in (30, 150):
        audit = gsg.audit_task(TASK, per_band=per_band)
        stats = audit["witnesses"]["not_hard"]
        assert stats["hits"] == 2 * per_band
        assert stats["draws"] == 3 * per_band
        assert stats["rate"] == 2 / 3
        assert stats["per_band"]["hard"]["expected"] == per_band * 2 / 3
        assert stats["bands_missing_judged"] == ["hard"]
        assert stats["bands_missing_underpowered"] == []
        assert audit["status"] == "WARN"
        assert audit["notes"] == []
        assert any(
            "never in ['hard'] where its pooled rate 66.7% predicted" in w
            for w in audit["warnings"]
        )
    assert gsg.main([TASK, "--per-band", "150", "--strict"]) == 1


def test_zero_pooled_firings_still_fails_under_the_guard(monkeypatch):
    """The guard must NEVER soften the declared-but-never-generated defect."""
    _install(monkeypatch, _gen_module(SEMANTIC_WITNESSES={
        "never": lambda g: False,
    }))
    for per_band in (2, 6, 50):
        audit = gsg.audit_task(TASK, per_band=per_band)
        assert audit["status"] == "FAIL", per_band
        assert audit["notes"] == [], per_band
        assert any("NEVER fires" in e for e in audit["errors"]), per_band


def test_min_expected_boundary_is_exact(monkeypatch):
    # rate 1/4 exactly: expected = 3.0 at n = 12 -> judged (>= floor);
    # expected = 2.75 at n = 11 -> under-powered.
    def _make(n_hits_per_fired_band, per_band):
        def _generate(seed, sample_index, difficulty=None):
            if difficulty == "hard":
                return [[0]]
            return [[1 if sample_index % 2 == 0 else 0]]
        return _generate

    _install(monkeypatch, _gen_module(
        generate=lambda seed, si, difficulty=None: (
            [[0]] if difficulty == "hard" else [[1 if si % 2 == 0 else 0]]
        ),
        SEMANTIC_WITNESSES={"w": lambda g: g[0][0] == 1},
    ))
    audit = gsg.audit_task(TASK, per_band=8)
    stats = audit["witnesses"]["w"]
    expected = stats["per_band"]["hard"]["expected"]
    judged = stats["bands_missing_judged"] == ["hard"]
    # whichever side of the floor this census lands on, the classification and
    # the emitted message must agree — no cell is both judged and noted.
    assert (expected >= 3.0) == judged
    assert not (stats["bands_missing_judged"] and stats["bands_missing_underpowered"])
    assert bool(audit["warnings"]) == judged
    assert bool(audit["notes"]) != judged


def test_census_for_power_reports_an_affordable_target():
    assert gsg._census_for_power(0.5) == 6
    assert gsg._census_for_power(0.1) == 30
    assert gsg._census_for_power(0.033) == 91     # the 796907d6d950 rare cell
    assert gsg._census_for_power(0.0) == 0


def test_band_partial_witness_exits_1_under_strict(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_band_grid,
        SEMANTIC_WITNESSES={"easy_only": lambda g: g[0][0] == 1},
    ))
    assert gsg.main([TASK, "--per-band", "12"]) == 0
    assert gsg.main([TASK, "--per-band", "12", "--strict"]) == 1


# ---------------------------------------------------------------------------
# 5. a hook that raises -> FAIL with the message recorded
# ---------------------------------------------------------------------------

def _boom(*_args):
    raise RuntimeError("boom in the hook")


def test_strict_hook_that_raises_fails_with_message(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=_boom))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "FAIL"
    assert audit["strict_canonical"]["hook_errors"] == 9
    joined = " ".join(audit["errors"])
    assert "raised RuntimeError: boom in the hook" in joined
    assert "strict_canonical_like raised/misreturned on 9/9 draws" in joined


def test_all_hook_calls_erroring_does_not_fabricate_a_zero_rate(monkeypatch):
    # Nothing was measured, so the gate must not ALSO claim "0% canonical-like":
    # the raise is the honest finding.
    _install(monkeypatch, _gen_module(strict_canonical_like=_boom))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "FAIL"
    assert audit["strict_canonical"]["measured"] == 0
    assert not any("ZERO of" in e for e in audit["errors"])


def test_witness_that_raises_fails_with_message(monkeypatch):
    _install(monkeypatch, _gen_module(SEMANTIC_WITNESSES={"explodes": _boom}))
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["status"] == "FAIL"
    assert audit["witnesses"]["explodes"]["hook_errors"] == 6
    assert any("witness 'explodes' raised/misreturned" in e for e in audit["errors"])


# ---------------------------------------------------------------------------
# strict_canonical_like return conventions — dispatched on TYPE, never on
# truthiness (contract v1 amended 2026-07-24). Five rows, one test each.
# ---------------------------------------------------------------------------

def test_return_empty_list_means_lawful(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: []))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "PASS"
    assert audit["strict_canonical"]["hits"] == 9
    assert audit["strict_canonical"]["rate"] == 1.0
    # the trap: [] is falsy, and must NOT be read as "rejected"
    assert audit["errors"] == []


def test_return_reason_list_means_not_lawful(monkeypatch):
    _install(monkeypatch, _gen_module(
        strict_canonical_like=lambda g: ["separator color 9, canonical is 5"]))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "FAIL"
    assert audit["strict_canonical"]["hits"] == 0
    assert dict(tuple(r) for r in audit["strict_canonical"]["top_reasons"]) == {
        "separator color 9, canonical is 5": 9
    }


def test_return_true_means_lawful(monkeypatch):
    # The trap: True must NOT be read as "one finding" (i.e. a rejection).
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: True))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "PASS"
    assert audit["strict_canonical"]["hits"] == 9
    assert audit["strict_canonical"]["rate"] == 1.0
    assert audit["strict_canonical"]["hook_errors"] == 0
    assert audit["strict_canonical"]["top_reasons"] == []


def test_return_false_means_not_lawful_with_recorded_reason(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: False))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "FAIL"
    assert audit["strict_canonical"]["hits"] == 0
    assert audit["strict_canonical"]["hook_errors"] == 0
    assert dict(tuple(r) for r in audit["strict_canonical"]["top_reasons"]) == {
        "predicate returned False": 9
    }
    assert any("ZERO of 9 census draws" in e for e in audit["errors"])


def test_bool_and_empty_list_never_collapse(monkeypatch):
    """`[]` (lawful) and `False` (rejected) are both falsy — never conflate."""
    lawful, _ = gsg._call_reasons_hook(lambda g: [], GRID, allow_bool=True)
    rejected, _ = gsg._call_reasons_hook(lambda g: False, GRID, allow_bool=True)
    true_form, _ = gsg._call_reasons_hook(lambda g: True, GRID, allow_bool=True)
    listed, _ = gsg._call_reasons_hook(lambda g: ["r"], GRID, allow_bool=True)
    assert lawful == [] and true_form == []
    assert rejected == ["predicate returned False"] and listed == ["r"]


def test_non_list_non_bool_return_is_a_contract_failure(monkeypatch):
    for bad in ("nope", 1, None, {"reason": "x"}):
        _install(monkeypatch, _gen_module(strict_canonical_like=lambda g, b=bad: b))
        audit = gsg.audit_task(TASK, per_band=2)
        assert audit["status"] == "FAIL", bad
        assert any("contract is list[str] | bool" in e for e in audit["errors"]), bad


def test_lesson_hook_still_rejects_bool(monkeypatch):
    # Spec section 3 was NOT amended: lesson_identifiable stays list[str]-only.
    _install(monkeypatch, _gen_module(lesson_identifiable=lambda d, q: True))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(2))
    audit = gsg.audit_task(TASK, lessons=2)
    assert audit["status"] == "FAIL"
    joined = " ".join(audit["errors"])
    assert "returned bool True" in joined
    assert "contract is list[str] (" in joined


# ---------------------------------------------------------------------------
# minimum strict rate — zero stays a hard FAIL, low-but-nonzero is a WARN
# ---------------------------------------------------------------------------

def _rate_gen(one_in):
    """Fires strict-lawful on exactly 1 of every `one_in` pinned draws."""
    return lambda seed, si, difficulty=None: [[0 if seed % one_in else 1]]


def test_rate_below_floor_warns_but_zero_still_fails(monkeypatch):
    module = _gen_module(
        generate=_rate_gen(50),                       # ~2% lawful
        strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["off-manifold"],
    )
    _install(monkeypatch, module, canonical=[[[1]]])
    audit = gsg.audit_task(TASK, per_band=60, min_strict_frac=0.05)
    assert 0 < audit["strict_rate"] < 0.05
    assert audit["status"] == "WARN"          # low-but-nonzero -> WARN
    assert audit["errors"] == []              # NOT a failure
    assert audit["strict_rate_below_floor"] is True
    assert any("is below the 5.0% floor [cli]" in w for w in audit["warnings"])

    # ZERO support remains a hard FAIL — the floor must never soften it.
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: ["nope"]),
             canonical=[[[1]]])
    zero = gsg.audit_task(TASK, per_band=10, min_strict_frac=0.05)
    assert zero["status"] == "FAIL"
    assert zero["strict_rate"] == 0.0
    assert zero["strict_rate_below_floor"] is None   # never reached the floor test
    assert any("ZERO of" in e for e in zero["errors"])


def test_rate_above_floor_passes(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_rate_gen(3),                        # ~33% lawful
        strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["off-manifold"],
    ), canonical=[[[1]]])
    audit = gsg.audit_task(TASK, per_band=60, min_strict_frac=0.05)
    assert audit["strict_rate"] > 0.05
    assert audit["status"] == "PASS"
    assert audit["strict_rate_below_floor"] is False


def test_min_strict_frac_zero_disables_the_floor(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_rate_gen(50),
        strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["off-manifold"],
    ), canonical=[[[1]]])
    audit = gsg.audit_task(TASK, per_band=60, min_strict_frac=0.0)
    assert audit["status"] == "PASS"
    assert audit["strict_rate_below_floor"] is False


def test_declared_floor_overrides_the_cli_floor(monkeypatch):
    """The 0ae119475d57 class: 12% support where the task promises ~100%."""
    _install(monkeypatch, _gen_module(
        generate=_rate_gen(8),                        # ~12% lawful
        strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["off-manifold"],
        MIN_STRICT_FRAC=0.9,
    ), canonical=[[[1]]])
    audit = gsg.audit_task(TASK, per_band=60, min_strict_frac=0.05)
    assert audit["strict_rate"] > 0.05            # would pass the global floor
    assert audit["min_strict_frac"] == 0.9
    assert audit["min_strict_frac_source"] == "declared"
    assert audit["status"] == "WARN"
    assert any("below the 90.0% floor [declared]" in w for w in audit["warnings"])
    assert gsg.main([TASK, "--per-band", "60", "--strict"]) == 1


def test_declared_floor_can_defend_a_broad_distribution(monkeypatch):
    """56f043832ecb/1672855ac30c class: deliberately broader than canonical."""
    _install(monkeypatch, _gen_module(
        generate=_rate_gen(50),                       # ~2% lawful
        strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["off-manifold"],
        MIN_STRICT_FRAC=0.01,
    ), canonical=[[[1]]])
    audit = gsg.audit_task(TASK, per_band=60, min_strict_frac=0.05)
    assert audit["status"] == "PASS"
    assert audit["min_strict_frac_source"] == "declared"
    assert audit["warnings"] == []


def test_invalid_declared_floor_is_loud_and_falls_back(monkeypatch):
    for bad in ("high", True, -0.5, 1.5):
        _install(monkeypatch, _gen_module(
            generate=_rate_gen(50),
            strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["off"],
            MIN_STRICT_FRAC=bad,
        ), canonical=[[[1]]])
        audit = gsg.audit_task(TASK, per_band=60, min_strict_frac=0.05)
        assert audit["min_strict_frac"] == 0.05, bad
        assert audit["min_strict_frac_source"] == "cli", bad
        assert any("MIN_STRICT_FRAC" in w and "falling back" in w
                   for w in audit["warnings"]), bad


def test_flat_rate_keys_are_machine_readable(monkeypatch, tmp_path):
    _install(monkeypatch, _gen_module(
        generate=_rate_gen(4),
        strict_canonical_like=lambda g: [] if g[0][0] == 1 else ["off-manifold"],
    ), canonical=[[[1]]])
    out = tmp_path / "rates.json"
    gsg.main([TASK, "--per-band", "20", "--json-out", str(out)])
    row = json.loads(out.read_text())["audits"][0]
    # flat per-task keys, no walking into the nested census
    assert row["strict_hits"] == row["strict_canonical"]["hits"]
    assert row["strict_draws"] == row["strict_canonical"]["draws"]
    assert row["strict_rate"] == row["strict_canonical"]["rate"]
    assert row["strict_draws"] == 60
    assert 0.0 < row["strict_rate"] <= 1.0
    assert row["min_strict_frac"] == 0.05


def test_flat_rate_keys_are_none_without_the_hook(monkeypatch, tmp_path):
    # None, not 0.0 — an undeclared hook must not read as a zero rate.
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True}))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["strict_rate"] is None
    assert audit["strict_hits"] is None
    assert audit["strict_rate_below_floor"] is None


# ---------------------------------------------------------------------------
# 3b. canonical acceptance
# ---------------------------------------------------------------------------

def test_hook_rejecting_a_canonical_input_fails(monkeypatch):
    other = [[7, 7], [7, 7]]
    _install(monkeypatch, _gen_module(
        strict_canonical_like=lambda g: [] if g == GRID else ["not a 3x3 plus"],
    ), canonical=[GRID, other, GRID])
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "FAIL"
    stats = audit["strict_canonical"]
    assert stats["canonical_inputs"] == 3
    assert stats["canonical_rejected"] == 1
    assert stats["canonical_rejection_examples"][0]["index"] == 1
    assert stats["canonical_rejection_examples"][0]["reasons"] == ["not a 3x3 plus"]
    assert any(
        "REJECTS 1/3 canonical inputs" in e and "#1 (2x2): not a 3x3 plus" in e
        for e in audit["errors"]
    )


def test_bool_hook_rejecting_canonical_input_fails(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: g == GRID),
             canonical=[GRID, [[7]]])
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["status"] == "FAIL"
    assert audit["strict_canonical"]["canonical_rejected"] == 1
    assert audit["strict_canonical"]["canonical_rejection_examples"][0][
        "reasons"] == ["predicate returned False"]


def test_canonical_acceptance_passes_when_hook_owns_its_inputs(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: []),
             canonical=[GRID, [[7]], [[1, 2], [3, 4]]])
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "PASS"
    assert audit["strict_canonical"]["canonical_inputs"] == 3
    assert audit["strict_canonical"]["canonical_rejected"] == 0
    assert audit["strict_canonical"]["canonical_hook_errors"] == 0


def test_missing_canonical_inputs_is_loud(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=lambda g: []),
             canonical=[])
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["status"] == "FAIL"
    assert any("NO canonical inputs were found" in e for e in audit["errors"])


def test_canonical_hook_error_is_reported_separately(monkeypatch):
    _install(monkeypatch, _gen_module(strict_canonical_like=_boom))
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["strict_canonical"]["canonical_hook_errors"] == 1
    assert any("1/1 CANONICAL inputs" in e for e in audit["errors"])


def test_canonical_inputs_read_through_the_shared_normalizers(monkeypatch, tmp_path):
    """Row-string grids and a bare-dict `test` split must reach the hook as ints."""
    import scripts.canonical_profile_gate as cpg

    canonical = tmp_path / "puzzles.jsonl"
    canonical.write_text(json.dumps({
        "task_id": TASK,
        # row-string encoding (609/4341 canonical rows use it)
        "train": [{"input": ["020", "222", "020"], "output": ["020"]}],
        # singleton test split stored as a BARE DICT (1239/4350 rows)
        "test": {"input": [[1, 1], [1, 1]]},
    }) + "\n")
    monkeypatch.setattr(cpg, "CANONICAL", canonical)

    seen: list = []

    def _hook(grid):
        seen.append(grid)
        return []

    _install(monkeypatch, _gen_module(strict_canonical_like=_hook), canonical=None)
    audit = gsg.audit_task(TASK, per_band=1)
    assert audit["strict_canonical"]["canonical_inputs"] == 2
    assert audit["strict_canonical"]["canonical_rejected"] == 0
    # the row-string row arrived as ints, and the bare-dict test split arrived
    assert seen[0] == [[0, 2, 0], [2, 2, 2], [0, 2, 0]]
    assert seen[1] == [[1, 1], [1, 1]]


def test_generate_that_raises_is_counted_and_fails(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_boom, strict_canonical_like=lambda g: []
    ))
    audit = gsg.audit_task(TASK, per_band=4)
    assert audit["status"] == "FAIL"
    assert audit["census"]["crashes"] == 12
    assert audit["census"]["draws"] == 0
    assert any("census draws CRASHED" in e for e in audit["errors"])


def test_uncallable_hook_declaration_fails(monkeypatch):
    _install(monkeypatch, _gen_module(
        strict_canonical_like="yes please", SEMANTIC_WITNESSES={"x": 3}
    ))
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["status"] == "FAIL"
    joined = " ".join(audit["errors"])
    assert "strict_canonical_like is str" in joined
    assert "SEMANTIC_WITNESSES['x'] is int" in joined


def test_import_failure_is_loud(monkeypatch):
    audit = gsg.audit_task("no_such_generator_fixture", per_band=2)
    assert audit["status"] == "IMPORT_FAIL"
    assert any("generator import failed" in e for e in audit["errors"])
    assert gsg.main(["no_such_generator_fixture", "--per-band", "2"]) == 2


# ---------------------------------------------------------------------------
# lesson_identifiable (hook 3) — materialization is stubbed so the test never
# needs Racket or a real canonical rule.
# ---------------------------------------------------------------------------

def _fake_lessons(n, *, demos=3, bands=("easy", "medium", "hard")):
    """Stub materializer.

    Mirrors the real signature (v1.1 added `bands` / `pass_difficulty` /
    `oracle_factory`) and hands back lessons carrying the same replay fields the
    real one does — band, seed, sample_index — so the scorer's evidence path is
    exercised without Racket.
    """
    def _materialize(task_id, count, *, n_demos, n_queries=1,
                     bands=bands, pass_difficulty=True, legacy=False,
                     oracle_factory=None):
        _materialize.seen = {"task_id": task_id, "count": count,
                             "n_demos": n_demos, "n_queries": n_queries,
                             "bands": tuple(bands),
                             "pass_difficulty": pass_difficulty,
                             "legacy": legacy}
        if legacy:
            bands = ("legacy",)
        return ([
            {"index": i, "band": bands[i % len(bands)], "seed": 1000 + i,
             "sample_index": i * 11,
             "difficulty_passed": pass_difficulty,
             "replay": (f"band={bands[i % len(bands)]} seed={1000 + i} "
                        f"sample_index={i * 11}"),
             "demos": [{"input": GRID, "output": GRID}] * n_demos,
             "query": {"input": GRID, "output": GRID}}
            for i in range(n)
        ], [])
    return _materialize


def test_unidentifiable_lesson_fails(monkeypatch):
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: (
            ["compatible with all 24 quadrant priority orders"]
        ),
    ))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(4))
    audit = gsg.audit_task(TASK, lessons=4)
    assert audit["status"] == "FAIL"
    assert audit["lessons"]["materialized"] == 4
    assert audit["lessons"]["unidentifiable"] == 4
    assert audit["lessons"]["identifiable"] == 0
    assert any("4/4 lessons are UNIDENTIFIABLE" in e for e in audit["errors"])
    assert any("quadrant priority" in e for e in audit["errors"])


def test_identifiable_lessons_pass_and_honor_examples_needed(monkeypatch):
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: [],
        EXAMPLES_NEEDED=4,
    ))
    materialize = _fake_lessons(3)
    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    audit = gsg.audit_task(TASK, lessons=3)
    assert audit["status"] == "PASS"
    assert audit["lessons"]["identifiable"] == 3
    assert audit["lessons"]["n_demos"] == 4
    assert audit["lessons"]["n_demos_source"] == "EXAMPLES_NEEDED"
    assert materialize.seen == {
        "task_id": TASK, "count": 3, "n_demos": 4, "n_queries": 1,
        "bands": ("easy", "medium", "hard"), "pass_difficulty": True,
        "legacy": False,
    }


def test_default_examples_needed_is_three(monkeypatch):
    _install(monkeypatch, _gen_module(lesson_identifiable=lambda d, q: []))
    materialize = _fake_lessons(2)
    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    gsg.audit_task(TASK, lessons=2)
    assert materialize.seen["n_demos"] == 3


def test_zero_materialized_lessons_fails(monkeypatch):
    _install(monkeypatch, _gen_module(lesson_identifiable=lambda d, q: []))
    monkeypatch.setattr(
        gsg, "materialize_lessons",
        lambda task_id, count, *, n_demos, n_queries=1, bands=None,
        pass_difficulty=True, legacy=False, oracle_factory=None: (
            [], ["RACKET_MISSING: racket not on PATH"]
        ),
    )
    audit = gsg.audit_task(TASK, lessons=5)
    assert audit["status"] == "FAIL"
    assert audit["lessons"]["materialized"] == 0
    joined = " ".join(audit["errors"])
    assert "RACKET_MISSING" in joined
    assert "ZERO of 5" in joined


def test_lesson_hook_that_raises_fails(monkeypatch):
    _install(monkeypatch, _gen_module(lesson_identifiable=_boom))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(2))
    audit = gsg.audit_task(TASK, lessons=2)
    assert audit["status"] == "FAIL"
    assert audit["lessons"]["hook_errors"] == 2
    assert any("raised RuntimeError: boom in the hook" in e for e in audit["errors"])


# ---------------------------------------------------------------------------
# 6. determinism + JSON schema
# ---------------------------------------------------------------------------

def _seed_sensitive(seed, sample_index, difficulty=None):
    """Output depends on the pinned seed, so counts are non-trivial."""
    return [[seed % 3]]


def test_two_runs_with_the_same_args_are_identical(monkeypatch):
    module = _gen_module(
        generate=_seed_sensitive,
        strict_canonical_like=lambda g: [] if g[0][0] == 0 else ["seed%3!=0"],
        SEMANTIC_WITNESSES={
            "residue_0": lambda g: g[0][0] == 0,
            "residue_1": lambda g: g[0][0] == 1,
            "residue_2": lambda g: g[0][0] == 2,
        },
    )
    _install(monkeypatch, module)
    first = gsg.audit_task(TASK, per_band=25)
    second = gsg.audit_task(TASK, per_band=25)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    # non-degenerate: the census actually splits across the three residues
    assert 0 < first["strict_canonical"]["hits"] < first["strict_canonical"]["draws"]
    assert sum(s["hits"] for s in first["witnesses"].values()) == 75


def test_json_out_is_count_backed(monkeypatch, tmp_path):
    _install(monkeypatch, _gen_module(
        generate=_seed_sensitive,
        SEMANTIC_WITNESSES={"residue_0": lambda g: g[0][0] == 0},
    ))
    out = tmp_path / "semantic.json"
    gsg.main([TASK, "--per-band", "5", "--json-out", str(out)])
    payload = json.loads(out.read_text())
    # v1.1 of the contract adds keys; every v1 key below is still asserted.
    assert payload["schema_version"] == 2
    assert payload["gate"] == "generator_semantic_gate"
    row = payload["audits"][0]
    assert row["task_id"] == TASK
    assert set(row) >= {
        "task_id", "status", "hooks_declared", "census", "strict_canonical",
        "witnesses", "lessons", "advisories", "errors", "warnings",
        "per_band", "lessons_requested", "witness_names",
    }
    stats = row["witnesses"]["residue_0"]
    assert stats["draws"] == 15
    assert set(stats["per_band"]) == {"easy", "medium", "hard"}
    assert all({"draws", "hits"} <= set(r) for r in stats["per_band"].values())


def test_census_seeds_match_the_profile_floor(monkeypatch):
    """The census must be the SAME population the profile floor measures."""
    from scripts.canonical_profile_gate import _pinned_seed as profile_seed

    seen: list[tuple[int, int, str]] = []

    def _record(seed, sample_index, difficulty=None):
        seen.append((seed, sample_index, difficulty))
        return GRID

    _install(monkeypatch, _gen_module(
        generate=_record, strict_canonical_like=lambda g: []
    ))
    gsg.audit_task(TASK, per_band=2)
    expected = [
        (profile_seed(TASK, band, i),
         profile_seed(TASK, band, i) % 7919 + i,
         band)
        for band in ("easy", "medium", "hard")
        for i in range(2)
    ]
    assert seen == expected


# ===========================================================================
# contract v1.1 (2026-07-25) — the five opt-in mechanisms and the two
# reporting upgrades. Every one of these is absent from the legacy corpus, so
# a fixture is the ONLY place they can be exercised.
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. rival-disagreement witnesses — "the witness fired" is not evidence
# ---------------------------------------------------------------------------

def _fake_oracle(apply_fn, *, ready=True, error=None):
    """A stand-in for the canonical Racket rule.

    `_RuleOracle` is patched wholesale so the rival path can be tested without
    Racket, a bundle, or a canonical rule on disk.
    """
    class _Oracle:
        def __init__(self, task_id):
            self.task_id = task_id
            self.bundle = object()
            self.bridge = object() if ready else None
            self.fn_name = "rule"
            self.error = error
            _Oracle.instances.append(self)

        @property
        def ready(self):
            return ready

        def apply(self, grid):
            if not ready:
                return None, error
            return apply_fn(grid), None

        def close(self):
            _Oracle.closed += 1

    _Oracle.instances = []
    _Oracle.closed = 0
    return _Oracle


# The fixture task: `generate` returns a 1x1 grid whose value is the seed % 3.
# The authoritative "rule" doubles the cell. A rival that also doubles AGREES
# everywhere (proves nothing); a rival that only differs on value 1 disagrees
# exactly where the `marks_one` witness fires.
def _cell(seed, sample_index, difficulty=None):
    return [[seed % 3]]


def _double(grid):
    return [[grid[0][0] * 2]]


def test_rival_claim_is_verified_when_a_named_rival_disagrees(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"marks_one": lambda g: g[0][0] == 1},
        SEMANTIC_RIVALS={"keeps_value": lambda g: [[g[0][0]]]},
        WITNESS_RIVALS={"marks_one": ["keeps_value"]},
    ))
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(_double))
    audit = gsg.audit_task(TASK, per_band=30)
    claim = audit["witnesses"]["marks_one"]["rival_claim"]
    assert claim["checked"] > 0
    # value 1 doubles to 2, the rival keeps 1 -> it disagrees on every firing
    assert claim["claim_holds"] == claim["checked"]
    assert claim["claim_violated"] == 0
    assert claim["per_rival_disagreements"]["keeps_value"] == claim["checked"]
    assert audit["status"] == "PASS"
    assert audit["weak_witnesses"] == []
    assert audit["rival_claims"]["marks_one"] is claim


def test_witness_that_proves_nothing_fails(monkeypatch):
    """The measured 600/600-vs-600/600 defect: the rival agrees everywhere."""
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"marks_one": lambda g: g[0][0] == 1},
        SEMANTIC_RIVALS={"also_doubles": _double},
        WITNESS_RIVALS={"marks_one": ["also_doubles"]},
    ))
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(_double))
    audit = gsg.audit_task(TASK, per_band=30)
    claim = audit["witnesses"]["marks_one"]["rival_claim"]
    assert claim["checked"] > 0
    assert claim["claim_holds"] == 0
    assert claim["claim_violated"] == claim["checked"]
    assert audit["status"] == "FAIL"
    assert any("PROVES NOTHING" in e for e in audit["errors"])
    # the witness itself still fired — firing is exactly what proves nothing
    assert audit["witnesses"]["marks_one"]["hits"] > 0


def test_partial_rival_disagreement_warns_with_a_replay_tuple(monkeypatch):
    # The rival differs only when the cell is 1 AND the seed is even, so the
    # claim holds on some firings and not others.
    def _sometimes(grid):
        return [[grid[0][0] * 2]] if grid[0][0] != 1 else [[99]]

    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"marks_one": lambda g: g[0][0] in (1, 2)},
        SEMANTIC_RIVALS={"partial": _sometimes},
        WITNESS_RIVALS={"marks_one": "partial"},        # str shorthand
    ))
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(_double))
    audit = gsg.audit_task(TASK, per_band=30)
    claim = audit["witnesses"]["marks_one"]["rival_claim"]
    assert claim["claim_holds"] > 0 and claim["claim_violated"] > 0
    assert audit["status"] == "WARN"
    assert any("rival claim holds on only" in w for w in audit["warnings"])
    example = claim["violation_examples"][0]
    assert {"band", "seed", "sample_index"} <= set(example)
    assert example["replay"].startswith("band=")
    assert example["grid_preview"]["shape"] == [1, 1]
    assert example["grid_preview"]["rows"] in (["1"], ["2"])
    assert any("counterexample grid=" in warning for warning in audit["warnings"])


def test_rival_claim_that_cannot_be_verified_is_an_error(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"marks_one": lambda g: g[0][0] == 1},
        SEMANTIC_RIVALS={"keeps_value": lambda g: [[g[0][0]]]},
        WITNESS_RIVALS={"marks_one": ["keeps_value"]},
    ))
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(
        _double, ready=False, error="RACKET_MISSING: racket not on PATH"))
    audit = gsg.audit_task(TASK, per_band=10)
    assert audit["status"] == "FAIL"
    assert any("could NOT be verified" in e and "RACKET_MISSING" in e
               for e in audit["errors"])


def test_rival_that_raises_is_counted_and_fails(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"marks_one": lambda g: g[0][0] == 1},
        SEMANTIC_RIVALS={"explodes": _boom},
        WITNESS_RIVALS={"marks_one": ["explodes"]},
    ))
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(_double))
    audit = gsg.audit_task(TASK, per_band=10)
    assert audit["status"] == "FAIL"
    claim = audit["witnesses"]["marks_one"]["rival_claim"]
    assert claim["rival_errors"] == claim["checked"]
    assert any("rival check errored" in e for e in audit["errors"])


def test_rival_declaration_errors_are_loud(monkeypatch):
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True},
        SEMANTIC_RIVALS={"ok": lambda g: g, "bad": 3},
        WITNESS_RIVALS={"always": ["nope"], "ghost": ["ok"]},
    ))
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["status"] == "FAIL"
    joined = " ".join(audit["errors"])
    assert "SEMANTIC_RIVALS['bad'] is int" in joined
    assert "names ['nope'] which are not in SEMANTIC_RIVALS" in joined
    assert "names witness 'ghost'" in joined


def test_witness_without_a_rival_claim_is_reported_weak(monkeypatch, capsys):
    """Weak is REPORTED (summary + per-witness line + JSON), not warned.

    Every witness in the hooked corpus is in this state, so a default WARN
    would flip the whole hooked corpus and get ignored. --require-rival-witness
    is the opt-in strictness.
    """
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True}))
    audit = gsg.audit_task(TASK, per_band=4)
    assert audit["weak_witnesses"] == ["always"]
    assert audit["status"] == "PASS"
    assert audit["warnings"] == []
    assert audit["notes"] == []

    assert gsg.main([TASK, "--per-band", "4"]) == 0
    out = capsys.readouterr().out
    assert "weak=1/1 (no rival claim)" in out
    assert "no rival claim (WEAK)" in out

    strictaudit = gsg.audit_task(TASK, per_band=4, require_rival_witness=True)
    assert strictaudit["status"] == "WARN"
    assert any("is WEAK" in w for w in strictaudit["warnings"])
    assert gsg.main([TASK, "--per-band", "4",
                     "--require-rival-witness", "--strict"]) == 1


def test_branch_witness_without_rival_claim_is_positive_coverage(monkeypatch):
    """Branch-only evidence must not fall through into rival-claim handling."""
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True},
        BRANCH_WITNESSES={"always"},
    ))
    audit = gsg.audit_task(TASK, per_band=4, require_rival_witness=True)
    assert audit["status"] == "PASS"
    assert audit["branch_witnesses"] == ["always"]
    assert audit["weak_witnesses"] == []
    assert audit["rival_claims"] == {}


# ---------------------------------------------------------------------------
# 2. replayable lesson evidence — band, seed, sample_index AND the survivor
# ---------------------------------------------------------------------------

def test_unidentifiable_lesson_reports_replay_tuple_and_named_survivor(monkeypatch):
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: ["query answer not pinned"],
        # `survives` reproduces the identity demos AND the identity query, so
        # the lesson never distinguishes it; `refuted` gets the demos wrong.
        LESSON_COMPETITORS={
            "survives": lambda g: [list(r) for r in g],
            "refuted": lambda g: [[9]],
        },
    ))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(3))
    audit = gsg.audit_task(TASK, lessons=3)
    assert audit["status"] == "FAIL"
    example = audit["lessons"]["unidentifiable_examples"][0]
    assert example["band"] in ("easy", "medium", "hard")
    assert isinstance(example["seed"], int)
    assert isinstance(example["sample_index"], int)
    assert example["replay"] == (
        f"band={example['band']} seed={example['seed']} "
        f"sample_index={example['sample_index']}"
    )
    assert example["survivors"] == ["survives"]
    assert example["survived_all"] == ["survives"]
    assert example["survivor_source"] == "LESSON_COMPETITORS"
    assert audit["lessons"]["competitor_survivor_counts"] == {"survives": 3}
    # the replay tuple and the survivor both reach the operator-facing error
    joined = " ".join(audit["errors"])
    assert "band=" in joined and "sample_index=" in joined
    assert "survivors: ['survives']" in joined


def test_unidentifiable_lesson_without_competitors_says_the_survivor_is_unnamed(
        monkeypatch):
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: ["ambiguous"]))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(2))
    audit = gsg.audit_task(TASK, lessons=2)
    example = audit["lessons"]["unidentifiable_examples"][0]
    assert example["survivors"] is None
    assert example["survivor_source"] == "none declared — reasons only"
    assert example["replay"].startswith("band=")
    assert any("declare LESSON_COMPETITORS" in n for n in audit["notes"])


def test_answer_equivalent_competitor_on_identifiable_lesson_is_reported_only(monkeypatch):
    """A rival matching demos and query is not a query ambiguity."""
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: [],
        LESSON_COMPETITORS={"raw_shape": lambda g: [list(r) for r in g]},
    ))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(2))
    audit = gsg.audit_task(TASK, lessons=2)
    assert audit["errors"] == []
    assert audit["status"] == "PASS"
    assert not audit["lessons"]["survivors_on_identifiable_lessons"]
    assert audit["lessons"]["competitor_survived_all_counts"] == {"raw_shape": 2}


def test_query_changing_competitor_on_identifiable_lesson_warns(monkeypatch):
    """A rival fitting demos but changing the query contradicts the hook."""
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: [],
        LESSON_COMPETITORS={
            "query_wrong": lambda g: [[1]] if g == [[1]] else [[0]],
        },
    ))

    def materialize(*args, **kwargs):
        return ([{
            "index": 0, "band": "easy", "seed": 1, "sample_index": 0,
            "replay": "band=easy seed=1 sample_index=0",
            "demos": [{"input": [[1]], "output": [[1]]}],
            "query": {"input": [[2]], "output": [[2]]},
        }], [])

    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    audit = gsg.audit_task(TASK, lessons=1)
    assert audit["status"] == "WARN"
    assert audit["lessons"]["survivors_on_identifiable_lessons"][0]["survivors"] == ["query_wrong"]


def test_competitor_that_raises_is_counted_and_warns(monkeypatch):
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: [],
        LESSON_COMPETITORS={"explodes": _boom},
    ))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(2))
    audit = gsg.audit_task(TASK, lessons=2)
    assert audit["lessons"]["competitor_errors"] == 2
    assert any("LESSON_COMPETITORS raised" in w for w in audit["warnings"])


def test_evaluate_competitors_separates_the_three_outcomes():
    lesson = {
        "index": 0, "replay": "band=easy seed=1 sample_index=0",
        "demos": [{"input": [[1]], "output": [[2]]}],
        "query": {"input": [[3]], "output": [[6]]},
    }
    scored = gsg.evaluate_competitors({
        "doubles": lambda g: [[g[0][0] * 2]],          # fits demos + query
        "adds_one": lambda g: [[g[0][0] + 1]],         # fits demo, not query
        "wrong": lambda g: [[0]],                      # refuted by the demo
    }, lesson)
    assert scored["survived_all"] == ["doubles"]
    assert scored["query_discriminates"] == ["adds_one"]
    assert scored["refuted"] == ["wrong"]
    assert scored["survived_demos"] == ["adds_one", "doubles"]


# ---------------------------------------------------------------------------
# 3. per-band lesson identifiability
# ---------------------------------------------------------------------------

def test_band_quotas_split_the_lesson_budget():
    assert gsg._band_quotas(12, ("easy", "medium", "hard")) == {
        "easy": 4, "medium": 4, "hard": 4}
    assert gsg._band_quotas(20, ("easy", "medium", "hard")) == {
        "easy": 7, "medium": 7, "hard": 6}
    assert gsg._band_quotas(2, ("easy", "medium", "hard")) == {
        "easy": 1, "medium": 1, "hard": 0}


def test_lessons_report_per_band_counts(monkeypatch):
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda demos, query: (
            [] if query["input"] else ["x"]
        ),
    ))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(6))
    audit = gsg.audit_task(TASK, lessons=6)
    per_band = audit["lessons"]["per_band"]
    assert set(per_band) == {"easy", "medium", "hard"}
    assert sum(r["materialized"] for r in per_band.values()) == 6
    assert audit["lessons"]["requested_per_band"] == {
        "easy": 2, "medium": 2, "hard": 2}
    assert audit["lessons"]["difficulty_passed"] is True


def _fake_runner(monkeypatch, calls):
    """Patch `puzzle_generators.runner.run_one` and record every call."""
    import puzzle_generators.runner as runner

    def _run_one(task_id, seed, sample_index, *, n_train, n_test,
                 bundle=None, bridge=None, fn_name=None, **axes):
        calls.append({"seed": seed, "sample_index": sample_index,
                      "n_train": n_train, "n_test": n_test, "axes": dict(axes)})
        pair = {"input": GRID, "output": GRID}
        return {"train": [pair] * n_train, "test": [pair] * n_test}

    monkeypatch.setattr(runner, "run_one", _run_one)


def test_materialize_lessons_passes_difficulty_and_strides_sample_index(
        monkeypatch):
    """Items 3 + 4 at the source: per band, difficulty through, no si=0 pin."""
    calls: list[dict] = []
    _fake_runner(monkeypatch, calls)
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(lambda g: g))
    lessons, errors = gsg.materialize_lessons(TASK, 6, n_demos=4)
    assert errors == []
    assert len(lessons) == 6
    assert [c["axes"] for c in calls] == [
        {"difficulty": "easy"}, {"difficulty": "easy"},
        {"difficulty": "medium"}, {"difficulty": "medium"},
        {"difficulty": "hard"}, {"difficulty": "hard"},
    ]
    # sample_index is NOT pinned to 0 any more: lesson k of a band starts at
    # k * LESSON_SAMPLE_STRIDE, and consecutive lessons never overlap.
    assert [c["sample_index"] for c in calls] == [0, 11, 0, 11, 0, 11]
    assert all(c["n_train"] == 4 and c["n_test"] == 1 for c in calls)
    # each band gets its own pinned seed series
    assert len({c["seed"] for c in calls}) == 6
    assert [lesson["band"] for lesson in lessons] == [
        "easy", "easy", "medium", "medium", "hard", "hard"]
    assert lessons[0]["replay"] == (
        f"band=easy seed={lessons[0]['seed']} sample_index=0")


def test_materialize_lessons_skips_difficulty_when_generate_cannot_take_it(
        monkeypatch):
    calls: list[dict] = []
    _fake_runner(monkeypatch, calls)
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(lambda g: g))
    lessons, errors = gsg.materialize_lessons(
        TASK, 3, n_demos=2, pass_difficulty=False)
    assert errors == []
    assert all(c["axes"] == {} for c in calls)
    assert all(lesson["difficulty_passed"] is False for lesson in lessons)


def test_generator_without_difficulty_support_is_reported_not_crashed(
        monkeypatch):
    module = _gen_module(lesson_identifiable=lambda d, q: [])
    module.generate = lambda seed, sample_index: GRID   # no difficulty kwarg
    _install(monkeypatch, module)
    materialize = _fake_lessons(3)
    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    audit = gsg.audit_task(TASK, lessons=3)
    assert materialize.seen["pass_difficulty"] is False
    assert audit["status"] == "PASS"          # a NOTE, never a failure
    assert any("does not accept a `difficulty` keyword" in n
               for n in audit["notes"])


def test_materialize_lessons_reports_a_missing_oracle(monkeypatch):
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(
        lambda g: g, ready=False, error="RACKET_MISSING: racket not on PATH"))
    lessons, errors = gsg.materialize_lessons(TASK, 3, n_demos=2)
    assert lessons == []
    assert errors == ["RACKET_MISSING: racket not on PATH"]


# ---------------------------------------------------------------------------
# 4. schedule-residue coverage
# ---------------------------------------------------------------------------

def test_schedule_coverage_counts_residues():
    draws = [("easy", 10 * i, 3 * i) for i in range(40)]
    stats, errors = gsg.schedule_coverage(draws)
    assert errors == []
    assert stats["draws"] == 40
    # seed = 10i -> seed % 2 is always 0: a real alias, and judged (40 >= 8)
    assert stats["residues"]["seed"]["2"]["covered"] == 1
    assert {"expression": "seed", "modulus": 2, "covered": 1,
            "residues": [0]} in stats["aliased"]
    # sample_index = 3i covers every residue mod 4
    assert stats["residues"]["sample_index"]["4"]["covered"] == 4


def test_schedule_coverage_does_not_judge_an_underpowered_modulus():
    draws = [("easy", i, i) for i in range(6)]      # 6 < 4 * 8
    stats, _ = gsg.schedule_coverage(draws)
    assert stats["residues"]["seed"]["8"]["judged"] is False
    assert not any(c["modulus"] == 8 for c in stats["aliased"])


def test_the_pinned_census_does_not_alias(monkeypatch):
    """The claim in `_census_sample_index`, measured rather than asserted."""
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True}))
    audit = gsg.audit_task(TASK, per_band=40)
    schedule = audit["census"]["schedule"]
    assert schedule["aliased"] == []
    for label in ("seed", "sample_index", "seed+sample_index"):
        for modulus in ("2", "3", "4", "5", "6", "7", "8"):
            cell = schedule["residues"][label][modulus]
            if cell["judged"]:
                assert cell["covered"] == cell["of"], (label, modulus, cell)


def test_declared_schedule_profile_coverage_is_reported(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"always": lambda g: True},
        schedule_profile=lambda seed, sample_index, difficulty=None: (
            (seed + sample_index) % 4
        ),
        SCHEDULE_PROFILES=(0, 1, 2, 3),
    ))
    audit = gsg.audit_task(TASK, per_band=40)
    schedule = audit["census"]["schedule"]
    assert set(schedule["profiles"]) == {"0", "1", "2", "3"}
    assert schedule["profiles_missing"] == []
    assert set(schedule["profiles_per_band"]) == {"easy", "medium", "hard"}
    assert audit["status"] == "PASS"


def test_a_profile_the_census_never_visits_warns(monkeypatch):
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"always": lambda g: True},
        schedule_profile=lambda seed, sample_index, difficulty=None: "only",
        SCHEDULE_PROFILES=("only", "never"),
    ))
    audit = gsg.audit_task(TASK, per_band=10)
    assert audit["status"] == "WARN"
    assert audit["census"]["schedule"]["profiles_missing"] == ["never"]
    assert any("never visited by the census" in w for w in audit["warnings"])


def test_schedule_profile_that_raises_fails(monkeypatch):
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True},
        schedule_profile=_boom,
    ))
    audit = gsg.audit_task(TASK, per_band=3)
    assert audit["status"] == "FAIL"
    assert any("schedule_profile raised on 9/9 draws" in e
               for e in audit["errors"])


def test_schedule_profiles_without_a_profile_function_is_an_error(monkeypatch):
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True},
        SCHEDULE_PROFILES=(0, 1),
    ))
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["status"] == "FAIL"
    assert any("SCHEDULE_PROFILES is declared without a schedule_profile" in e
               for e in audit["errors"])


# ---------------------------------------------------------------------------
# 5. EXAMPLES_NEEDED as the default n_demos (v1 behaviour, now reported)
# ---------------------------------------------------------------------------

def test_examples_needed_source_is_recorded(monkeypatch):
    _install(monkeypatch, _gen_module(
        lesson_identifiable=lambda d, q: [], EXAMPLES_NEEDED=5))
    materialize = _fake_lessons(2)
    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    audit = gsg.audit_task(TASK, lessons=2)
    assert materialize.seen["n_demos"] == 5
    assert audit["lessons"]["n_demos"] == 5
    assert audit["lessons"]["n_demos_source"] == "EXAMPLES_NEEDED"

    _install(monkeypatch, _gen_module(lesson_identifiable=lambda d, q: []))
    materialize = _fake_lessons(2)
    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    audit = gsg.audit_task(TASK, lessons=2)
    assert audit["lessons"]["n_demos"] == 3
    assert audit["lessons"]["n_demos_source"] == "default"


# ---------------------------------------------------------------------------
# 6. canonical ambiguity
# ---------------------------------------------------------------------------

def _canonical_file(monkeypatch, tmp_path, pairs, name="puzzles.jsonl"):
    import scripts.canonical_profile_gate as cpg

    path = tmp_path / name
    path.write_text(json.dumps({
        "task_id": TASK,
        "train": [{"input": i, "output": o} for i, o in pairs],
        "test": [],
    }) + "\n")
    monkeypatch.setattr(cpg, "CANONICAL", path)
    return path


def test_canonical_ambiguity_flags_a_simple_shortcut_as_a_NOTE(
        monkeypatch, tmp_path):
    """All canonical pairs answer-equivalent under identity -> NOTE, not WARN."""
    _canonical_file(monkeypatch, tmp_path,
                    [([[1, 2]], [[1, 2]]), ([[3]], [[3]])])
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True}), canonical=None)
    audit = gsg.audit_task(TASK, per_band=2)
    ambiguity = audit["canonical_ambiguity"]
    assert ambiguity["usable_pairs"] == 2
    assert "identity" in ambiguity["ambiguous_simple"]
    assert {"source": "simple", "shortcut": "identity"} in ambiguity["unsatisfied"]
    assert audit["status"] == "PASS"          # NOTE by default
    assert any("canonical CANNOT falsify it" in n for n in audit["notes"])
    assert not any("canonical CANNOT falsify it" in w for w in audit["warnings"])

    promoted = gsg.audit_task(TASK, per_band=2,
                              require_shortcut_counterexample=True)
    assert promoted["status"] == "WARN"
    assert any("canonical CANNOT falsify it" in w for w in promoted["warnings"])


def test_a_declared_canonical_shortcut_warns_on_its_own(monkeypatch, tmp_path):
    """CANONICAL_SHORTCUTS asserts "this is a plausible WRONG rule"."""
    _canonical_file(monkeypatch, tmp_path, [([[1, 0]], [[9, 0]])])
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True},
        CANONICAL_SHORTCUTS={
            "keep_seed_positions": lambda g: [[9 if v else 0 for v in g[0]]],
        },
    ), canonical=None)
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(1))
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["canonical_ambiguity"]["ambiguous_declared"] == [
        "keep_seed_positions"]
    assert audit["status"] == "WARN"
    assert any("keep_seed_positions" in w and "CANNOT falsify" in w
               for w in audit["warnings"])


def test_ambiguity_is_satisfied_by_a_verified_rival_witness(
        monkeypatch, tmp_path):
    """9df4a42fced1's shape: canonical cannot falsify, a GENERATED draw can."""
    _canonical_file(monkeypatch, tmp_path, [([[1, 0]], [[9, 0]])])
    shortcut = lambda g: [[9 if v else 0 for v in g[0]]]   # noqa: E731
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"off_center": lambda g: g[0][0] == 1},
        SEMANTIC_RIVALS={"keep_seed_positions": shortcut},
        WITNESS_RIVALS={"off_center": ["keep_seed_positions"]},
        CANONICAL_SHORTCUTS={"keep_seed_positions": shortcut},
    ), canonical=None)
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(_double))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(1))
    audit = gsg.audit_task(TASK, per_band=30)
    ambiguity = audit["canonical_ambiguity"]
    assert ambiguity["ambiguous_declared"] == ["keep_seed_positions"]
    assert ambiguity["unsatisfied"] == []
    assert ambiguity["satisfied_by_witness"] == {
        "keep_seed_positions": ["off_center"]}
    assert audit["status"] == "PASS"
    assert not any("CANNOT falsify" in w for w in audit["warnings"])


def test_no_canonical_pairs_reports_nothing_rather_than_guessing(
        monkeypatch, tmp_path):
    _canonical_file(monkeypatch, tmp_path, [])
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True}), canonical=None)
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["canonical_ambiguity"]["usable_pairs"] == 0
    assert audit["canonical_ambiguity"]["unsatisfied"] == []
    assert audit["status"] == "PASS"


def test_a_task_whose_outputs_differ_has_no_ambiguity_finding(
        monkeypatch, tmp_path):
    _canonical_file(monkeypatch, tmp_path,
                    [([[1, 2]], [[3, 4]]), ([[5]], [[6]])])
    _install(monkeypatch, _gen_module(
        SEMANTIC_WITNESSES={"always": lambda g: True}), canonical=None)
    audit = gsg.audit_task(TASK, per_band=2)
    assert audit["canonical_ambiguity"]["ambiguous_simple"] == []
    assert audit["notes"] == []
    assert audit["status"] == "PASS"


def test_canonical_pairs_reader_shares_the_input_view():
    """DRY: `canonical_inputs` is the input column of `canonical_pairs`."""
    from scripts.canonical_profile_gate import canonical_inputs, canonical_pairs

    task = "7d09ccad28c8"
    pairs = canonical_pairs(task)
    assert pairs, "expected the real canonical file to carry this task"
    assert [p["input"] for p in pairs] == canonical_inputs(task)


# ---------------------------------------------------------------------------
# JSON schema v2 — additive
# ---------------------------------------------------------------------------

def test_json_out_carries_the_v11_evidence(monkeypatch, tmp_path):
    _install(monkeypatch, _gen_module(
        generate=_cell,
        SEMANTIC_WITNESSES={"marks_one": lambda g: g[0][0] == 1},
        SEMANTIC_RIVALS={"keeps_value": lambda g: [[g[0][0]]]},
        WITNESS_RIVALS={"marks_one": ["keeps_value"]},
    ))
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(_double))
    out = tmp_path / "v11.json"
    gsg.main([TASK, "--per-band", "20", "--json-out", str(out)])
    payload = json.loads(out.read_text())
    assert payload["schema_version"] == 2
    row = payload["audits"][0]
    assert set(row) >= {
        "rival_claims", "weak_witnesses", "canonical_ambiguity",
        "optional_declarations", "require_rival_witness",
        "require_shortcut_counterexample",
    }
    assert row["optional_declarations"]["SEMANTIC_RIVALS"] == ["keeps_value"]
    assert row["optional_declarations"]["WITNESS_RIVALS"] == {
        "marks_one": ["keeps_value"]}
    claim = row["witnesses"]["marks_one"]["rival_claim"]
    assert claim["checked"] == claim["claim_holds"] > 0
    assert set(row["census"]["schedule"]) >= {
        "residues", "aliased", "moduli", "sample_index_rule"}


def test_legacy_lesson_sample_reproduces_the_v1_population(monkeypatch):
    """The escape hatch is EXACTLY v1: si=0, no difficulty, one series."""
    calls: list[dict] = []
    _fake_runner(monkeypatch, calls)
    monkeypatch.setattr(gsg, "_RuleOracle", _fake_oracle(lambda g: g))
    lessons, errors = gsg.materialize_lessons(TASK, 4, n_demos=3, legacy=True)
    assert errors == []
    assert [c["sample_index"] for c in calls] == [0, 0, 0, 0]
    assert [c["axes"] for c in calls] == [{}, {}, {}, {}]
    assert [c["seed"] for c in calls] == [
        gsg._pinned_seed(TASK, "lesson", i) for i in range(4)
    ]
    assert all(lesson["band"] == gsg.LEGACY_BAND for lesson in lessons)


def test_legacy_lesson_sample_is_reported_as_such(monkeypatch):
    _install(monkeypatch, _gen_module(lesson_identifiable=lambda d, q: []))
    monkeypatch.setattr(gsg, "materialize_lessons", _fake_lessons(3))
    audit = gsg.audit_task(TASK, lessons=3, legacy_lesson_sample=True)
    assert audit["lessons"]["legacy_sample"] is True
    assert audit["lessons"]["difficulty_passed"] is False
    assert any("--legacy-lesson-sample is ON" in n for n in audit["notes"])
    assert audit["status"] == "PASS"


def test_lesson_plan_is_deterministic_and_non_overlapping():
    plan = gsg._lesson_plan(TASK, 6, bands=("easy", "medium", "hard"),
                            pass_difficulty=True, legacy=False)
    assert plan == gsg._lesson_plan(TASK, 6, bands=("easy", "medium", "hard"),
                                    pass_difficulty=True, legacy=False)
    assert [(band, si, axes) for band, _seed, si, axes in plan] == [
        ("easy", 0, {"difficulty": "easy"}),
        ("easy", 11, {"difficulty": "easy"}),
        ("medium", 0, {"difficulty": "medium"}),
        ("medium", 11, {"difficulty": "medium"}),
        ("hard", 0, {"difficulty": "hard"}),
        ("hard", 11, {"difficulty": "hard"}),
    ]
    # the stride exceeds any realistic demos+query block, so consecutive
    # lessons of a band never consume the same sample_index
    assert gsg.LESSON_SAMPLE_STRIDE > 1 + 8


# ---------------------------------------------------------------------------
# WFB-2001 — a shortcut that IS the selected rule carries no counterexample
# obligation. `3f4b5ff68c93`'s canonical rule is literally `(rule! (transpose
# g))`, so all 5 canonical pairs are answer-equivalent under the generic
# `transpose` shortcut. Under --require-shortcut-counterexample the gate
# demanded a GENERATED counterexample to transpose — a training row on which
# the task's own authority is wrong. Six canonical rows are bare dihedral
# one-liners, so this is a class, not one task.
# ---------------------------------------------------------------------------

def _canonical_program_stub(monkeypatch, program):
    monkeypatch.setattr(gsg, "_canonical_program_cached", lambda task_id: program)


def test_bare_dihedral_authority_is_recognized(monkeypatch):
    for program, expected in (
        ("(rule! (transpose g))", "transpose"),
        ("(rule!  (lambda (g) (transpose g)))", "transpose"),
        ("(rule! (rotate-cw g))", "rot90"),
        ("(rule! (rotate-ccw g))", "rot270"),
        ("(rule! (rotate-180 g))", "rot180"),
        ("(rule! (flip-lr g))", "flip_lr"),
    ):
        _canonical_program_stub(monkeypatch, program)
        assert gsg.authoritative_simple_shortcut("t") == expected, program


def test_composite_rule_is_not_an_authority_shortcut(monkeypatch):
    """The exclusion must stay narrow — `(overlay g (transpose g))` (5d59b75cb58e)
    is NOT the transpose shortcut and keeps its obligation."""
    for program in (
        "(rule! (overlay g (transpose g)))",
        "(rule! (lambda (g) (let ((x (transpose g))) (overlay g x))))",
        "(rule! (transpose (flip-lr g)))",
    ):
        _canonical_program_stub(monkeypatch, program)
        assert gsg.authoritative_simple_shortcut("t") is None, program


def test_exact_nested_flip_authorities_are_rot180(monkeypatch):
    for program in (
        "(rule! (flip-ud (flip-lr g)))",
        "(rule! (flip-lr (flip-ud g)))",
        "(rule! (lambda (g) (flip-ud (flip-lr g))))",
        "(rule! (lambda (g) (flip-lr (flip-ud g))))",
    ):
        _canonical_program_stub(monkeypatch, program)
        assert gsg.authoritative_simple_shortcut("t") == "rot180", program

    # Merely containing the composition does not make the whole rule rot180.
    _canonical_program_stub(monkeypatch, "(rule! (overlay g (flip-ud (flip-lr g))))")
    assert gsg.authoritative_simple_shortcut("t") is None


def test_authority_equal_shortcut_is_not_an_unsatisfied_obligation(monkeypatch):
    monkeypatch.setattr(
        gsg, "_canonical_pairs_cached",
        lambda task_id: [{"input": [[1, 2], [3, 4]], "output": [[1, 3], [2, 4]]}],
    )
    _canonical_program_stub(monkeypatch, "(rule! (transpose g))")
    stats = gsg.check_canonical_ambiguity(
        "t", declared_shortcuts={}, rival_claims={}, witness_rivals={},
    )
    assert "transpose" in stats["ambiguous_simple"]
    assert stats["authority_equal"] == ["transpose"]
    assert [f["shortcut"] for f in stats["unsatisfied"]] == []


def test_non_authority_shortcut_still_carries_its_obligation(monkeypatch):
    """A rule that is NOT the shortcut must still be asked for a counterexample."""
    monkeypatch.setattr(
        gsg, "_canonical_pairs_cached",
        lambda task_id: [{"input": [[1, 2], [3, 4]], "output": [[1, 3], [2, 4]]}],
    )
    _canonical_program_stub(monkeypatch, "(rule! (some-other-thing g))")
    stats = gsg.check_canonical_ambiguity(
        "t", declared_shortcuts={}, rival_claims={}, witness_rivals={},
    )
    assert stats["authority_equal"] == []
    assert "transpose" in [f["shortcut"] for f in stats["unsatisfied"]]


def test_declared_rival_is_never_excluded_by_authority_equality(monkeypatch):
    """An author asserting 'this is a plausible WRONG rule' outranks the heuristic."""
    monkeypatch.setattr(
        gsg, "_canonical_pairs_cached",
        lambda task_id: [{"input": [[1, 2], [3, 4]], "output": [[1, 3], [2, 4]]}],
    )
    _canonical_program_stub(monkeypatch, "(rule! (transpose g))")
    stats = gsg.check_canonical_ambiguity(
        "t",
        declared_shortcuts={"transpose": lambda g: [list(r) for r in zip(*g)]},
        rival_claims={}, witness_rivals={},
    )
    assert {f["source"] for f in stats["unsatisfied"]} == {"declared"}


# Declared-rival lesson assessment without an author lesson hook.
def _declared_only_double(grid):
    return [[value * 2 for value in row] for row in grid]


def _declared_only_add_one(grid):
    return [[value + 1 if value else 0 for value in row] for row in grid]


def _declared_only_lesson():
    inputs = [
        [[1, 0], [0, 0]], [[0, 1], [0, 0]],
        [[0, 0], [1, 0]], [[0, 0], [0, 1]],
    ]
    query = [[2, 0], [0, 0]]
    return {
        "index": 0, "band": "easy", "seed": 17, "sample_index": 22,
        "replay": "band=easy seed=17 sample_index=22",
        "demos": [{"input": grid, "output": _declared_only_double(grid)} for grid in inputs],
        "query": {"input": query, "output": _declared_only_double(query)},
    }


def _declared_only_fixture(monkeypatch, tmp_path, **attrs):
    lesson = _declared_only_lesson()
    first = lesson["demos"][0]
    _canonical_file(monkeypatch, tmp_path, [(first["input"], first["output"])])
    _install(monkeypatch, _gen_module(EXAMPLES_NEEDED=4, **attrs))
    calls = []

    def materialize(*args, **kwargs):
        calls.append(kwargs)
        return [lesson], []

    monkeypatch.setattr(gsg, "materialize_lessons", materialize)
    return calls


@pytest.mark.parametrize("declaration", ["LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"])
@pytest.mark.parametrize("strict_hook", [False, True])
def test_declared_query_changing_rival_is_scored_without_lesson_hook(
        monkeypatch, tmp_path, declaration, strict_hook):
    attrs = {declaration: {"adds_one": _declared_only_add_one}}
    if strict_hook:
        attrs["strict_canonical_like"] = lambda grid: []
    calls = _declared_only_fixture(monkeypatch, tmp_path, **attrs)
    audit = gsg.audit_task(TASK, per_band=2, lessons=1, require_contract=True)

    assert audit["lessons"] is not None, "declared rivals were never lesson-scored"
    assert audit["status"] == "FAIL"
    assert not audit["hooks_declared"]["lesson_identifiable"]
    stats = audit["lessons"]
    assert stats["assessment_basis"] == "declared_rivals"
    assert stats["hook_declared"] is False
    assert stats["hook_errors"] == 0
    assert stats["unidentifiable"] == 1
    assert stats["per_band"]["easy"]["unidentifiable"] == 1
    example = stats["unidentifiable_examples"][0]
    assert example["survivors"] == ["adds_one"]
    assert example["replay"] == "band=easy seed=17 sample_index=22"
    assert calls[0]["n_demos"] == 4
    assert not any("could not NAME" in note for note in audit["notes"])
    if declaration == "CANONICAL_SHORTCUTS":
        assert stats["auto_scored_canonical_shortcuts"] == ["adds_one"]
        assert audit["canonical_ambiguity"]["ambiguous_declared"] == ["adds_one"]


def test_hookless_answer_equivalent_and_demo_refuted_rivals_are_not_ambiguity(
        monkeypatch, tmp_path):
    _declared_only_fixture(monkeypatch, tmp_path, LESSON_COMPETITORS={
        "doubles": _declared_only_double, "always_zero": lambda grid: [[0]],
    })
    audit = gsg.audit_task(TASK, per_band=2, lessons=1, require_contract=True)
    assert audit["status"] == "PASS"
    stats = audit["lessons"]
    assert stats["identifiable"] == 1
    assert stats["unidentifiable"] == 0
    assert stats["competitor_survived_all_counts"] == {"doubles": 1}
    assert stats["competitor_survivor_counts"] == {"doubles": 1}
    assert stats["survivors_on_identifiable_lessons"] == []
    assert "without detected declared-rival ambiguity" in gsg._summary_line(audit)
    assert any("lesson_identifiable absent" in note for note in audit["notes"])


def test_hookless_competitor_error_is_counted_without_a_hook_error(monkeypatch, tmp_path):
    def broken(grid):
        raise ValueError("fixture rival failure")

    _declared_only_fixture(monkeypatch, tmp_path, LESSON_COMPETITORS={"broken": broken})
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "WARN"
    assert audit["lessons"]["competitor_errors"] == 1
    assert audit["lessons"]["hook_errors"] == 0
    assert any("fixture rival failure" in warning for warning in audit["warnings"])
    assert gsg.main([TASK, "--per-band", "2", "--lessons", "1", "--strict"]) == 1


def test_hookless_materialization_failure_is_not_a_pass(monkeypatch, tmp_path):
    _declared_only_fixture(monkeypatch, tmp_path, LESSON_COMPETITORS={"doubles": _declared_only_double})
    monkeypatch.setattr(gsg, "materialize_lessons", lambda *a, **kw: ([], ["fixture rejection"]))
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "FAIL"
    assert audit["lessons"]["materialized"] == 0
    assert any("ZERO of 1 lessons materialized" in error for error in audit["errors"])
    assert not any("lesson_identifiable declared" in error for error in audit["errors"])


@pytest.mark.parametrize("attrs", [
    {}, {"LESSON_COMPETITORS": {}}, {"CANONICAL_SHORTCUTS": {}},
    {"SEMANTIC_RIVALS": {"doubles": _declared_only_double}},
])
def test_no_lesson_contract_preserves_legacy_advisory(monkeypatch, attrs):
    _install(monkeypatch, _gen_module(**attrs))

    def unexpected_materialization(*args, **kwargs):
        pytest.fail("a module with no lesson contract was materialized")

    monkeypatch.setattr(gsg, "materialize_lessons", unexpected_materialization)
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "NO_CONTRACT"
    assert audit["errors"] == []
    assert audit["lessons"] is None
    required = gsg.audit_task(TASK, per_band=2, lessons=1, require_contract=True)
    assert required["status"] == "FAIL"


@pytest.mark.parametrize("declaration", ["LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"])
def test_malformed_lesson_declaration_remains_a_failure(monkeypatch, declaration):
    _install(monkeypatch, _gen_module(**{declaration: {"not_callable": None}}))
    audit = gsg.audit_task(TASK, per_band=2, lessons=1)
    assert audit["status"] == "FAIL"
    assert audit["lessons"] is None
    assert any(declaration in error for error in audit["errors"])
