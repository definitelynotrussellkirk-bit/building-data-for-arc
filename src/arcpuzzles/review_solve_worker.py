"""Run a reviewer program on public inputs; the controller alone holds labels."""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    root = Path(sys.argv[1])
    spec = importlib.util.spec_from_file_location("reviewer_solution", root / "solution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inputs = json.loads((root / "inputs.json").read_text())["inputs"]
    predictions = []
    for grid in inputs:
        output = module.solve(grid)
        if hasattr(output, "tolist"):
            output = output.tolist()
        predictions.append(output)
    (root / "predictions.json").write_text(json.dumps(predictions, allow_nan=False))


if __name__ == "__main__":
    main()
