# Working notes: ecd1058990ce

## 2026-10-26 parametric build and adversarial hardening

The base generator and exact canonical default remain unchanged:

```racket
(rule! (lambda (g) (scale-map g (list 2 1 2) (list 2 1 2))))
```

The proposed `target_weighted` setting expands rows containing the top-left
color at least twice, then chooses a target-densest column from that expanded
intermediate. The retained wrong-order witness changes source counts
`[2,2,1]` into intermediate counts `[11,20,10]`, moving the winner from column
0 to column 1.

A second adversarial pass found that the old minimum two-demo lesson admitted a
plausible shortcut: count target cells only in rows classified as heavy and
ignore the one-copy light rows. That rule fit both old demonstrations for every
seed and failed query index 2. It is now retained as protected-Racket
`heavy_rows_only.rkt`. The second demonstration was replaced with a light-row
tie-break case, while the first still rejects raw-count wrong order. The two
minimum examples choose middle and right respectively, so fixed-column rules
are also rejected.

Inputs remain setting-independent and prefix-stable for 2–6 demonstrations and
1–4 queries. The query outputs remain 30×30, 21×30, 12×30, and 3×30. The
returned evidence includes a reproducible before/after 1,000-seed shortcut
audit, focused protected-Racket tests, the bounded probe, task tests, authoring
preflight, public projection/privacy checks, and a fresh sequential witness.

This is authoring evidence only. Owner source review, exact native acceptance,
and training admission remain pending. The finite rival family and bounded seed
census do not prove universal program uniqueness or training gain.
