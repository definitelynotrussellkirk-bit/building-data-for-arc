from pathlib import Path
import copy
import importlib.util
import json
import shutil
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    body = path.read_bytes()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def repo_root() -> Path:
    for candidate in (HOME, *HOME.parents):
        if (candidate / "shared/data/raw/arc-agi_evaluation_challenges.json").is_file():
            return candidate
    raise FileNotFoundError("public ARC data")


@pytest.fixture(scope="module")
def adapter():
    return load(HOME / "workspace/parametric/adapter.py", "b99_adapter_test")


def official_pairs():
    root = repo_root()
    challenge = json.loads((root / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["b99e7126"]
    solutions = json.loads((root / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())["b99e7126"]
    return challenge["train"] + [dict(input=p["input"], output=o) for p, o in zip(challenge["test"], solutions)]


@pytest.mark.parametrize("index", range(4))
def test_official_pairs_match_canonical(adapter, index):
    pair = official_pairs()[index]
    assert adapter.G.solve(pair["input"], "all_ink") == pair["output"]


def test_default_program_is_exact_reference(adapter):
    assert adapter.program({"scope": "all_ink"}) == (HOME / "reference.rkt").read_text()
    assert (HOME / "reference.rkt").read_bytes() == (HOME / "workspace/parametric/canonical.rkt").read_bytes()


@pytest.mark.parametrize("seed", [0, 1, 2, 17, 43])
def test_matched_inputs_prefixes_and_setting_identification(adapter, seed):
    canonical = adapter.generate(seed, {"scope": "all_ink"}, 6, 4)
    alternate = adapter.generate(seed, {"scope": "largest_component"}, 6, 4)
    assert [p["input"] for s in ("train", "test") for p in canonical[s]] == [p["input"] for s in ("train", "test") for p in alternate[s]]
    assert canonical["train"][:2] != alternate["train"][:2]
    assert len({json.dumps(p["input"]) for s in ("train", "test") for p in canonical[s]}) == 10
    for demos in range(2, 7):
        episode = adapter.generate(seed, {"scope": "all_ink"}, demos, 4)
        assert episode["train"] == canonical["train"][:demos]
        assert episode["test"] == canonical["test"]
    for queries in range(1, 5):
        episode = adapter.generate(seed, {"scope": "all_ink"}, 2, queries)
        assert episode["test"] == canonical["test"][:queries]


def test_minimum_lesson_refutes_declared_rivals(adapter):
    for seed in range(8):
        for scope in adapter.G.SCOPES:
            episode = adapter.generate(seed, {"scope": scope}, 2, 4)
            for rival in adapter.G.RIVALS:
                survives = all(adapter.G.solve(p["input"], scope, rival=rival) == p["output"] for p in episode["train"])
                changes = any(adapter.G.solve(p["input"], scope, rival=rival) != p["output"] for p in episode["test"])
                assert not (survives and changes), (seed, scope, rival)


def test_stress_is_full_periodic_lattice(adapter):
    pair = adapter.generate(17, {"scope": "all_ink"}, 2, 4)["test"][-1]
    g = pair["input"]
    info = adapter.G.analyze(g)
    assert len(g) == len(g[0]) == 29
    assert len(info["row_bands"]) == len(info["col_bands"]) == 7
    assert len(info["mask"]) >= 5
    assert pair["output"] != g


def test_public_views_are_masked_and_first_turn_stable(adapter):
    seen = set()
    for seed in range(8):
        full = adapter.present(seed, {"scope": "largest_component"}, 2, 4, presentation_seed=91)
        first = adapter.present(seed, {"scope": "largest_component"}, 2, 1, presentation_seed=91)
        assert full["public"][0] == first["public"][0]
        seen.add(full["private"]["source_indices"][0])
        for view in full["public"]:
            assert set(view) == {"train", "test"}
            assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
    assert len(seen) > 1


def test_causal_intermediate_changes_output(adapter):
    pair = adapter.generate(17, {"scope": "largest_component"}, 2, 4)["test"][-1]
    info = adapter.G.intermediate(pair["input"], {"scope": "largest_component"})
    assert info["selected_mask"] != info["counterfactual_mask"]
    assert adapter.G.solve(pair["input"], "largest_component") != adapter.G.solve(pair["input"], "largest_component", rival="all_ink")


def test_relocated_adapter_uses_declared_local_resources(adapter, tmp_path):
    contract = json.loads((HOME / "workspace/parametric/promotion.json").read_text())
    root = repo_root()
    for relative in [contract["adapter"], *contract["resources"]]:
        shutil.copyfile(root / relative, tmp_path / Path(relative).name)
    relocated = load(tmp_path / "adapter.py", "b99_adapter_relocated")
    assert relocated.generate(43, {"scope": "largest_component"}, 2, 4) == adapter.generate(43, {"scope": "largest_component"}, 2, 4)


@pytest.mark.parametrize("args", [
    (True, {"scope": "all_ink"}, 2, 4),
    (0, {"scope": "bad"}, 2, 4),
    (0, {}, 2, 4),
    (0, {"scope": "all_ink"}, 1, 4),
    (0, {"scope": "all_ink"}, 7, 4),
    (0, {"scope": "all_ink"}, 2, 0),
    (0, {"scope": "all_ink"}, 2, 5),
])
def test_invalid_requests(adapter, args):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)
