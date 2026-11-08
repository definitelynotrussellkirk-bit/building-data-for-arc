"""One source-bound height-boundary comparison; no reference-label claim."""
import hashlib
import json
from pathlib import Path
import sys
import time

from reviewer_support import find_root, load_selected_generator


HERE = Path(__file__).resolve().parent
TASK = "2ca60ab198d6"
PIN = "a9bb48897a774b2eff60fdfefefb19a9015391e56bbb906680d9d3db419f2151"
SEED_HEX = "23996496d61f3d9ebe6fab371f391b7097557472c8bf27e890f8b2c17920451b"


def main():
    started = time.monotonic()
    gen, source, digest = load_selected_generator(TASK, root=find_root(__file__))
    assert digest == PIN, (digest, PIN)
    seed = int(SEED_HEX[:16], 16)
    grid = gen.generate(seed, 0, difficulty="medium", grid_h=6)
    errors = gen.self_check(grid, difficulty="medium")
    observed = gen.observe_overrides(grid)
    assert len(grid) == 6 and observed["grid_h"] == 6 and errors == []
    try:
        gen.generate(seed, 0, difficulty="medium", grid_h=5)
    except ValueError as exc:
        rejected = {"exception": type(exc).__name__, "message": str(exc)}
    else:
        raise AssertionError("grid_h=5 was accepted below the advertised minimum 6")
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PIN
    report = {
        "ticket_id": "ticket-9142578cac235702", "type": "api_boundary",
        "status": "completed", "task_id": TASK, "generator_sha256": digest,
        "rule_hash_declared_not_executed": gen.RULE_HASH,
        "seed_derivation": "int(first 16 hex digits of pinned ticket seed, 16)",
        "ticket_seed": SEED_HEX, "seed": seed,
        "valid_call": {"sample_index": 0, "difficulty": "medium", "grid_h": 6,
                       "observed": observed, "self_check": errors, "input": grid},
        "invalid_call": {"sample_index": 0, "difficulty": "medium", "grid_h": 5,
                         **rejected},
        "elapsed_seconds": time.monotonic() - started,
        "argv": sys.argv, "cwd": "repo",
        "limits": ["One height lower-bound comparison at one seed; not an override sweep.",
                   "No Racket execution, output-label audit, or safety approval is claimed."]
    }
    with (HERE / "result.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "valid_height": len(grid), "invalid": rejected}))


if __name__ == "__main__":
    main()
