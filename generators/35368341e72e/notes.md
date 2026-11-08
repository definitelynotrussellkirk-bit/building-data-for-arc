# Working notes: 35368341e72e

## Intended rule and authority

Distinct nonzero keys in row 0 label non-overlapping 3x3 prototypes in rows
1--3.  Reading the nonzero keys in the last row from left to right forms an
ordered query.  The output concatenates the named prototypes, preserving
repeated keys, with one zero column between adjacent 3x3 blocks.

The selected canonical Racket authority was not changed.  Generator v3.0.0 pins
`RULE_HASH = "dfe1312c69fd"`; final generator SHA-256 is
`c9684fe1e2f9b3a74dd8474424b2a3098b328eb07f34f458e18c1aa6b83ca265`.
A prototype may be entirely background; one canonical example requires this.

## Decisions and reversals

The imported v2.2.0 design advertised palette, density, texture, degenerate,
and query controls that were dead, overlapping, clamped, or outside the lawful
domain.  V3 removes those controls and exposes four exact axes only:
`grid_h=5..12`, `grid_w=11..20`, `n_keys=1..3`, and `query_len=2..3`.
Unknown, non-integer, boolean, and out-of-range overrides are rejected.

The width/query ranges were narrowed after a regression showed that old legal
settings could make the gallery wider than the input, an unseen transformation
relative to canonical examples.  The new domain guarantees output width at
most 11 and input width at least 11.

The strongest canonical-fitting shortcut is to deduplicate the query.  All
canonical queries use distinct keys, so v3 deliberately repeats a key in every
generated query and declares executable witness/rival hooks.  The minimal
Racket-labelled disagreement is in `counterexamples/deduplicate-query.json`.

A deterministic `canonical_anchor` profile (`seed % 3 == 0`) fixes 6x11,
three keys, and query length 3 so every difficulty has exact canonical-scale
support.  Other seeds explore the full valid domains.  `EXAMPLES_NEEDED=2`;
production lessons use two demonstrations and one query.

## Evidence and tools

The final battery is 12/12 green, selected task tests are 51/51, and a
300-lesson / 900-rotation census found no ambiguity against the declared rival.
`workspace/reference_probe.py` is an independent Python oracle;
`workspace/qualify.py` replays canonical labels, generated draws, shortcut
counterexamples, and profile support in one machine-readable command.

## Known limits

The semantic evidence covers the explicitly declared duplicate-dropping rival,
not every possible hypothesis.  The canonical anchor is deterministic rather
than a proof of full-support probabilities.  Catalog approval and training
admission are outside this repair and remain unchanged.
## Current reviewer considerations

Source SHA-256: `c9684fe1e2f9b3a74dd8474424b2a3098b328eb07f34f458e18c1aa6b83ca265`.

# Decisions for `35368341e72e`

## D1 — Keep the selected Racket authority unchanged

**Prior state.** The generator had no `RULE_HASH`, although the selected
canonical rule already expressed the intended lookup-and-gallery operation.

**Decision.** Pin `RULE_HASH = "dfe1312c69fd"` and make Python generation,
validation, the mirror, tests, and independent probes conform to that authority.
Do not alter canonical or archival Racket data.

**Why.** All canonical pairs and the minimal counterexample are labelled
correctly by the selected rule.  `rule_smoke`, `racket_lint`, and
`authority_sync` are green in the after battery.  Changing the authority would
have hidden generator defects rather than repaired them.

**Limit.** Authority sync reports a pre-existing archival raw-code divergence;
the selected executable authority is synchronized and no authority bytes were
changed here.

## D2 — Replace decorative axes with four exact semantic controls

**Prior state.** Version 2.2.0 advertised palette, density, texture, degenerate,
and query controls that were dead, overlapping, clamped, or outside the lawful
rule domain.  Unknown and bad overrides could be silently accepted.

**Decision.** Expose only `grid_h`, `grid_w`, `n_keys`, and `query_len`.  Validate
unknown keys, booleans/non-integers, and range violations before drawing.  Make
`observe_overrides()` recover all four controls from the generated grid.

**Alternatives rejected.** I did not keep no-op compatibility aliases: they
would preserve the exact axis-honesty failure the assignment asks reviewers to
remove.  I did not advertise malformed “degenerates”: they are negative tests,
not training inputs for this rule.

**Probe.** The final full override matrix is green; the first test-first run
showed 30 behavioral failures before implementation.

## D3 — Restrict width/query domains to preserve the canonical transformation

**Prior state.** Broad combinations could produce a 3-row gallery wider than
the input.  That changes the canonical “extract and shrink” relation into an
unseen reshape task.

**Decision.** Use input width 11–20 and query length 2–3.  The maximum output
width is therefore 11, never larger than the minimum input width.  Keep height
5–12 and key count 1–3 because they preserve the same rule and have legal
layouts.

**Alternative rejected.** Padding the input or clipping outputs would add a new
rule.  Declaring many joint incompatibilities would make the public contract
harder to use without adding semantic diversity.

**Probe.** `test_generated_outputs_preserve_the_canonical_shrink_relation`
failed against the old domain and passes in the final 51-test suite.

## D4 — Make repeated query keys mandatory

**Prior state.** Canonical demonstrations contain no repeated query key.  The
plausible rival “deduplicate the final-row query before gallerying” therefore
fits every canonical label.

**Decision.** Generate a query of length 2 or 3 containing at least one repeated
key, preserve left-to-right order, and allow one-key dictionaries (where all
queries necessarily repeat).  Declare the rival in all semantic-contract
namespaces and provide a witness predicate.

**Alternative rejected.** Sampling repetition only occasionally leaves small
lessons vulnerable by chance.  Increasing demonstration count without changing
support also fails to distinguish the rival.

**Probe.** The Racket-labelled witness is
`counterexamples/deduplicate-query.json`.  Independent qualification found
192/192 generated counterexamples; the 300-lesson census refuted the rival in
all production lessons and all 900 query rotations.

## D5 — Reserve a deterministic canonical-profile anchor

**Prior state.** The broad generator produced too few exact 6×11, three-key
examples for the pinned profile floor, especially by band.

**Decision.** `schedule_profile()` uses `seed % 3 == 0` for an exact 6×11,
three-key, length-3 anchor.  The other two residues draw from full public domains
with difficulty weighting.

**Alternatives rejected.** Making all samples canonical would erase useful
shape diversity.  Relying only on probabilistic weighting made the profile gate
seed-fragile.

**Probe.** The pinned census has at least one anchor in easy, medium, and hard
and exceeds the pooled 25% envelope floor.  The independent qualification saw
8 easy, 8 medium, and 6 hard exact hits in its schedule.

## D6 — Validate structure, including an all-background prototype

**Prior state.** The original validator did not enforce the complete dictionary
layout.  My first strengthened draft assumed every prototype contained a
nonzero cell.

**Decision.** Validate rectangular ARC grids, distinct/spaced row-0 keys,
prototype-band placement, zero separator rows, and declared query keys.  Treat
an all-background 3×3 prototype as lawful because a canonical demonstration
contains one.

**Alternative rejected.** Requiring a visible prototype would contradict the
selected authority and canonical data.

**Probe.** The canonical empty-prototype regression failed first, then all
canonical pairs passed both the validator and an independent oracle.

## D7 — Use two demonstrations and one query for lesson assembly

**Decision.** Set `EXAMPLES_NEEDED = 2`.  Every generated pair contains the
repeated-query witness, so any one demonstration refutes the declared rival;
two demonstrations retain variation without unnecessary lesson length.  The
production census used the actual 2-demo/1-query assembly and the rotation pass
held out each of the three pairs once.

**Limit.** This supports only the declared finite rival set.  It does not prove
that every human- or model-invented hypothesis is uniquely excluded.

## D8 — Build task-local independent qualification tools

**Decision.** Add `workspace/reference_probe.py` and `workspace/qualify.py`.
The probe independently parses the dictionary and computes the gallery; it does
not import `rule_mirror`.  Qualification replays canonical pairs, generated
samples, the duplicate-dropping rival, and the pinned profile schedule in one
machine-readable command.

**Why.** Future agents can distinguish a broken mirror from a broken generator
and reproduce the key invariants without reconstructing this review.

**Limit.** The Python translation is independent of generator implementation,
but the Racket authority remains the final label source; the retained
counterexample was therefore also run through `arcpuzzles apply`.

## Parametric admission prototype — review-790aa8341b8feb64

The approved production generator remains byte-for-byte unchanged at SHA-256
`c9684fe1e2f9b3a74dd8474424b2a3098b328eb07f34f458e18c1aa6b83ca265`.
The new task-local adapter lives under `workspace/parametric/` and exposes one
episode-fixed parameter:

- `assembly=query_order`: exact canonical Racket bytes, SHA-256
  `dfe1312c69fd8633b6a2b5ae2c5bf91276111d2e3ed07c84f6eb48dab8956066`;
- `assembly=fewest_cells_first`: decode every queried key to its 3×3 prototype,
  count active cells per occurrence, stable-sort by count while preserving ties
  and repeated keys, then gallery in that order; program SHA-256
  `99a8c138b81cdb1774f3b30ba8e6a1dbf808e8732b45603598807a2c05a75870`.

Inputs are matched across settings. Episodes accept 2–6 demonstrations and emit
exactly four sequentially revealed, distinct queries. The fourth query is 30×30,
contains five key/prototype bands and seven query occurrences, and produces a
3×27 answer. `public_turn()` exposes only demonstrations plus the current query
input; settings, answers and future queries remain private.

The authoring audit spans both settings, seeds 0/17/97 and demonstration counts
2/3/6: 18 jobs and 272 protected-Racket evaluations. Every label matched Racket,
the selected setting was the sole retained finite-rival survivor, matched inputs
and public projection held, and the 30×30 nondefault case changed under the
canonical query-order counterfactual.

Native qualification retained four jobs (two settings × seeds 0/17), four
queries per job and 40 protected-Racket evaluations with status `qualified`.
The source-bound causal witness is `checks/35368341e72e/causal/witness.json`:
step A derives per-occurrence prototype counts `[6,3,5,2,6,4,3]`; step B consumes
that intermediate to produce `[2,3,3,4,5,6,6]`. Skipping A preserves query order
and changes the protected-Racket final answer. Reviewer readiness does not grant
variant approval, owner acceptance or training admission.

Known scope: this is a two-setting hypothesis family, not a claim that every
possible assembly ordering is identifiable. The owner must integrate exact bytes
and rerun native qualification plus acceptance on the live source before any
catalog or training decision.
