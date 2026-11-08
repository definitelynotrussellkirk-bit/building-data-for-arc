"""Reproduce the retained 4-seed x 4-setting matrix and validate written bytes."""
from pathlib import Path
import importlib.util
import json
import sys
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root


started = time.monotonic()
root = find_root(__file__)
home = Path(__file__).resolve().parent
source = root / "generators/581bb11ff645/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("hole_rank_matrix", source)
prototype = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prototype
spec.loader.exec_module(prototype)
seeds = (0, 7, 42, 20261023)
with RacketBridge(timeout=10) as bridge:
    episodes = [prototype.generate_episode(seed, **setting, n_demo=3, n_query=4, bridge=bridge)
                for seed in seeds for setting in prototype.SETTINGS]
    prototype.write_batch(episodes, home / "examples")
    result = prototype.verify_batch(home / "examples", bridge=bridge)
result["seeds"] = list(seeds)
result["elapsed_seconds"] = round(time.monotonic() - started, 6)
result["all_seven_incorrect_rivals_eliminated_by_first_demo"] = all(
    len(ep["certificate"]["elimination_demo_indices"]) == 7
    and set(ep["certificate"]["elimination_demo_indices"].values()) == {0}
    for ep in episodes)
assert result["all_seven_incorrect_rivals_eliminated_by_first_demo"]
(home / "replay.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in {"rows", "source_bindings"}}, sort_keys=True))
