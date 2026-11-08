# Workspace

The selected implementation is `../generator.py`.

## Source-bound lesson probe

`lesson_probe.py` builds a portable runtime from the current selected source,
uses the selected canonical Racket authority for outputs, and dynamically reads
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES` from that
runtime. It checks canonical-shortcut fit, lesson-level rival survival, cyclic
sample-index starts, exact-input uniqueness, strict-domain acceptance, witness
frequency, and an independent Python/Racket authority mirror.

From the packet root:

```bash
python3 repo/generators/ebff81ea3252/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out repo/generators/ebff81ea3252/workspace/lesson_probe_report.json \
  --timeout 1800
```

The script self-bootstraps through `run_with_racket.py` when `RACKET_PATH` is not
already set and resolves a relative `--out` path against the caller's working
directory. The retained report was generated from source SHA-256
`660d584a…0dbb34f` and contains 300/300 identifiable lessons with zero authority
mismatches. It is finite evidence about declared rivals, not universal proof.

`lesson_probe_smoke.json` is a one-lesson-per-band path/bootstrap smoke artifact;
`lesson_probe_report.json` is the required 100-lessons-per-band census.
