# Bounded allocation-quality proposal

Ticket: `ticket-5b2bd7d1df8da57b`  
Seed: `dc9dda8e113b64a174ba744b9974506affe803fbeafe7eddc9943b477ac2642f`

## What the current packet shows

The packet's 500-record authoring draw is uniform, while the selected catalog
rows are almost entirely flat-weighted (`498` at `1.0`, `2` at `0.0`). The
selection itself is intentionally focused: 320 coverage records, 150 unfinished
approved originals, 28 recent returns, two public-evaluation coverage records,
and one runtime dependency. Of the 500, 293 are currently approved; 59 retain a
parametric prototype, and only 47 prototype READMEs even mention four-query
coverage. There are 178 records with at least one unresolved retained audit.
These inventories describe review state, not measured training value.

The reproducible three-record sample was the pinned task plus two IDs selected
with `random.Random(int(seed, 16)).sample(sorted(other_ids), 2)`:

- `a2e752ad6948`: current generator/rule identities match the manifest and
  catalog. Two source-current audits reproduce a three-demonstration global-
  parity shortcut. The generator declares no lesson schedule or semantic rival.
- `6143c7ef56be`: identities also match. One source-current audit reproduces a
  three-demonstration corners-only shortcut before an independent-layout query;
  it likewise declares no lesson schedule or rival.
- `d2a80a6f9495`: identities match and no unresolved audit is retained.

All three have catalog weight `1.0`, are approved, and have no retained
parametric/four-query prototype. This tiny sample cannot estimate library defect
rates, but it demonstrates that flat catalog weights do not encode current
teaching-risk or evidence completeness. Provenance also did not predict the
result: the sampled records include bank, training, and augmented ancestry.

## Alternative allocation to test

Do **not** change the training mixture from this ticket. Instead, run one
source-bound, 30-record owner experiment using current bytes:

| Stratum | Records | Reason |
| --- | ---: | --- |
| Source-current unresolved lesson/rival audits | 15 | Highest prior probability of an actionable teaching repair |
| Approved original-task records missing retained four-query evidence | 10 | Converts production-capable families into independently supervised episodes |
| Uniform approved controls | 5 | Estimates the opportunity cost of targeting |

For each record, spend at most ten authoring minutes and materialize one episode
with two demonstrations and four distinct queries where the production grammar
supports it. Execute all six labels through the selected Racket rule, check the
most concrete retained/plausible rival using demonstrations only, and record
source/rule hashes, retries, duplicate rejections, reviewer minutes, grid side,
and whether a usable lesson or a source-bound repair resulted.

Estimated upper bound: 30 records, 180 Racket labels, and five reviewer-hours.
Racket labeling is expected to be cheap relative to semantic review; the packet
contains no current per-record timing or dedup receipts, so that estimate must be
replaced by measured minutes in the experiment.

Compare strata by two cost-normalized outcomes:

1. usable, distinct, Racket-backed six-pair lessons per reviewer-hour; and
2. source-current teaching defects resolved per reviewer-hour.

Also report the share of outputs with side at least 20, but do not reward padding
or prototype-only settings. Deduplicate by the builder's real episode identity,
not by task ID alone.

## Stopping rule

Stop a record immediately on any source/rule identity mismatch. Stop a stratum
after ten records if fewer than 60% can produce four distinct queries or if more
than 25% remain ambiguous after the bounded rival check. Keep the present
allocation if the targeted strata improve the primary yield by less than 25%
over uniform controls or cost more than 1.5× reviewer minutes per usable lesson.
Only propose a training-weight change after the source-bound experiment reports
accepted episode counts, deduplication loss, and current model outcomes; high
loss alone is not a defect.

## Coverage limits

This proposal uses one three-record packet sample and dated r6 training context.
The packet does not include current per-record losses, candidate episode IDs,
accepted-export receipts, or measured deduplication cost. The prototype README
inventory is only a coarse coverage signal and was not treated as execution
proof.
