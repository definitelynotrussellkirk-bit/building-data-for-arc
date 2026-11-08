"""Execute both native programs on the lawful minimum 4x4 staircase."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    raise FileExistsError(args.out)
repo = Path.cwd()
home = repo / "generators/8e6c44aee812/workspace/parametric"
spec = importlib.util.spec_from_file_location("minimum_boundary_audit", home / "audit_native.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
binding = audit.source_binding()
report = {"schema": "staircase-minimum-boundary-v1", "status": "running",
          "source_sha256": binding,
          "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "scope": "One lawful 4x4 input under each exact native setting; no broader support claim.",
          "cases": [], "training_admitted": False}
with audit._local_imports(audit.RUNTIME, home):
    adapter = audit._load(home / "adapter.py")
    proto = audit._load(home / "prototype.py")
    apply, identity, bridge = audit._real_evaluator(audit.RUNTIME)
    assert identity["backend"] == "racket" and identity["protected"] is True
    report["racket"] = identity
    try:
        diagonal = [4, 5, 4, 6]
        grid = [[diagonal[max(r, c)] for c in range(4)] for r in range(4)]
        assert proto._GEN.self_check(grid) == []
        for scale in (2, 3):
            settings = {"output_scale": scale}
            program = adapter.program(settings)
            output = audit._grid(apply(program, grid))
            assert output == audit.reference(grid, settings)
            assert output == proto.solve(grid, output_scale=scale)
            assert len(output) == 4 * scale and all(len(row) == 4 * scale for row in output)
            report["cases"].append({"settings": settings, "input": grid,
                "program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                "output": output, "mirror_agrees": True})
    finally:
        bridge.close()
assert audit.source_binding() == binding
report.update(status="passed", racket_evaluations=2, source_unchanged=True)
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": report["status"], "racket_evaluations": 2, "out": str(args.out)}))
