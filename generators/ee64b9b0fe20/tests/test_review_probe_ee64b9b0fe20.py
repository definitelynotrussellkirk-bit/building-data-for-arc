"""Pure tests for the retained census/lesson evidence helper."""
import importlib.util
from pathlib import Path


def load_probe():
    path = Path(__file__).resolve().parents[1] / "workspace/review_probe.py"
    assert path.is_file(), "review_probe.py must be supplied as a reusable artifact"
    spec = importlib.util.spec_from_file_location("review_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_grid_digest_does_not_depend_on_dictionary_key_order():
    probe = load_probe()
    assert probe.digest_json({"b": 2, "a": 1}) == probe.digest_json({"a": 1, "b": 2})
    assert probe.digest_json([[1, 2]]) != probe.digest_json([[2, 1]])


def test_lesson_analysis_requires_a_surviving_rival_to_change_the_query():
    probe = load_probe()
    rivals = {"identity": lambda grid: grid, "always_zero": lambda grid: [[0]]}
    demos = [{"input": [[0]], "output": [[0]]}]
    query = {"input": [[2]], "output": [[2]]}
    assert probe.ambiguous_rivals(rivals, demos, query) == ["always_zero"]
    assert probe.ambiguous_rivals(rivals, demos + [{"input": [[1]], "output": [[1]]}], query) == []


def test_reference_wrapper_uses_a_real_portable_execution_layout(tmp_path, monkeypatch):
    import sys
    probe = load_probe()
    assert callable(getattr(probe, "prepare_review_runtime", None)), "probe must prepare the mapped execution layout"
    repo = Path(__file__).resolve().parents[3]
    runtime = tmp_path / "moved-runtime"
    receipt = probe.prepare_review_runtime(repo, runtime, [probe.TASK_ID])
    assert receipt["task_ids"] == [probe.TASK_ID]
    assert (runtime / "scripts/comment_solutions.py").is_file()
    generator = runtime / "puzzle_generators/per_puzzle" / probe.TASK_ID / "generator.py"
    assert generator.is_file() and not generator.is_symlink()
    monkeypatch.syspath_prepend(str(runtime))
    # Force an isolated import: another focused test may already load the shared
    # package from the authoring layout, so test the relocated entry in a child.
    import subprocess
    result = subprocess.run([sys.executable, "-c",
        "from puzzle_generators.rule_wrap import wrap_rule; assert 'lambda' in wrap_rule('(rule! (gravity g \\\"down\\\"))')"],
        cwd=runtime, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
