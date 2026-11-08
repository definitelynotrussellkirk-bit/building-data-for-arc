from __future__ import annotations

import sys

import pytest

from scripts.generator_module_loader import load_module_from_path


def test_loader_registers_module_before_dataclass_execution(tmp_path):
    path = tmp_path / "dataclass_generator.py"
    path.write_text(
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class Example:\n"
        "    value: int\n"
    )

    module = load_module_from_path("test_dataclass_generator", path)

    assert module.Example(7).value == 7
    assert sys.modules["test_dataclass_generator"] is module


def test_loader_removes_failed_new_module(tmp_path):
    path = tmp_path / "broken_generator.py"
    path.write_text("raise RuntimeError('broken')\n")

    with pytest.raises(RuntimeError, match="broken"):
        load_module_from_path("test_broken_generator", path)

    assert "test_broken_generator" not in sys.modules
