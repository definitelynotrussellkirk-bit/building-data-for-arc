"""Focused prototype contracts; canonical production is unchanged."""
from pathlib import Path
import copy
import importlib.util

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/adapter.py"


@pytest.fixture(scope="module")
def adapter():
    spec = importlib.util.spec_from_file_location("symmetry_adapter_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_selected_authority(adapter):
    import json
    programs = {
        r["program_solution"]
        for line in canonical_path(find_root(__file__)).read_text().splitlines()
        if (r := json.loads(line)).get("task_id") == "f283b8535697"
    }
    assert programs == {adapter.program({"output_mode": "patch"})}
    assert adapter.program({"output_mode": "largest_object"}) not in programs


def test_largest_object_isolated_not_raw_bbox(adapter):
    p = [[2, 2, 2, 2, 0], [2, 0, 0, 2, 0], [2, 3, 3, 2, 0],
         [2, 0, 0, 2, 0], [2, 2, 2, 2, 0]]
    assert adapter.core.extract_largest(p) == [
        [2, 2, 2, 2], [2, 0, 0, 2], [2, 0, 0, 2],
        [2, 0, 0, 2], [2, 2, 2, 2]]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matching_inputs_distinct_queries_and_teaching(adapter, demos):
    episodes = [adapter.generate(17, {"output_mode": mode}, demos, 4)
                for mode in adapter.core.MODES]
    assert [[p["input"] for s in ("train", "test") for p in e[s]]
            for e in episodes][0] == [p["input"] for s in ("train", "test")
                                      for p in episodes[1][s]]
    for mode, e in zip(adapter.core.MODES, episodes):
        assert len(e["train"]) == demos and len(e["test"]) == 4
        frozen = [tuple(map(tuple, p["input"]))
                  for s in ("train", "test") for p in e[s]]
        assert len(set(frozen)) == demos + 4
        for name in adapter.core.rival_programs(mode):
            assert any(adapter.core.rival_outputs(p["input"], mode)[name] != p["output"]
                       for p in e["train"]), (mode, name)
        for s in ("train", "test"):
            for p in e[s]:
                assert adapter.core.validate_input(p["input"]) == []
                assert p["output"] == adapter.core.predict(p["input"], mode)
        assert len(e["test"][-1]["input"]) == 30
        assert len(e["test"][-1]["input"][0]) == 30


def test_query_prefix_and_private_metadata_invariance(adapter):
    settings = {"output_mode": "largest_object"}
    one = adapter.generate(3, settings, 3, 1)
    four = adapter.generate(3, settings, 3, 4)
    turn = {"train": four["train"], "test": four["test"][:1]}
    assert public_challenge_bytes(one) == public_challenge_bytes(turn)
    polluted = copy.deepcopy(turn)
    polluted.update(seed=999, settings={"output_mode": "wrong"}, program="secret")
    polluted["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(turn) == public_challenge_bytes(polluted)
    two_demos = adapter.generate(3, settings, 2, 4)
    assert [p["input"] for p in four["test"]] == [p["input"] for p in two_demos["test"]]


def test_two_demos_exclude_modal_color_and_bbox_area_shortcuts(adapter):
    from collections import Counter
    e = adapter.generate(17, {"output_mode": "largest_object"}, 2, 4)

    def rivals(grid):
        p = adapter.core.reconstructed_patch(grid)
        objects = adapter.core.components(p)
        counts = Counter(v for row in p for v in row if v != 0)
        modal = max(counts, key=counts.get)
        selected_color = max((o for o in objects if p[o[0][0]][o[0][1]] == modal), key=len)
        area = lambda o: ((max(r for r, _ in o) - min(r for r, _ in o) + 1)
                          * (max(c for _, c in o) - min(c for _, c in o) + 1))
        return (adapter.core._crop(p, selected_color),
                adapter.core._crop(p, max(objects, key=area)))

    for which in (0, 1):
        assert any(rivals(p["input"])[which] != p["output"] for p in e["train"])


def test_sampler_boundary_content_and_purity(adapter):
    for h, w, family in [(10, 10, "corner"), (10, 30, "band_v"),
                         (30, 10, "band_h"), (30, 30, "corner")]:
        g = adapter.core.sample_input(9, 0, h, w, family)
        assert (len(g), len(g[0])) == (h, w)
        assert adapter.core.validate_input(g) == []
        before = copy.deepcopy(g)
        adapter.core.predict(g, "largest_object")
        assert g == before
        assert sum(v not in (0, 1) for row in g for v in row) >= 10
        # A 5x5 corner marker may occupy a full quadrant of a 10x10 grid.
        # Substantive content across every quadrant is the 30x30 stress check.
        if (h, w) == (30, 30):
            for r0, r1 in [(0, h//2), (h//2, h)]:
                for c0, c1 in [(0, w//2), (w//2, w)]:
                    assert sum(g[r][c] not in (0, 1)
                               for r in range(r0, r1) for c in range(c0, c1)) >= 6
    e = adapter.generate(9, {"output_mode": "patch"}, 2, 1)
    original = copy.deepcopy(e)
    e["train"][0]["input"][0][0] = 9
    assert adapter.generate(9, {"output_mode": "patch"}, 2, 1) == original


@pytest.mark.parametrize("args", [
    (True, {"output_mode": "patch"}, 3, 4),
    (-1, {"output_mode": "patch"}, 3, 4),
    (0, {"output_mode": "patch"}, True, 4),
    (0, {"output_mode": "patch"}, 1, 4),
    (0, {"output_mode": "patch"}, 7, 4),
    (0, {"output_mode": "patch"}, 3, 0),
    (0, {"output_mode": "patch"}, 3, 5),
    (0, {"output_mode": "patch"}, 3, 4.0),
    (0, {"output_mode": True}, 3, 4),
    (0, {"output_mode": "patch", "extra": 0}, 3, 4),
])
def test_request_rejection_is_explicit(adapter, args):
    with pytest.raises(ValueError):
        adapter.generate(*args)


def test_bad_input_and_dimensions_rejected(adapter):
    for dims in [(9, 10), (11, 12), (30, 32), (True, 10)]:
        with pytest.raises(ValueError):
            adapter.core.sample_input(0, 0, *dims, "corner")
    assert adapter.core.validate_input([[True]])
    assert adapter.core.validate_input([[0, 1], [0]])


def test_verifier_rejects_corrupt_label_and_boolean_input(adapter):
    from types import SimpleNamespace
    import json
    from arcpuzzles.parametric_worker import _grid, _real_evaluator
    source = SOURCE.with_name("verify_and_export.py")
    spec = importlib.util.spec_from_file_location("symmetry_verifier_test", source)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    settings = {"output_mode": "patch"}
    episode = adapter.generate(0, settings, 2, 4)
    cases = []
    bad = copy.deepcopy(episode)
    bad["train"][0]["output"][0][0] = (bad["train"][0]["output"][0][0] + 1) % 10
    cases.append((bad, "Python label differs from Racket"))
    bad = copy.deepcopy(episode)
    bad["train"][0]["input"][0][0] = True
    cases.append((bad, "exact integer"))
    programs = {json.dumps({"output_mode": m}): adapter.program({"output_mode": m})
                for m in adapter.core.MODES}
    apply, identity, bridge = _real_evaluator(find_root(__file__) / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        for bad, message in cases:
            forged = SimpleNamespace(core=adapter.core, program=adapter.program,
                                     generate=lambda *args, value=bad: copy.deepcopy(value))
            with pytest.raises(ValueError, match=message):
                verifier._verify_episode(forged, lambda p, g: _grid(apply(p, g)), _grid,
                                         0, settings, 2, 4, programs)
    finally:
        bridge.close()
