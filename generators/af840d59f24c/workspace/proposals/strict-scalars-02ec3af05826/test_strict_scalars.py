from __future__ import annotations

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'repo/generators/af840d59f24c/generator.py'


def _tree() -> ast.Module:
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def test_strict_helper_rejects_coercible_non_int_scalars() -> None:
    tree = _tree()
    helper = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_strict_int_scalar"),
        None,
    )
    assert helper is not None, "the generator must define _strict_int_scalar"
    module = ast.Module(body=[helper], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, object] = {}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    validate = namespace["_strict_int_scalar"]
    assert validate("seed", 0) == 0
    assert validate("sample_index", -7) == -7  # range policy stays with the caller
    for bad in (True, False, 1.0, "1", b"1", None):
        try:
            validate("seed", bad)
        except TypeError:
            pass
        else:
            raise AssertionError(f"accepted non-int scalar: {bad!r}")


def test_every_seed_and_sample_index_entrypoint_invokes_strict_validation() -> None:
    tree = _tree()
    missing: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name == "_strict_int_scalar":
            continue
        params = {arg.arg for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]}
        for param in sorted(params & {"seed", "sample_index"}):
            found = False
            for call in ast.walk(node):
                if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
                    continue
                if call.func.id != "_strict_int_scalar" or len(call.args) < 2:
                    continue
                if isinstance(call.args[1], ast.Name) and call.args[1].id == param:
                    found = True
                    break
            if not found:
                missing.append(f"{node.name}({param})")
    assert not missing, "missing strict validation: " + ", ".join(missing)
