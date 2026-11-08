# Minimal-impostor diagnostic

`probe_minimal_impostors.py` preserves the exact five named tiny mutations from
the shared defect linter: all background, full one color, singleton, solid 2x2,
and short line. It uses each accepted baseline's modal color as background,
resolves modal ties in row-major first-seen order, and uses the numerically
smallest different color as foreground. A uniform baseline has no mutations.

From the extracted packet root, run:

```bash
python3 run_with_racket.py python3 generators/cb439f1b5f4a/workspace/probe_minimal_impostors.py \
  cb439f1b5f4a --seed 0 --samples 6 --out ../checks/minimal-impostors/evidence.json
```

The CLI accepts any selected per-puzzle task ID. Choose a fresh output path;
existing reports are never overwritten. `--samples` is bounded to 1..6.
Generation uses the supplied seed and indices 0 through samples minus one,
cycling easy, medium, and hard. This population need not match the linter's
population; the mutation recipe matches it. `--help` requires only Python.

The report retains baseline generation arguments and pixels, all mutated pixels,
validator results or exceptions, accepted mutation counts, generator and tool
hashes, the inspected linter hash, the catalog rule hash, and selected Racket
outputs and execution hashes through public `Catalog.apply`. At most 30 mutations
are sent to Racket in one bounded batch. Rejected mutations are retained without
reference execution. Exit 0 means the diagnostic completed; exit 2 means it was
incomplete, including rejected generated baselines or reference execution errors.

**These are observations, not a legality certificate or lint waiver.** The
diagnostic does not apply canonical minimal-shape exemptions, recreate a full
lint verdict, suppress a finding, change approval, or make training labels.
An accepted shape with a valid reference output still needs task-semantic
assessment. The exact pixels let reviewers assess evidence hidden by an
aggregate message such as `solid_2x2 6/6`.

The tool imports only public `reviewer_support.find_root` and `arcpuzzles.Catalog`
for checkout discovery and reference execution; it does not import private
`scripts` helpers. The wrapper supplies the runtime and Python import paths.
