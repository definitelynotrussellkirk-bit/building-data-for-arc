# Workspace

`reference_probe.py` is a source-bound independent verifier for the selected generator. From the repository root:

```sh
python3 generators/fcd1f7b55d3b/workspace/reference_probe.py
```

It verifies the five canonical pairs against an independent exactly-two/bounding-box oracle, enumerates the compact 72-case exact-control boundary matrix, samples every difficulty band, and checks all query rotations of deterministic five-pair lesson windows against the generator's declared competitors. It records the generator hash in its JSON output and exits nonzero on any finding.

The probe is bounded to the declared competitors and selected generator manifold; it is not a proof of unique induction against arbitrary rules. The selected implementation remains `../generator.py`.
