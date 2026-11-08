"""Task-local tests for the proposed conflict-policy family; labels use Racket."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
PATH = HOME / "workspace/parametric/prototype.py"


def load():
    assert PATH.is_file(), "conflict-policy prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("conflict_policy_prototype", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_three_policies_have_fixed_rules_and_four_distinct_queries():
    p = load()
    episodes = []
    with p.RacketLabeler() as oracle:
        for policy in p.POLICIES:
            episode = p.generate_episode(31, policy=policy, input_seed=47, labeler=oracle)
            p.verify_episode(episode, labeler=oracle)
            assert episode["params"] == {"conflict_policy": policy}
            challenge = episode["challenge"]
            assert len(challenge["train"]) == 2 and len(challenge["test"]) == 4
            assert episode["certificate"]["survivors"] == ["policy:" + policy]
            grids = [x["input"] for x in challenge["train"] + challenge["test"]]
            assert len({p.grid_key(g) for g in grids}) == 6
            assert all(not p.GEN.self_check(g) for g in grids)
            episodes.append(episode)
    assert all([x["input"] for x in e["challenge"]["train"] + e["challenge"]["test"]] ==
               [x["input"] for x in episodes[0]["challenge"]["train"] + episodes[0]["challenge"]["test"]]
               for e in episodes)
    assert len({p.grid_key(e["challenge"]["test"][0]["output"]) for e in episodes}) == 3


@pytest.mark.parametrize("kwargs", [
    {"n_demos": 0}, {"n_demos": 1}, {"n_demos": True}, {"n_demos": 2.0},
    {"n_demos": 9}, {"n_queries": 0}, {"n_queries": 17}, {"n_queries": False},
    {"n_queries": 4.0}, {"policy": "yellow"}, {"seed": True}, {"input_seed": 1.5},
])
def test_invalid_requests_fail_before_reference_execution(kwargs):
    p = load()
    options = {"seed": 13}
    options.update(kwargs)
    with pytest.raises(ValueError):
        p.generate_episode(**options)


def test_sampler_maximum_counts_and_exact_retry_failure():
    p = load()
    demos, queries = p.sample_inputs(91, n_demos=8, n_queries=16)
    assert (len(demos), len(queries)) == (8, 16)
    assert len({p.grid_key(g) for g in demos + queries}) == 24
    with pytest.raises(ValueError, match="attempt"):
        p.sample_inputs(91, n_demos=2, n_queries=4, max_attempts=5)


def test_certificate_uses_demonstrations_and_query_inputs():
    p = load()
    grid = p.GEN.generate(17, 0, n_shared_conflict=0)
    demo = {"input": grid, "output": p.mirror(grid, "left")}
    conflicting = p.GEN.generate(18, 0, n_shared_conflict=1)
    bad = p.lesson_certificate([demo, deepcopy(demo)], [conflicting], "left")
    assert not bad["identifiable"] and bad["per_query"][0]["ambiguous_rivals"]
    equivalent = p.lesson_certificate([demo, deepcopy(demo)], [grid], "left")
    assert equivalent["identifiable"]
    assert len(equivalent["survivors"]) > 1


def test_visible_ids_ignore_private_settings_and_query_answers():
    p = load()
    with p.RacketLabeler() as oracle:
        e = p.generate_episode(7, labeler=oracle)
    original = p.public_challenge_bytes(e["challenge"])
    modified = deepcopy(e)
    modified["seed"] = 999
    modified["params"] = {"conflict_policy": "right"}
    modified["program"] = "private metadata changed"
    modified["challenge"]["test"][0]["output"] = [[9]]
    assert p.public_challenge_bytes(modified["challenge"]) == original
    assert p.public_challenge_id(modified["challenge"]) == p.public_challenge_id(e["challenge"])


def test_verifier_rejects_forged_label_certificate_program_and_duplicates():
    p = load()
    with p.RacketLabeler() as oracle:
        e = p.generate_episode(8, labeler=oracle)
        mutants = []
        m = deepcopy(e)
        m["challenge"]["test"][0]["output"][0][0] = (m["challenge"]["test"][0]["output"][0][0] + 1) % 10
        mutants.append(m)
        m = deepcopy(e)
        m["certificate"]["identifiable"] = False
        mutants.append(m)
        m = deepcopy(e)
        m["program"] = p.materialize_program("right")
        mutants.append(m)
        m = deepcopy(e)
        m["challenge"]["test"][1] = deepcopy(m["challenge"]["test"][0])
        mutants.append(m)
        m = deepcopy(e)
        m["challenge"]["test"][0]["input"][0][0] = False
        mutants.append(m)
        for mutant in mutants:
            with pytest.raises(ValueError):
                p.verify_episode(mutant, labeler=oracle)


def test_export_is_sorted_visible_only_and_rejects_duplicate_payloads(tmp_path):
    p = load()
    with p.RacketLabeler() as oracle:
        episodes = [p.generate_episode(19, policy=x, input_seed=23, labeler=oracle) for x in p.POLICIES]
        report = p.write_batch(list(reversed(episodes)), tmp_path / "good", labeler=oracle)
        identifiers = [row["public_id"] for row in report["episodes"]]
        assert identifiers == sorted(identifiers)
        for e in episodes:
            public_id = p.public_challenge_id(e["challenge"])
            raw = (tmp_path / "good/public" / (public_id + ".json")).read_bytes()
            assert raw == p.public_challenge_bytes(e["challenge"])
            import hashlib, json
            assert hashlib.sha256(raw).hexdigest() == public_id
            visible = json.loads(raw)
            assert set(visible) == {"train", "test"}
            assert all(set(x) == {"input"} for x in visible["test"])
        with pytest.raises(ValueError, match="duplicate"):
            p.write_batch([episodes[0], deepcopy(episodes[0])], tmp_path / "duplicate", labeler=oracle)
        assert not (tmp_path / "duplicate").exists()


def test_canonical_default_is_exact_registered_program_and_racket_labels():
    p = load()
    from reviewer_support import canonical_pairs, find_root
    import json
    root = find_root(__file__)
    records = [json.loads(s) for s in (root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    canonical = next(x for x in records if x.get("task_id") == p.TASK_ID)
    assert p.materialize_program("left") == canonical["program_solution"]
    with p.RacketLabeler() as oracle:
        for pair in canonical_pairs(p.TASK_ID, root=root):
            assert oracle.apply(pair["input"], "left") == pair["output"]


def test_verifier_rejects_forged_schema_lineage_and_runtime():
    p = load()
    accepted = []
    with p.RacketLabeler() as oracle:
        e = p.generate_episode(41, labeler=oracle)
        mutations = {
            "schema": "unrelated-schema",
            "parent": {"source_split": "evaluation", "source_task_id": "forged"},
            "runtime": {"protected": False, "binary_sha256": "0" * 64},
        }
        relocated = deepcopy(e)
        for key in ("binary_path", "prelude_path", "bridge_path"):
            relocated["runtime"][key] = "/relocated/" + key
        assert p.verify_episode(relocated, labeler=oracle)
        altered_hash = deepcopy(e)
        altered_hash["runtime"]["binary_sha256"] = "0" * 64
        with pytest.raises(ValueError, match="runtime identity"):
            p.verify_episode(altered_hash, labeler=oracle)
        for field, value in mutations.items():
            mutant = deepcopy(e)
            mutant[field] = value
            try:
                p.verify_episode(mutant, labeler=oracle)
            except ValueError:
                continue
            accepted.append(field)
    assert accepted == [], f"accepted forged provenance fields: {accepted}"
