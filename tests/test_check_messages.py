"""Battery and lint messages name the actual phase, the caller's evidence path and the exact pin."""
import shutil

import pytest

from arcpuzzles import Catalog, runtime

TARGET = "e42dbdaedbe0"  # unpinned and failing several stages in this library


def _unpinned():
    row = Catalog().describe(TARGET)
    source = (Catalog().root / row["generator"]).read_text()
    if "\nRULE_HASH" in source:
        pytest.skip(f"{TARGET} is pinned now; choose another unpinned generator")
    return row


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_lint_prints_the_exact_rule_hash_to_pin(tmp_path):
    row = _unpinned()
    result = runtime.check(Catalog(), TARGET, stage="lint", output=tmp_path / "lint", timeout=300)
    console = result["stdout"] + result["stderr"]
    log = (tmp_path / f"lint/checks/{TARGET}_before_lint.log").read_text()
    for text in (console, log):  # the failing line and the fix are both visible without opening the log
        assert "missing required module constant: RULE_HASH" in text
        assert f'pin RULE_HASH = "{row["rule_hash"]}"' in text


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_after_phase_failure_is_labeled_after_and_paths_point_to_output(tmp_path):
    _unpinned()
    out = tmp_path / "after"
    result = runtime.check(Catalog(), TARGET, full_battery=True, phase="after", output=out, timeout=900)
    assert not result["passed"]
    assert "AFTER CHECK FAILED" in result["stdout"]
    assert "BASELINE COMPLETE" not in result["stdout"]
    assert f"RUN   lint -> {out.resolve()}/checks/{TARGET}_after_lint.log" in result["stdout"]
    assert (out / f"checks/{TARGET}_after_lint.log").is_file()
