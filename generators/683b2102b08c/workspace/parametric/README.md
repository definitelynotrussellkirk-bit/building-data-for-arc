# Majority-mask attachment: native parameter family

`attach_side=left|right` changes which horizontal side receives the secondary
mask. `left` returns the selected canonical Racket source byte-for-byte. `right`
places the secondary's left edge at the main mask's rightmost column. Both
settings retain one-column bounding-box overlap, floor vertical centering,
complete disconnected color masks, and secondary-over-main painting order.

The rule first counts colors below the yellow separator, selects the unique
majority mask, and computes its full bounds. Those input-dependent bounds choose
the secondary mask's destination. Whole-color aggregation is essential: a
largest-component shortcut changes both the retained mask and the destination.

## Supported requests

- Exact integer seed in `0..2**63-1`.
- Exactly `{"attach_side":"left"}` or `{"attach_side":"right"}`.
- Independently requested 2–6 demonstrations and 1–4 queries; ordinary native
  qualification uses 3 demonstrations and 4 queries.
- The same seed has identical inputs under both settings. Demo and query streams
  are independent; changing either count preserves its prefix and the other
  stream. All inputs within a returned episode are distinct.
- Four-query profiles are 8×8, variable medium, variable large, and dense 30×30.
  The largest input has a split 14×9 majority mask and a 9×10 secondary mask,
  real output-edge contact, holes, disconnected parts and overlaps. Orange 7 and
  yellow 4 keep their canonical roles; both foreground colors vary.

Two constructive demonstrations show a disconnected color majority against a
larger connected minority, odd centering and actual overwrites, then reverse
color/position roles with equal heights, a larger secondary box, asymmetric
masks and a disconnected secondary. Extra
demonstrations vary geometry and density. The first two also distinguish the 21
declared rival programs in the retained bounded self-review; this is not a proof
against arbitrary programs.

## Reproduce

From the outer packet folder, with its verified Python and Racket setup:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/683b2102b08c/tests/test_parametric.py -q
WORK/.venv/bin/python review.py run python3 \
  generators/683b2102b08c/workspace/parametric/verify.py \
  --out ../checks/683b2102b08c/recheck
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  683b2102b08c --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/683b2102b08c/fresh-qualification --summary
```

Use new output paths on reruns. `verify.py` uses the existing protected Racket
bridge and public-byte helpers, checks labels and plausible shortcuts, retains
one four-query example for each setting, and verifies first-turn projection.
It also serves as a small reusable audit runner for future edits to this family.

## Evidence and status

`evidence/current/report.json` records 18 lesson configurations across seeds
0, 8 and 17, with 1,320 protected grid evaluations. All 21 rivals are rejected
by the demonstrations in every exercised configuration. The 30×30 cases contain
at least 100 foreground cells, with both masks spread across substantial bounds.
`examples.private.json` contains full labels, setting programs, rivals and their
predictions. The two `public/` files contain three demonstrations and exactly
one current query, named only by their visible-byte hashes.

Give the consumer only the current public prefix. Keep the remaining three
queries, programs, settings and query answers controller-side, revealing each
new query after the previous answer with no total-count or final-turn hints.
The existing consumer owns those turns; this prototype does not add a controller.

`evidence/manifest.json` and the returned native qualification bind the proposed
source. The owner must qualify and accept the integrated exact bytes before
native accepted export. No production generator, canonical rule, approval
record, training admission or allocation weight is changed by this proposal.
