# Proposed match-relation variant for bdd177308a5b

**Status: proposed prototype, unapproved.** The episode-level parameter is
`match_relation ∈ {exact, quarter_turn_cw}`. The canonical/default `exact`
setting returns the canonical Racket source byte-for-byte. The alternative
changes only the unique shape-comparison expression so an outside object must
match the template after one clockwise quarter turn.

The reasoning pattern stays fixed: read the colored template inside the gray
L-frame, normalize outside connected objects, select the unique object under
the episode relation, and recolor it gray. Four authored lawful inputs each
contain a distinct exact candidate and clockwise-quarter-turn candidate, so the
other setting is refuted by every demonstration. One parameter is sampled once
per episode before three demonstrations and one query are materialized.

Every retained label, rival prediction, and all eight canonical replay pairs
are executed with the bundled `RacketBridge`. Public episode files contain only
labeled demonstrations and a masked query input. Private evidence retains the
seed, selected parameter, query answer, exact Racket source, and hashes.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/bdd177308a5b/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/match-relation-v1

python3 review.py run python3 -m pytest -q \
  generators/bdd177308a5b/tests/test_parametric_variant.py
```

Seeds 0 and 1 cover both settings. This bounded two-setting fixture study is
not production approval and does not establish uniqueness against undeclared
ARC interpretations.
