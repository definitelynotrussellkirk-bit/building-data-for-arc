"""Bounded native-contract and boundary execution evidence for this prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import artifact
from arcpuzzles.parametric_worker import _real_evaluator, evaluate_contract
from reviewer_support import canonical_pairs


def run(out):
    adapter = artifact.adapter
    root = artifact.ROOT
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    contract = json.loads(Path(__file__).with_name("promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"stop_short": stop}, "demos": demos, "queries": 4}
            for seed in (17, 53) for demos in range(2, 7) for stop in (0, 1, 2)]
    native = evaluate_contract(root, adapter.TASK_ID, contract, jobs)
    apply, runtime, bridge = _real_evaluator(root / "shared/runtime")
    boundary, canonical_count, extra_evaluations = [], 0, 0
    try:
        for pair in canonical_pairs(adapter.TASK_ID, root=root, labeled_only=True):
            assert apply(adapter.program({"stop_short": 0}), pair["input"]) == pair["output"]
            canonical_count += 1
            extra_evaluations += 1
        for h, w in ((9, 9), (9, 30), (30, 9), (30, 30)):
            for seed in (5, 47):
                for orientation in (0, 1):
                    grid, sampling = adapter.sample_input(seed, orientation, h, w)
                    labels = []
                    for stop in adapter.SETTINGS:
                        label = apply(adapter.program({"stop_short": stop}), grid)
                        assert label == adapter.transform(grid, stop)
                        labels.append(label)
                        extra_evaluations += 1
                    blocks = adapter._blocks(grid)
                    cells = adapter._scattered(grid, blocks)
                    spans = [len(adapter._path(p, blocks[col], h, w)) - 1 for col, p in cells]
                    boundary.append({"seed": seed, "index": orientation, **sampling,
                        "input_sha256": hashlib.sha256(artifact._bytes(grid)).hexdigest(),
                        "label_sha256": [hashlib.sha256(artifact._bytes(g)).hexdigest() for g in labels],
                        "scatter_count": len(cells), "longest_path": max(spans),
                        "central_scatters": sum(h // 3 <= p[0] < 2 * h // 3 and w // 3 <= p[1] < 2 * w // 3 for _, p in cells),
                        "passed": True})
                    if (h, w, seed, orientation) == (30, 30, 5, 1):
                        large_witness = {"input": grid, "outputs": {str(s): g for s, g in zip(adapter.SETTINGS, labels)}}
        # Literal short rays exercise saturation at the source, including stop=2.
        grid = [[6] * 9 for _ in range(9)]
        for r in range(3):
            for c in range(3):
                grid[r][c] = 2
                grid[r + 6][c + 6] = 4
        grid[1][4], grid[4][7] = 2, 4
        for stop in adapter.SETTINGS:
            assert apply(adapter.program({"stop_short": stop}), grid) == adapter.transform(grid, stop)
            extra_evaluations += 1
    finally:
        bridge.close()
    source_paths = [Path(__file__), Path(__file__).with_name("adapter.py"), Path(__file__).with_name("artifact.py"),
                    Path(__file__).with_name("canonical.rkt"), Path(__file__).with_name("promotion.json"),
                    root / "generators" / adapter.TASK_ID / "generator.py"]
    result = {"schema": "arcpuzzles-stop-short-probe-v1", "status": "passed", "proposed": True,
              "source_sha256": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
              "native_contract_jobs": len(jobs), "native_contract_checks": native["checks"],
              "native_racket_evaluations": native["racket_evaluations"], "racket": runtime,
              "boundary_cases": boundary, "canonical_labels": canonical_count,
              "extra_racket_evaluations": extra_evaluations,
              "training_admitted": False,
              "limits": "Two episode seeds for all 2..6 demo counts and three settings; 16 boundary scenes. No owner qualification/acceptance and no exhaustive induction claim."}
    out.mkdir(parents=True)
    (out / "result.json").write_bytes(artifact._bytes(result))
    (out / "large-witness.json").write_bytes(artifact._bytes(large_witness))
    print(json.dumps({"status": result["status"], "native_contract_jobs": len(jobs),
          "racket_evaluations": native["racket_evaluations"] + extra_evaluations,
          "boundary_cases": len(boundary), "canonical_labels": canonical_count,
          "max_boundary_attempts": max(row["attempts"] for row in boundary)}, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.out)


if __name__ == "__main__":
    main()
