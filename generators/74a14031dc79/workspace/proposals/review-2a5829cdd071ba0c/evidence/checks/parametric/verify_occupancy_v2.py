from __future__ import annotations

import importlib.util
import json
from pathlib import Path

TASK_ID = "74a14031dc79"
SOURCE = Path("generators") / TASK_ID / "workspace/parametric/prototype.py"
EVIDENCE = Path("../checks/parametric/occupancy-rule-v2")


def load_prototype():
    spec = importlib.util.spec_from_file_location("occupancy_rule_v2_verifier", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    prototype = load_prototype()
    result = prototype.verify_evidence(EVIDENCE, root=Path.cwd())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
