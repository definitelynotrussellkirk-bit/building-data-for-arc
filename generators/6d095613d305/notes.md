# Working notes: 6d095613d305

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `5ac475aba254060b6f5a4d848c3b50b76a5e00fa55c497baf27f25b404641c68`.

# Distribution and implementation decisions

Task `6d095613d305`; assignment `review-cc655a435b7de032`. Final generator
SHA256: `5ac475aba254060b6f5a4d848c3b50b76a5e00fa55c497baf27f25b404641c68`.
Where the predecessor source did not explain a choice, its original rationale is
recorded as unknown rather than inferred.

## D1 — Keep the canonical Racket authority

**Choice.** Preserve the existing Racket program and pin its normalized hash as
`bd682e817aa3`.

**Rationale.** All five public pairs agree with the rule, and the baseline rule
smoke already executed 120 valid transformations without crash or mutation. The
observed defects were in the input distribution and contract, not labels.

**Alternatives rejected.** Rewriting the authority in Racket would add semantic
and synchronization risk without fixing the lesson distribution. Treating the
new Python mirror as label authority was also rejected; it is only a fast checked
oracle.

**Probe / limitation.** Final rule smoke checked 120 Racket/Python pairs with
zero mismatch, and authority sync passed. Finite parity does not prove the two
programs equivalent for every possible grid.

## D2 — Remove inert axes instead of pretending to implement them

**Choice.** Replace the predecessor's singleton, unprobeable, dead palette, and
negative-fixture controls with four literal axes: height 8–18, width 9–20,
equal waypoint count 3–5, and crossing profile `separated|single|multiple`.
Reject unknown keys.

**Original rationale.** Unknown. The predecessor declared controls such as
`crossing`, palette/texture variants, and fixed position bias but did not make
them observably affect ordinary output.

**Alternatives rejected.** Inventing semantics for every old palette/texture
name would expand scope without teaching the geometric rule. Keeping diagnostic
singletons would preserve a misleading public API.

**Probe / failure mode.** The baseline override stage stopped before its matrix;
the final matrix accepted 27,990/27,990 draws across 311 cases and three bands,
and rejected the unknown key. This intentionally breaks callers that depended on
silently ignored misspellings.

## D3 — Use semantic overlap profiles, not a boolean crossing promise

**Choice.** Define the profile from the Racket-equivalent output: zero overlap
cells, exactly one, or at least two.

**Rationale.** These categories are directly observable and teach both the path
construction and the special output color. A boolean `crossing=yes|no` was
unprobeable and underspecified whether one or many cells should overlap.

**Alternatives rejected.** Merely biasing random points toward each other does
not guarantee a witness. Hand-authoring one fixed template per class would be
easy to fingerprint and would reduce geometric diversity.

**Probe / limitation.** The final independent sample is exactly 144/144/144 over
432 draws. `multiple` has no upper bound beyond the grid geometry; the generator
does not promise a uniform overlap-count distribution within that class.

## D4 — Rejection-sample general layouts while requiring teaching witnesses

**Choice.** Sample distinct waypoint cells, then accept only layouts with the
requested profile that disagree with vertical-first, column-major, and
first-to-last-only rivals. Crossing layouts must also disagree with later-color
overwrite.

**Rationale.** This keeps varied layouts while making the intended distinctions
causal in every ordinary example.

**Alternatives rejected.** Unconstrained scatter was the predecessor behavior
and could leave the rule underdetermined. Fully constructive templates would be
faster but risk a small, recognizable grammar. Post-hoc relabeling to force a
profile would alter the input/output rule and was rejected.

**Probe / limitation.** The sampler is deterministic and bounded at 1,024
attempts. No exhaustion occurred in the 27,990-case override battery or the
reported 432-draw probe. An untested adversarial seed/override combination could
still exhaust the bound; failure is loud rather than returning a weak grid.

## D5 — Make every three-example window complete

**Choice.** Cycle `single`, `multiple`, `separated`; `EXAMPLES_NEEDED=3`. Test
all cyclic starts, not only schedule-aligned blocks.

**Rationale.** Any three consecutive samples then contain both positive overlap
examples and a negative example, while preserving variation in their order.
This directly matches the packet's three-demo solve episode.

**Alternatives rejected.** Independent random profile choices can produce three
non-crossing or three simple examples. A longer schedule would demand more demos
than the current reviewer/export path supplies. Always putting the canonical
anchor first would make absolute sample position more learnable than necessary.

**Probe / limitation.** The reusable probe tested 216 cyclic windows over all
three start residues, 24 seeds, and three bands; all were identifiable. This
contract assumes sequential sample indices. An external exporter that skips or
reorders samples must re-run lesson identifiability on its assembled episode.

## D6 — Put canonical-scale support in the single-overlap slot

**Choice.** When the default schedule selects `single`, draw 9–10 rows, 11–13
columns, and three waypoints per color. Explicit axis overrides remain literal.

**Rationale.** Public examples are in this scale/count envelope and have one or
two overlap cells. Anchoring one of three slots raises recognizable support in
every difficulty band without making all examples canonical-sized.

**Alternatives rejected.** Difficulty-only size ranges caused zero hard-band
support. Literal replay of stored public inputs would risk memorization. Making
all slots canonical-scale would sacrifice breadth.

**Probe / limitation.** Framework profile floor improved from 6/60 envelope hits
with zero hard support to 24/60 with support in every band. The independent probe
found 147/432 strict hits, not exactly one third, because some non-anchor draws
also happen to satisfy the strict predicate.

## D7 — Mirror the authority and name plausible rivals

**Choice.** Add an input-pure Python mirror plus four explicit competitors:
vertical-first bends, column-major waypoint order, first-to-last-only paths, and
later-color overlap overwrite.

**Rationale.** These are compact, plausible rules that fit superficial examples
and correspond to distinct information the demonstrations must convey.

**Alternatives rejected.** Generic dihedral or identity shortcuts are useful
sanity checks but do not target this task's semantic ambiguity. A large arbitrary
rival zoo would increase maintenance and false-positive risk.

**Probe / limitation.** Each rival is refuted in every lesson and in its relevant
single-example domain. The set is not exhaustive; an unmodeled hypothesis may
still survive a finite lesson.

## D8 — Fail closed on malformed or semantically weak inputs

**Choice.** Validate rectangularity, literal ARC colors, exactly two nonzero
non-9 colors, equal 3–5 counts, horizontal and vertical movement, non-identity,
and meaningful middle waypoints.

**Rationale.** A generator validator should describe the lawful training domain,
not merely accept anything the Racket program can execute.

**Alternatives rejected.** Permitting color 9 in input conflates a marker with
the output-only overlap signal. Accepting two-point or collinear chains weakens
all-waypoint and bend evidence.

**Probe / limitation.** Focused malformed cases and all public pairs are tested.
The lawful domain is intentionally narrower than the mathematical program's
maximum possible input domain.

## D9 — Build a reusable curriculum audit

**Choice.** Add `workspace/curriculum_probe.py`, which imports the generator's
actual competitor declarations, tests all cyclic starts, records source hashes
and denominators, and exits nonzero on invalid or unidentifiable windows.

**Rationale.** The lesson contract is easy to regress if only marginal diversity
is measured. Future agents need a one-command source-bound census.

**Alternatives rejected.** A notebook or one-off inline script would be harder to
replay and easier to detach from the final source. Copying competitor names into
the probe would let declarations and measurement drift.

**Probe / limitation.** The retained report covers seeds 0–23 and 432 records;
it is deterministic but finite. It uses the checked Python mirror for scale and
therefore relies on the separate 120-case Racket parity check.

## Review 2026-10-25 — assignment `review-08d0cd0ce36b9d08`

The reviewed base generator and canonical Racket rule remain unchanged. A native
three-setting family was added under `workspace/parametric/`: byte-exact
`canonical`, plus `longer` and `shorter` variants that trace both waypoint paths,
select one by measured length, and recolor that selected trace to 8 away from
9-valued intersections. Inputs are matched across settings, support 2–6 demos
and 1–4 independent queries, alternate which sorted color is longer, contain
real intersections, and include substantive 30×30 queries.

The bounded self-audit covered 12 seed/demo/setting jobs and 144 protected-Racket
executions; no named fixed-order, fixed-path, paint-both, or alternate-setting
rival survived all visible demonstrations. The retained wrong-intermediate
witness substitutes the shorter trace for the selected longer trace and changes
157 final cells. Public projection produced 24 one-query views; 36 private-field
invariance mutations and 6 visible-change controls passed.

The canonical ledger stores this task's lone test pair as a mapping rather than
a list. `preflight_compat.py` normalizes only that legacy collection during base
label inspection, preserves the original record hash, and delegates all source
binding, parametric execution, and receipt construction to the stock authoring
preflight. The authoring qualification passed all 6 setting/seed jobs and all 5
original labels. This is reviewer evidence only; exact-source owner qualification,
acceptance, and training admission remain pending.
