# Qualification workspace

The selected implementation is `../generator.py`.  These helpers are retained
for future reviewers and are not selected as runtime generator code.

## `reference_probe.py`

An independent Python translation of the canonical dictionary/gallery rule. It
parses prototypes, computes authority-shaped outputs, implements the
`deduplicate_query` rival, and reports profile/witness facts.  It intentionally
does not call `generator.rule_mirror`, so it can catch a mirror and generator
being wrong in the same way.

## `qualify.py`

Run from the extracted packet root:

```sh
python3 review.py run python3 generators/35368341e72e/workspace/qualify.py \
  --out ../checks/qualification.json
```

The command checks all canonical training pairs, 192 generated draws, repeated-
query counterexamples, uniqueness, and the pinned per-band canonical profile.
It writes a compact JSON report and exits nonzero on any mismatch.

For a final label disagreement, use the selected Racket authority rather than
only this translation.  The retained example is:

```sh
python3 review.py run python3 -m arcpuzzles apply 35368341e72e \
  --input ../checks/counterexample-35368341e72e/input.json \
  --out ../checks/counterexample-35368341e72e/racket.json
```

Do not consult either helper during a visible-only solve; they expose the rule.
