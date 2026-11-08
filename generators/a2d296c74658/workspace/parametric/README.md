# Complete vertical gaps, then use the completed state

This separate native family has one episode-fixed parameter:

| `completion_mode` | Executed rule |
|---|---|
| `vertical` | Exact canonical source: fill every zero with immediate vertical orange (7) neighbors using yellow (4). |
| `cascade` | Perform the canonical stage, then fill every remaining zero with immediate horizontal yellow (4) neighbors using red (2). |

Stage B reads the completed A grid. Its yellow anchors may be original, newly
created, or mixed. A can also fill a prospective B center, making it ineligible:
the cross with vertical 7s and horizontal 4s must finish with center 4. This
creates a real input-dependent state dependency; reversing the stages changes
outputs. Each stage is exhaustive, preserves occupied centers, and reads a
fixed input state. Within-stage sequential writes and repeated copies of a
single stage are equivalent here because a stage never creates its own endpoint
color; the audit does not count those as distinct mechanisms.

## Native interface and input construction

`adapter.py` imports the exact adjacent `prototype.py`. `program(settings)`
returns a complete `rule!` string; the canonical default is byte-for-byte the
catalog program. `generate(seed, settings, demos=3, queries=4)` supports 2–6
demonstrations and independently 1–4 queries. Seeds are exact integers in
0..2^63−1. Claim labels are deterministic Python values; qualification executes
every label through protected Racket independently.

The semantic domain is any rectangular exact-integer ARC grid with each side
1–30. Generated inputs span 7×9 through 30×30. The first core demo is 9×11;
the second is a 25–27 by 27–29 complete contrast mosaic. Its shuffled, reflected
11×11 tiles teach long shared chains, old/new/mixed anchors, blocked centers,
wrong colors, wider gaps, both-stage order, crowded valid gaps and boundaries.
Long chains have at least five gaps per line; the mosaic has more than 32
targets in each stage. These controls repair the concrete finite-rival findings,
not every possible invented count threshold.

Two demos are sufficient for the supported finite bank; larger demo counts keep
that core and add independent dense scenes. Four shuffled query profiles are
7×9, 15×19, 24×28 and 30×30. The large query has substantial nonzero content in
every quadrant, long interior chains and many operations in both stages.
Each scene has an independent seed stream; inputs match across settings, count
prefixes are stable, returned lists are fresh, and global random state is unused.
Horizontal/vertical reflections preserve the semantics. No 90-degree rotation
invariance is claimed: the two stages use different axes and colors.

## Independent tools and evidence

`rivals.py` implements a separate Python oracle and standalone Racket rivals.
`audit.py` checks deterministic assembly, distinct inputs, labels, demonstration
fit before query disagreement, source hashes, supported counts, and large and
thin boundary fixtures. It reports actual Racket calls separately from cached
or logical comparisons. The stale-original-predicate and reversed-stage programs
are explicitly identified as one equivalent mechanism.

Initial isolated examples allowed wrong contextual restrictions to fit both
demos and fail dense queries. Their protected witnesses and minimal controls
are retained in the returned checks. The repaired mosaic includes same-color
neighbors beside and beyond endpoints, unrelated neighboring colors, and
boundary positives. Reusable tests pin those observations.

From the packet's outer directory:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest generators/a2d296c74658/tests -q
WORK/.venv/bin/python review.py run python3 generators/a2d296c74658/workspace/parametric/audit.py --out ../checks/a2d296c74658/semantic-audit-new.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest a2d296c74658 --evidence generators/a2d296c74658/workspace/parametric/evidence/current --include generators/a2d296c74658/tests/test_parametric_native.py --include generators/a2d296c74658/tests/test_parametric_rivals.py --reported-checks 'Actual bounded current checks only'
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify a2d296c74658 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/a2d296c74658/qualification --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/a2d296c74658/qualification/qualification.json --out ../checks/a2d296c74658/preview
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/a2d296c74658/preview
```

Use new output directories after edits and the native guarded replacement for
an existing inventory. The preview exporter is already bundled; reveal only
one chosen `public/<hash>.json` at a time. The order map, directory listing,
future queries, settings and answers remain controller-private. The verifier
checks serialization and source bindings without another Racket replay.

Production `generator.py`, canonical source and existing approval records are
unchanged. Its retained cap-two/edge-chain teaching findings remain production
findings; the native family supplies new distinguishing demonstrations without
silently clearing those audits. Finite checks do not prove universal inference,
learning benefit, owner acceptance or training admission.
