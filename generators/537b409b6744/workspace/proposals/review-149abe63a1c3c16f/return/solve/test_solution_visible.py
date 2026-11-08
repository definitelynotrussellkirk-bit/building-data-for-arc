import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("post_repair_solution", HERE / "solution.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_all_visible_training_examples():
    challenge = json.loads((HERE / "challenge.json").read_text())
    for index, pair in enumerate(challenge["train"]):
        assert module.solve(pair["input"]) == pair["output"], index
