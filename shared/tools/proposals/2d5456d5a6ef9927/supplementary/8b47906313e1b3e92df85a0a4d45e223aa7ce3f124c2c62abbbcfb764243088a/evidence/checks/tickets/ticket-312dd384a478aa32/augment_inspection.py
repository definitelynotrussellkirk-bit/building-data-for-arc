"""Add side-effect-free AST-derived current source contracts to inspection.json."""
from __future__ import annotations
import ast
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"


def assignments(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(), filename=str(path))
    values: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value_node = node.value
        if value_node is None:
            continue
        names = [target.id for target in targets if isinstance(target, ast.Name)]
        if "AXES" in names and isinstance(value_node, ast.Dict):
            axes: dict[str, Any] = {}
            for key_node, axis_node in zip(value_node.keys, value_node.values):
                try:
                    key = ast.literal_eval(key_node)
                except Exception:
                    continue
                try:
                    axis_value = ast.literal_eval(axis_node)
                except Exception:
                    axis_value = {"ast": ast.unparse(axis_node)}
                axes[str(key)] = axis_value
            values["AXES"] = axes
            names = [name for name in names if name != "AXES"]
        try:
            value = ast.literal_eval(value_node)
        except Exception:
            continue
        for name in names:
            values[name] = value
    return values


def main() -> None:
    path = HERE / "inspection.json"
    payload = json.loads(path.read_text())
    for record in payload["sampled_records"]:
        source = REPO / record["source_path"]
        values = assignments(source)
        axes = values.get("AXES") if isinstance(values.get("AXES"), dict) else {}
        record["source_contract"] = {
            "version": values.get("VERSION"),
            "rule_hash_literal": values.get("RULE_HASH"),
            "examples_needed": values.get("EXAMPLES_NEEDED"),
            "axis_names": list(axes),
            "axes": axes,
            "lesson_schedule_period_literal": values.get("LESSON_SCHEDULE_PERIOD"),
        }
        record["catalog_freshness"] = {
            "catalog_version": record["catalog"].get("version"),
            "source_version": values.get("VERSION"),
            "version_matches": record["catalog"].get("version") == values.get("VERSION"),
            "catalog_live_axes": record["catalog"].get("live_axes", []),
            "source_axis_names": list(axes),
            "axes_match": set(record["catalog"].get("live_axes", [])) == set(axes),
        }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({r["task_id"]: r["catalog_freshness"] for r in payload["sampled_records"]}, indent=2))


if __name__ == "__main__":
    main()
