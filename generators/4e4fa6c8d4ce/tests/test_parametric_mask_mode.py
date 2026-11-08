from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "4e4fa6c8d4ce"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load(path: Path, name: str):
    assert path.is_file(), f"missing module: {path}"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_parametric_module_declares_canonical_default_and_seed_stable_mode() -> None:
    prototype = _load(PROTOTYPE_PATH, f"parametric_{TASK_ID}")
    assert prototype.PARAMETER_SPEC == {
        "name": "mask_mode",
        "values": ("filled", "empty"),
        "default": "filled",
    }
    first = prototype.choose_mask_mode(20261019)
    assert first in prototype.PARAMETER_SPEC["values"]
    assert prototype.choose_mask_mode(20261019) == first


def test_parametric_python_rules_preserve_roles_and_disagree() -> None:
    prototype = _load(PROTOTYPE_PATH, f"parametric_{TASK_ID}")
    generator = _load(
        ROOT / "generators" / TASK_ID / "generator.py",
        f"parametric_generator_{TASK_ID}",
    )
    grid = generator.generate(20261020, 2, difficulty="medium")
    filled = prototype.apply_python(grid, "filled")
    empty = prototype.apply_python(grid, "empty")
    analysis = generator._analyse(grid)

    assert filled == generator.rule_mirror(grid)
    assert filled != empty
    for row in range(analysis["palette_size"]):
        for col in range(analysis["palette_size"]):
            palette_value = analysis["palette"][row][col]
            if analysis["mask"][row][col]:
                assert (filled[row][col], empty[row][col]) == (palette_value, 0)
            else:
                assert (filled[row][col], empty[row][col]) == (0, palette_value)


def test_episode_uses_one_mode_and_public_challenge_hides_it() -> None:
    prototype = _load(PROTOTYPE_PATH, f"parametric_{TASK_ID}")
    episode = prototype.build_episode(
        seed=20261021,
        mask_mode="empty",
        difficulty="medium",
        start_index=0,
        n_train=3,
        n_test=1,
        labeler=prototype.apply_python,
    )

    assert episode["meta"]["parameters"] == {"mask_mode": "empty"}
    assert episode["meta"]["sample_indices"] == [0, 1, 2, 3]
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert prototype.parameter_rival_findings(episode) == []

    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    challenge_text = repr(challenge)
    assert "mask_mode" not in challenge_text
    assert "empty" not in challenge_text


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_racket_sources_match_python_for_both_modes() -> None:
    prototype = _load(PROTOTYPE_PATH, f"parametric_{TASK_ID}")
    generator = _load(
        ROOT / "generators" / TASK_ID / "generator.py",
        f"parametric_generator_{TASK_ID}",
    )
    assert _normalized_rule_hash(prototype.racket_source("filled")) == generator.RULE_HASH

    grid = generator.generate(20261022, 1, difficulty="hard")
    for mode in prototype.PARAMETER_SPEC["values"]:
        assert prototype.apply_racket(grid, mode) == prototype.apply_python(grid, mode)


def test_evidence_builder_executes_complete_racket_labeled_episodes() -> None:
    prototype = _load(PROTOTYPE_PATH, f"parametric_{TASK_ID}")
    evidence = prototype.build_evidence(
        seed=20261023,
        difficulty="medium",
        start_index=0,
        n_train=3,
        n_test=1,
    )

    assert evidence["checks"]["all_passed"] is True
    assert set(evidence["episodes"]) == {"filled", "empty"}
    assert evidence["checks"]["settings_disagree_on_witness"] is True
    assert evidence["checks"]["filled_rule_hash_matches_selected"] is True
    for mode in prototype.PARAMETER_SPEC["values"]:
        episode = evidence["episodes"][mode]
        assert episode["meta"]["parameters"] == {"mask_mode": mode}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert evidence["checks"]["racket_python_parity"][mode] == [True] * 4
        assert evidence["checks"]["parameter_rival_findings"][mode] == []
        assert evidence["sources"]["rules"][mode]["text"] == prototype.racket_source(mode)


def test_artifact_writer_keeps_public_challenges_parameter_blind(tmp_path: Path) -> None:
    prototype = _load(PROTOTYPE_PATH, f"parametric_{TASK_ID}")
    episodes = {
        mode: prototype.build_episode(
            seed=20261024,
            mask_mode=mode,
            difficulty="easy",
            start_index=0,
            n_train=3,
            n_test=1,
            labeler=prototype.apply_python,
        )
        for mode in prototype.PARAMETER_SPEC["values"]
    }
    evidence = {"schema": "test-evidence", "episodes": episodes}
    out_path = tmp_path / "evidence.json"
    public_dir = tmp_path / "public"

    written = prototype.write_artifacts(
        evidence, out_path=out_path, public_dir=public_dir
    )

    assert json.loads(out_path.read_text())["schema"] == "test-evidence"
    assert set(written["public_challenges"]) == {"episode-a", "episode-b"}
    for record in written["public_challenges"].values():
        path = Path(record["absolute_path"])
        payload = json.loads(path.read_text())
        assert len(payload["train"]) == 3
        assert len(payload["test"]) == 1
        assert "output" not in payload["test"][0]
        text = path.read_text()
        assert "mask_mode" not in text
        assert "filled" not in text
        assert "empty" not in text
        assert "rule" not in text
