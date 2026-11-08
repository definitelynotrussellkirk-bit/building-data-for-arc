"""Independent canonical rival classification and query-isolation regressions."""
from copy import deepcopy
import importlib.util

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "fa3550d200a0"
ROOT = find_root(__file__)
PROBE_PATH = ROOT / "generators" / TASK / "workspace" / "probe_canonical.py"
SPEC = importlib.util.spec_from_file_location("fa3550d200a0_canonical_probe", PROBE_PATH)
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def unique_canonical_pairs():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    return list({PROBE.grid_hash(p["input"]): p for p in pairs}.values())


def test_independent_canonical_connectivity_classification():
    pairs = unique_canonical_pairs()
    assert len(pairs) == 4
    assert all(PROBE.stamp(p["input"]) == p["output"] for p in pairs)
    assert all(PROBE.window_rival(p["input"]) == p["output"] for p in pairs)
    # This rival is refuted by supplied data, so it cannot be advertised as
    # canonical-fitting even if a restricted generator made it appear correct.
    assert sum(PROBE.stamp(p["input"], False) == p["output"] for p in pairs) == 1


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    gen, _source, _digest = load_selected_generator(TASK, root=ROOT)
    pairs = unique_canonical_pairs()
    declarations = gen.CANONICAL_SHORTCUTS
    assert declarations, "A measured canonical-fitting shortcut should be retained"
    for name, rival in declarations.items():
        assert all(rival(deepcopy(p["input"])) == p["output"] for p in pairs), name
    rivals, inventory = PROBE.rival_inventory(gen)
    assert all(row["origin"] == "selected_generator" for row in inventory.values())
    assert set(rivals) == set(inventory)
    assert all(not name.startswith("audit_") for name in rivals)


def test_query_answers_never_refute_rivals_for_other_queries():
    episode = {"train": [{"input": [[0]], "output": [[0]]}],
               "test": [{"input": [[1]], "output": [[2]]},
                        {"input": [[3]], "output": [[3]]},
                        {"input": [[4]], "output": [[5]]},
                        {"input": [[6]], "output": [[6]]}]}
    rivals, errors = PROBE.lesson_rival_assessment(episode, {"identity": deepcopy})
    assert errors == []
    row = rivals["identity"]
    assert row["fits_all_demonstrations"] is True
    assert row["demonstration_refuting_indices"] == []
    assert [q["status"] for q in row["queries"]] == [
        "ambiguous", "survived_on_query", "ambiguous", "survived_on_query"]
