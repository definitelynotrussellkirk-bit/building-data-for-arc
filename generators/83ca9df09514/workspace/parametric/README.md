# Proposed duplicate-key precedence parameter

**Status: PROPOSED prototype.** This task-local artifact extends only ARC task
`83ca9df09514`. It does not change the selected production generator, canonical
Racket authority, catalog kind, approval hashes, or shared parametric API.

## Rule and episode contract

The original task finds the uniquely dense template row. Each sparse key row
pairs nonzero destination colors with template colors at the same columns, then
broadcasts those destinations over every matching template-color group.

The prototype adds one episode-fixed parameter for the previously undefined case
where two nonzero keys in one sparse row align to the same template color but
carry different destinations:

| `duplicate_precedence` | Meaning | Status |
|---|---|---|
| `rightmost_wins` | Scan left-to-right and let the later key overwrite the earlier key. | Canonical/default |
| `leftmost_wins` | Scan right-to-left and let the earlier key overwrite the later key. | Proposed alternate |

The default program is byte-identical to canonical Racket source SHA-256
`cae56e2f8161ccd2fd21aa8b0d4e0b51318d3e114e626ea9097fab7c2602af87`
and rule hash `1dc6f00b70c9`. The alternate changes exactly the inner mapping-loop traversal
from `(range 0 w)` to `(reverse (range 0 w))`; template discovery, row roles,
color grouping, blank-row handling, and broadcast semantics are unchanged.

`parameter_for_seed(seed)` selects one setting for the whole episode. Consecutive
seeds selecting opposite settings share the same lawful inputs (`0/1`, `2/3`,
etc.), isolating the rule change. The retained episodes use two demonstrations
and four distinct queries; counts are independently configurable from 1 through
8. Every nonblank sparse row has a real conflicting duplicate, so each demo
contradicts the opposite setting before any query answer depends on it.

## Exact commands

Run from the extracted packet directory containing `review.py`:

```bash
python3 review.py setup
python3 review.py run python3 -m pytest generators/83ca9df09514/tests/test_parametric_duplicate_precedence.py -q
python3 review.py run python3 generators/83ca9df09514/workspace/parametric/prototype.py \
  --out ../checks/parametric/duplicate-precedence-v1 \
  --seeds 0 1 --demo-count 2 --query-count 4
```

The output directory must not already exist. All labels, rival predictions, the
distinguishing witness, and canonical replay are produced by the bundled Racket
runtime. Python only constructs inputs, materializes the two guarded programs,
and validates/export records.

## Evidence layout and visibility

- `public/challenge-<visible-hash>.json`: model-visible demonstrations and query
  inputs only. Filenames hash the exact visible bytes.
- `private/episodes/<visible-hash>.json`: seed, selected parameter, query answers,
  selected-program hash, and both Racket prediction sets.
- `private/rules/*.rkt`: exact executed programs.
- `private/canonical-default-check.json`: all ten source-qualified canonical
  labeled pairs replayed under the byte-identical default.
- `private/distinguishing-witness.json`: one input and both executed outputs.
- `manifest.json`: source/runtime identities, a public-ID-sorted episode index, hashes, and limits.

No seed, setting name, program text/hash, or query answer appears in a public
challenge. Different settings over paired inputs produce different visible
training labels and therefore different content-addressed public IDs.

## Limits

This is bounded authoring evidence for two declared settings, not production
approval or training admission. Conflicting duplicate keys deliberately extend
the production generator's accepted grammar; production samples still give
duplicate reveals the same value. Identifiability is checked only against the
opposite precedence setting, not arbitrary programs. The retained evidence covers
two paired episodes and finite input draws, while the focused tests cover strict
validation, canonical replay, Racket parity, sampler uniqueness, and export
privacy.
