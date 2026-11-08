# Proposed diagonal-mode parameter for `888fb4310749`

This task-local prototype preserves the original rectangular billiard-block
family and changes one executed rule choice: stamps propagate along **both**
diagonal families (the canonical/default setting), only the falling `\\`
diagonal, or only the rising `/` diagonal. Everything else remains fixed:
extract the nonzero rectangle, use period `height + width`, paint rotated
companions in color `9 - source_color`, clip partial stamps, and paint source
stamps last.

The selected production generator, canonical program, `RULE_HASH`, and approval
state are unchanged. This is proposed prototype evidence, not a production axis
or training-admission claim.

## Parameter

- `diagonal_mode`: allowed `("both", "falling", "rising")`; default `"both"`.
- The default Racket text is byte-for-byte the canonical program.
- Alternatives replace both exact sign lists `(list 1 -1)` with `(list 1)` or
  `(list -1)`.
- The hidden value is chosen once from the deterministic episode seed and reused
  across every demonstration and query. The default is three demonstrations and
  four distinct queries; both counts are independently configurable from 1 to 8.
- Every retained fixture is required to make all three mode outputs different,
  so demonstrations identify the selected mode before the query.

## Run retained evidence

From the outer extracted packet directory:

```bash
python3 review.py run python3 generators/888fb4310749/workspace/parametric/prototype.py \
  --base-seed 20261023 \
  --demo-count 3 \
  --query-count 4 \
  --out ../checks/parametric/888fb4310749-diagonal-mode-v2
```

The command writes exact `.rkt` files, three private Racket-labelled episodes,
redacted public challenges, a same-input cross-mode witness, `report.json`, and
a SHA-256 manifest. Each public filename is the SHA-256 of the exact visible
bytes written through `reviewer_support.public_challenge_bytes`; exports are
sorted by that ID and duplicate visible payloads fail. Public query outputs,
hidden modes, seeds, rival predictions, and program text are omitted. Python is
used only as an independent parity oracle; all retained labels and rivals are
executed through the included Racket bridge.
