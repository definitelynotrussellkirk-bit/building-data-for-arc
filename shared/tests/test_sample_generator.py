from pathlib import Path

import pytest

from scripts.sample_generator import read_task_id


def test_read_task_id_resolves_constant_alias(tmp_path: Path) -> None:
    source = tmp_path / "generator.py"
    source.write_text(
        'GENERATOR_ID = "0c2b397c7f01"\n'
        "TASK_ID = GENERATOR_ID\n",
        encoding="utf-8",
    )

    assert read_task_id(source) == "0c2b397c7f01"


def test_read_task_id_rejects_unresolved_alias(tmp_path: Path) -> None:
    source = tmp_path / "generator.py"
    source.write_text("TASK_ID = UNKNOWN_ID\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unresolved task-id constant"):
        read_task_id(source)


def test_read_task_id_falls_back_when_constant_is_absent(tmp_path: Path) -> None:
    directory = tmp_path / "fallback-task"
    directory.mkdir()
    source = directory / "generator.py"
    source.write_text("VERSION = '1.0.0'\n", encoding="utf-8")

    assert read_task_id(source) == "fallback-task"
