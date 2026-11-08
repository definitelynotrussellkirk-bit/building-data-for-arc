"""Task-local worker: execute supplied rules with the included Racket bridge."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

# This process is launched only inside a public prepare_runtime snapshot.
if not (Path.cwd() / "RUNTIME_MANIFEST.json").is_file():
    raise RuntimeError("Run this worker through prototype.py in a prepared runtime")
sys.path.insert(0, str(Path.cwd()))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def main():
    request = json.load(sys.stdin)
    wrapped = {key: wrap_rule(program) for key, program in request["programs"].items()}
    results = {key: [] for key in wrapped}
    with RacketBridge(timeout=15.0) as bridge:
        binary_sha = hashlib.sha256(Path(bridge.racket_binary).read_bytes()).hexdigest()
        for key, program in wrapped.items():
            for grid in request["inputs"]:
                bridge.define_grid("parametric_input", grid)
                # Reapply the exact callable each time, so no rule binding survives a restart.
                results[key].append(bridge.eval_text(f"({program} parametric_input)"))
    print(json.dumps({"engine": "RacketBridge", "wrapped_programs": wrapped,
                      "outputs": results, "racket_binary_sha256": binary_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
