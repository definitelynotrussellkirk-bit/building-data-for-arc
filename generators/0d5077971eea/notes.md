# Working notes: 0d5077971eea

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review — version 2.0.0

The v1.2.1 source never supplied zero-header markers, foreign interior colors,
or header-eight rows. Several advertised controls were no-ops and `[[]]` could
crash self_check. The review repairs those behaviors without changing Racket.

Default draws now alternate core/canonical-profile preference and rich wide/high-
density examples. Every three-demo production lesson has a rich witness when
accepted indices stay consecutive; the retained source-bound census and all
cyclic windows validate actual assembled lessons. Eight rivals fit all three
canonical pairs and are deliberately separated. The source/seed-specific reports
and failed iterations are in the returned review package for assignment
`review-fdeaf0f7f2e659d5`; see its REVIEW.md, DECISIONS.md and RESULTS.json.

One genuine first repair allowed the first marker to precede a deliberate
zero-header spectator; markers now follow it constructively. A second defect at
seed 6127 on a 5x7 grid with ten colors and high density exhausted palette slots;
a randomized markerless row reserves sufficient capacity without clipping.
The unused historical axis names now fail explicitly; callers should use the
four documented AXES. Each difficulty keeps their full explicit domain.

The sampler is intentionally productive: pure identity grids are rejected, even
though the raw Racket rule is defined on them. Mandatory witness rows, fixed zero/
eight semantic colors, and width-density coupling are distribution limits, not
universal task coverage. Any downstream lesson reshuffling must be checked under
its real assembly policy. No model training gain was measured.
## Current reviewer considerations

Source SHA-256: `a338b592c839a0ef4bec46d972da6ca06e45f2caf0353869343902badc5b3f61`.

# Decisions: 0d5077971eea

## Source and authority

The immutable draw selected `review-fdeaf0f7f2e659d5`, task `0d5077971eea`, from
the supplied 20261003-232145 packet. Baseline generator SHA-256 is
`315c7676bc7a70900a85fe823a93926cd2e641ffe659146d79d5a47ff98cb991`.
The final generator SHA-256 is
`a338b592c839a0ef4bec46d972da6ca06e45f2caf0353869343902badc5b3f61`.
The selected normalized Racket hash is `1130750019d1`; the raw canonical program
SHA-256 is `071b2a298d5c565c469357c6b6662d4fe94ec5e123bbe48fa36861d8e40691df`.
No rule or catalog file changed. There was no supplied task-specific prior return
to use as a lead: the notes were placeholders and associated notes empty. The
baseline comment gives a sparse-row motivation; other original choices are
unknown and are not retroactively justified here.

## D1 / R1 — Follow the executable zero-header exception

The canonical prose says to replace marker 8 by the row header; the executable
rule adds a nonzero-header condition. Its actual rule is: change interior 8 to
column-zero key when that key is nonzero; preserve every other cell. Empty
headers and header 8 therefore preserve marker 8. The original generator's
blank rows contain no markers and cannot teach the difference between skipping
and erasing those markers. Added zero-header rows with markers and nonzero
spectators make the distinction observable. Changing Racket to erase markers
was rejected: this would alter the selected authority and is not needed to
repair the distribution.

## D2 / R1 — Vary irrelevant content and distinguish row scope

Interior spectator colors are unchanged by the authority, so the revised
sampler places a foreign color beside a transforming row's markers. Header-8
rows with spectators cover an existing canonical header value. Two transforming
rows of different key colors on opposite parity classes distinguish row-local
headers from the canonical alternating-row shortcut. Rows, colors, and their
assignment to primary/secondary roles are randomized. A markerless palette row
adds useful header-only examples and supplies the capacity proof in D5.

All draw labels remain fixed to their task meaning: zero is the empty-header
color and eight is the marker color. Arbitrary background/marker palette
permutations were rejected because this Racket authority is color-specific.
Identity-only grids remain lawful under the raw rule but are excluded from the
productive generator/validator domain. They are explicit negative tests, not
advertised ordinary textures.

## D3 / R2 — Honest controls over decorative axes

| Exact control | Domain | How it is observed |
| --- | --- | --- |
| grid_h | 5..12 | Number of rows |
| grid_w | 7..16 | Number of columns |
| n_distinct_colors | 4..10 | Set cardinality of all input colors, including 0 and 8 |
| marker_density | low / med / high | Maximum marker count in a transforming row: 1 / 2..floor((w-1)/2) / larger |

Every joint combination is constructive. Integer controls reject booleans,
strings, fractional values and nulls; unknown names and invalid values fail
visibly. Caller overrides use the full declared domain in every difficulty;
profile preferences affect defaults only. GenCtx records the actual chosen
value, and `observe_overrides` reconstructs it from pixels.

Removed `palette_kind`, `palette_size`, `anchor_corner`, `asymmetry_force`,
`position_bias`, and texture aliases because the previous implementation did
not realize them. Keeping decorative axes as accepted no-ops was rejected.
Inventing additional semantics solely to retain those names would add scope
without useful task coverage. Callers using those names must update; the major
version bump makes the contract change explicit. Four real axes provide
1,680 combinations per band, not a claimed count of independent semantic axes.

## D4 — Canonical profile support and complete lessons

Canonical profiles are `(6,9,5)`, `(7,9,4)`, `(7,9,5)`. Core draws favor heights
6/7, width 9, and palette size 4/5 while retaining broader possibilities. Rich
odd-index draws default to width 10..16 and high marker density. This breaks
fixed-nine-column and at-most-three-marker rules that fit every canonical pair.
Both profiles occur in every band. Rich height/width/palette weights grow with
difficulty and core density preferences also change, without invalidating any
explicit override.

The period-two schedule was chosen because every three consecutive draws
contains a rich draw. Complete five-pair lessons also retain a rich draw in
every cyclic three-demo window. Purely independent random witness occurrence
was rejected after a real intermediate failure: sample seed 13, start 1,
rotation 3 permitted `first_nonzero_key` to fit all demonstrations and disagree
on the query. `checks/intermediate-cyclic-witnesses.json` retains it; the exact
intermediate source is `checks/intermediate-cyclic-generator.py`. The repaired
spectator placement ensures every zero-header marker comes after a nonzero
spectator, so this rival is directly contradicted.

Production rejects duplicate or unproductive pairs and advances indices. The
reported guarantee therefore rests on the measured accepted lesson population,
not on requested start residues alone. The 300-lesson final census has 1,500
unique inputs and no rejected-pair population substitution. Arbitrary downstream
shuffling, filtering, or using fewer than three demonstrations can destroy the
curriculum property; run the saved-lesson probe on the actual export policy.

## D5 / R4 — Construct capacity instead of retrying

Independent review found a genuine crash at seed 6127, sample index 1,
height 5, width 7, ten colors, high density. Dense optional rows could consume
all slots needed for absent palette colors. The failed implementation is retained
as `checks/intermediate-capacity-generator.py`; its SHA is
`8b37e5215e4db012ba7d055160cbd14661faba9076009f2abf18c7a8b1033edb`.

The repair reserves one randomized markerless row. At height five there is still
one row after the two transforming rows, zero-header row, and optional header-8
row. Its width-seven interior offers six slots. At most six of the eight
possible key colors remain missing after two different header colors are placed.
Thus capacity is sufficient even at the joint extreme, without retries, dropping
colors, changing density, or silently reducing an override. The 10,000-seed
boundary sweep complements this constructive bound.

## D6 — Rivals are executable hypotheses, not labels

Eight rivals are declared and dynamically scored: erase_zero_key,
recolor_all_nonzero, first_nonzero_key, first_non8_key, alternating_rows,
at_most_three, column_lt9, and nearest_colored_header. All fit all three usable
canonical pairs. Racket supplies production outputs; the generator does not
call a Python answer routine to label data. Local tests additionally use an
independent row oracle checked on canonical and literal witnesses.

The saved-census rotation probe checks generator/census hashes, instance hashes,
complete populations and all actual declared namespaces. It does not copy a
hard-coded rival list or regenerate a different population. Eight hypotheses
repeated in three namespaces are reported as eight hypotheses. The tool is
retained in the task workspace for future revisions, with tests for stale source,
corrupt instances, and incomplete population metadata.

## D7 — Keep audits and optional shared changes separate

A1 and A2 expose absent distinguishing counterexamples in other tasks. Their
Racket-backed witnesses and source identities are retained in `AUDIT.md` and
`checks/audit/`; their generators remain unchanged as the assignment requires.
F1 supplies an optional tested shared profile-floor patch under `checks/proposals/`.
It is absent from the selected source delta. Exact-vs-envelope policy should be
an explicit maintainer choice; the undeniable double-counting defect and that
policy choice are distinguished in the proposal.

## Remaining limits and rejected claims

No Qwen3.5-9B training run, held-out ARC score, model speedup or training gain was
measured. A finite declared-rival audit is not universal identification, and
canonical size/palette support is not itself semantic coverage. The mandatory
witness rows and rich width-density correlation remain distribution choices;
future broadening should preserve exact-control capacity and check actual
lesson assembly. The final solves are program revisions and work logs, not
captured token-level traces. Query correctness remains private to later scoring.

## 2026-10-25 native parametric admission candidate

Added a source-bound two-setting family without changing the accepted generator
or canonical rule. `row_local` returns the exact selected canonical Racket text;
`densest_source` selects the unique row with the most interior 8 markers and
uses that row's header as an input-derived intermediate before painting all
interior 8s. Inputs are matched across settings, prefixes are count-stable, the
minimum two demos distinguish the settings and named rivals, and the fourth
query is a content-rich 30×30 scene.

Reviewer qualification replayed 40 labels in protected Racket across two seeds
and both settings. Public projection produced 16 sequential one-query views;
export conformance and 24 private-field invariance checks passed. A protected
counterfactual witness changes only the selected header intermediate and changes
the final grid. This is ready reviewer evidence, not owner acceptance or a claim
of universal identifiability/training gain.
