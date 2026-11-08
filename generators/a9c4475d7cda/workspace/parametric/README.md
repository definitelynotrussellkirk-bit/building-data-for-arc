# Proposed panel-count threshold family

The current task-local prototype combines the two source-bound returns without
changing the production generator or canonical Racket authority. One hidden
`min_panel_count` is fixed across all demonstration and query pairs:

| Value | Rule | Status |
| --- | --- | --- |
| `1` | paint 1 for a panel containing at least one color-6 cell | proposed |
| `2` | paint 1 for a panel containing at least two color-6 cells | exact canonical default |
| `3` | paint 1 for a panel containing at least three color-6 cells | proposed |

The API keeps the existing `min_panel_count` name. `demos` and `queries` are
independent exact integers in `1..16`; seeds are exact integers in `0..2**63-1`.
The deterministic chooser cycles `2,3,1`. Inputs are independent of the chosen
setting and reuse all four lawful production profiles, with the prototype cycle
starting at `balanced`. That first zero-containing profile gives a one-demo
threshold-1 lesson both output values, refuting constant masks. Every retained
pair contains count-1, count-2 and count-3 panels, distinguishing all three
declared thresholds. Sampling retries duplicates and fails rather than returning
a short episode.

`programs/threshold-{1,2,3}.rkt` retain the exact Racket programs. `rule_text`
checks them against one guarded edit of the hash-pinned canonical program; the
default remains byte-identical. Python labels returned by the thin `adapter.py`
are claims. `materialize` executes the chosen and alternative programs in Racket,
replays the canonical examples, and derives teaching certificates from
demonstrations alone.

From the extracted packet directory:

```sh
python3 review.py run python3 generators/a9c4475d7cda/workspace/parametric/prototype.py \
  --seed 17 --demos 3 --queries 4 --out ../checks/parametric/current-thresholds
python3 review.py run python3 generators/a9c4475d7cda/workspace/parametric/prototype.py \
  --verify-only --out ../checks/parametric/current-thresholds
python3 review.py run python3 -m pytest -q generators/a9c4475d7cda/tests
```

The writer preflights the complete batch, rejects duplicate visible payloads
before creating output, and physically emits public files in visible-ID order.
Public filenames hash the exact saved model-visible bytes; hidden settings, seeds,
programs and query labels remain private. The low-level `write_episodes` validates
Python claims; it does not itself obtain Racket authority. Use `materialize` and
the independent `verify_evidence` replay for that boundary.

The replay verifies the exact inventory, current generator/prototype/adapter/
program bindings, strict labels, deterministic inputs, saved Racket programs,
canonical parity, all declared alternatives, teaching certificates and exact
public bytes. It rejects rehashed source/program/label/certificate tampering; a
new manifest cannot turn such a mutation into current evidence.

Current decisions and measured checks are in
`../../evidence/conflict-reconciliation.json`. Original 74-test/two-setting
worker evidence and the separate 83-test/three-setting qualification receipt
remain reviewer-reported provenance for their original bytes. They do not qualify
the merged implementation. `promotion.json` declares a proposed interface only;
no acceptance, production API change, variant approval or training admission is
performed here. Finite threshold-rival checks do not establish arbitrary-rule
identifiability or learning value.
