"""The public starter command works for a new test directory without overwriting."""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'shared/tools/write_generator_test.py'
TASK = '1e26763a6f70'


def invoke(destination, task=TASK):
    return subprocess.run(
        [sys.executable, str(HELPER), task, '--out', str(destination)],
        cwd=destination.parents[3], capture_output=True, text=True, timeout=10,
    )


def test_cli_creates_missing_test_directory_and_refuses_overwrite(tmp_path):
    destination = tmp_path / 'generators' / TASK / 'tests' / 'test_generator.py'
    first = invoke(destination)
    assert first.returncode == 0, first.stderr
    original = destination.read_bytes()
    tree = ast.parse(original)
    assert any(isinstance(node, ast.FunctionDef)
               and node.name == 'test_canonical_inputs_are_inside_generator_domain'
               for node in tree.body)
    assert TASK in original.decode()
    destination.write_bytes(original + b'\n# reviewer work must survive\n')
    authored = destination.read_bytes()
    second = invoke(destination)
    assert second.returncode != 0
    assert 'FileExistsError' in second.stderr
    assert destination.read_bytes() == authored


def test_invalid_task_id_creates_neither_parent_nor_file(tmp_path):
    destination = tmp_path / 'generators' / TASK / 'tests' / 'test_generator.py'
    result = invoke(destination, task='invalid-id')
    assert result.returncode != 0 and 'ValueError' in result.stderr
    assert not destination.parent.exists()
