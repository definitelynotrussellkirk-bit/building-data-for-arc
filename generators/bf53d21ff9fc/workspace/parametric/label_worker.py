"""Execute materialized landing-offset programs in the bundled Racket runtime."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = {"programs": {}, "evaluation_count": 0}
    with RacketBridge(timeout=10.0) as bridge:
        result["runtime_identity"] = bridge.runtime_identity
        for setting, source in request["programs"].items():
            callable_text = wrap_rule(source)
            definition = f"(define __prototype_rule {callable_text})"
            bridge.eval_text(definition)
            outputs = {}
            for name, grid in request["inputs"].items():
                bridge.define_grid("__prototype_input", grid)
                label = bridge.eval_text("(__prototype_rule __prototype_input)")
                if (
                    not isinstance(label, list)
                    or not 1 <= len(label) <= 30
                    or not isinstance(label[0], list)
                    or not 1 <= len(label[0]) <= 30
                    or any(not isinstance(row, list) or len(row) != len(label[0]) for row in label)
                    or any(type(cell) is not int or not 0 <= cell <= 9 for row in label for cell in row)
                ):
                    raise ValueError(f"Racket emitted an invalid ARC grid for {setting}/{name}")
                outputs[name] = label
                result["evaluation_count"] += 1
            result["programs"][setting] = {
                "program_sha256": sha256(source),
                "callable": callable_text,
                "callable_sha256": sha256(callable_text),
                "definition": definition,
                "definition_sha256": sha256(definition),
                "application": "(__prototype_rule __prototype_input)",
                "outputs": outputs,
            }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
