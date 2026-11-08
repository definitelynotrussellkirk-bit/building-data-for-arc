# Workspace tools for 486794347a11

The selected implementation is `../generator.py`. Files here are review aids and
are not copied into a normal generated runtime.

## `marker_shortcut_probe.py`

This deterministic census samples generated inputs, deliberately omits the
explicit marker count, and asks whether top-row geometry still predicts the
scale factor. It reports:

- single geometry features that map exactly to the label;
- accuracies and confusion matrices for named plausible rival rules;
- optional depth-1 through depth-4 decision trees on held-out seeds when
  scikit-learn is installed; and
- the first eight schedule phases for inspection.

Run it against any prepared runtime by placing that runtime on `PYTHONPATH`:

```bash
PYTHONPATH=/path/to/runtime \
python3 marker_shortcut_probe.py \
  --seeds 100 --samples 64 --out marker-shortcut-census.json
```

The default 32 seeds × 32 sample indices × 4 difficulty bands is the cheap gate.
The review used 100 × 64 × 4 = 25,600 generated inputs for both before and after
measurements.

Interpret exact single-feature mappings and named rivals first. A multivariate
model can lawfully reconstruct the intended count from several marker-position
features—for example, two markers have one inter-marker gap while three markers
have two. A high tree score is therefore a discovery lead, not automatically a
defect. Promote a learned proxy to a failing gate only when it expresses a
meaningfully different rule and a legal or canonical counterexample makes that
rule disagree with count-and-scale.
