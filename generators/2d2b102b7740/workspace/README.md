# Minimal-grammar diagnostic

`probe_minimal_grammar.py` is a reusable authoring CLI for catalog tasks with a
per-puzzle generator and a canonical Racket rule. It
accepts one supplied grid, constructs the same five small geometry probes used
by shared defect lint, and records `self_check` decisions alongside actual
canonical Racket outputs. It records source, input, output, and tool hashes.
It loads the exact hashed Python source bytes, avoiding stale timestamp-based
bytecode. It preserves execution errors/timeouts and refuses to overwrite an
existing report.

From a review packet's outer root, with a new output filename:

```sh
python3 review.py run python3 generators/2d2b102b7740/workspace/probe_minimal_grammar.py \
  --task 2d2b102b7740 --input ../checks/minimal-grammar-probe-input.json \
  --out ../checks/minimal-grammar-recheck.json
```

Use `--help` for difficulty and reference-worker timeout options. In a regular
repository checkout, run the script with that repository's supported Racket
environment. Nine focused tests in `../tests/test_minimal_grammar_probe.py`
exercise fixture fidelity, independent working directories, actual Racket,
failure receipts, timeout handling, and stale-bytecode avoidance.

The report intentionally leaves semantic validity for review. Successful
execution alone cannot establish a task's grammar: a 2×2 blue block executes
under this Racket rule but is rejected correctly as noncollinear. A horizontal
four-blue line, however, satisfies the grammar and extends correctly. The tool
never exempts a lint check, modifies catalog approval, or changes training
admission. `../generator.py` remains the selected generator implementation.
