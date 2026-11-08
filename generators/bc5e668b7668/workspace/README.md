# bc5e668b7668 workspace

## `lesson_rival_probe.py`

A reusable, source-bound lesson-level probe for this generator. It reads
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES` from the
selected module instead of maintaining a second rival list. Labels are obtained
only through the supported `arcpuzzles apply` command, and each batch must report
the exact selected generator SHA-256 and declared Racket rule hash.

Run from the extracted packet root:

```bash
python3 run_with_racket.py \
  python3 generators/bc5e668b7668/workspace/lesson_rival_probe.py \
  --lessons-per-band 100 \
  --demos-per-lesson 4 \
  --bands easy medium hard \
  --batch-size 64 \
  --out-dir ../checks/lesson-probe-final
```

The default five-example lesson is four demonstrations plus one query.
Nonoverlapping windows advance by five against the four-slot schedule, so 100
lessons cover each cyclic start exactly 25 times. The report records canonical
shortcut fit, authority batch hashes, unique-input counts, witness coverage,
per-competitor demo survival, and explicit limits. It returns nonzero if a
declared canonical shortcut does not actually fit every canonical pair, any
competitor survives a complete lesson, any declared witness is missing from a
lesson's demos, an authority hash differs, or generated inputs collide.

This is bounded evidence against declared competitors, not universal induction.
