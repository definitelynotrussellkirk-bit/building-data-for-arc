from pathlib import Path
import importlib.util

import pytest

PATH = Path(__file__).resolve().parents[1] / "workspace/probe_lessons.py"


def _load():
    assert PATH.is_file(), "the reusable lesson probe has not been implemented"
    spec = importlib.util.spec_from_file_location("local_lesson_probe", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_distinguishes_refuted_equivalent_and_query_changing_rivals():
    m = _load()
    demos = [{"input": [[0]], "output": [[0]]}]
    query = {"input": [[1]], "output": [[1]]}
    rivals = {"brand_new_name": lambda g: [[0]], "identity": lambda g: g,
              "refuted": lambda g: [[2]]}
    got = m.classify_lesson(demos, query, rivals)
    assert got == {"refuted": ["refuted"], "answer_equivalent": ["identity"],
                   "query_changing": ["brand_new_name"]}


def test_probe_does_not_mutate_inputs_even_for_inplace_rival():
    m = _load()
    def mutation(g):
        g[0][0] = 0
        return g
    demos, query = [{"input": [[0]], "output": [[0]]}], {"input": [[1]], "output": [[1]]}
    m.classify_lesson(demos, query, {"in_place": mutation})
    assert query["input"] == [[1]]


def test_probe_requires_offline_labels_and_nonempty_demonstrations():
    m = _load()
    with pytest.raises(ValueError):
        m.classify_lesson([], {"input": [[1]], "output": [[1]]}, {})
    with pytest.raises(ValueError):
        m.classify_lesson([{"input": [[1]], "output": [[1]]}], {"input": [[1]]}, {})
