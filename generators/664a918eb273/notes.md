# Working notes: 664a918eb273

Review: `review-222f5dfc78c493dd`, 2026-10-02.

The imported summary described a fixed shape bank, but the actual v3 generator
used arbitrary walks and random placements. Its weak self-check accepted all
900 sampled inputs even though 696 violated the independent packing geometry
contract. On the comparable 450-input Racket execution prefix, 198 outputs lost
colored cells. Successful execution did not establish faithful labels.

The v4 repair constructs a valid packed chain before generating its separated
input. It restores a substantial small canonical-style component, supports
repeated colors and two-cell paths, and includes positive anchor offsets and
vertical misalignment to refute executable shortcuts. Axes are real, observed,
validated, and rejected explicitly when geometrically incompatible.

The canonical Racket program and canonical JSONL are unchanged. Two active
`racket_target.target_code` copies were synchronized to that exact program;
archival `raw_code` and all unrelated fields were preserved. Source divergence
had independently failed the authority check; this was not a semantic rule fix.

The final 12-stage battery and standalone lint pass. The focused suite passes
29 tests. Final-source census: 9,000 safe sampled inputs and 450 Racket executions
without cell loss or safe-geometry disagreement. A relocated runtime repeats the
29 tests and 600 geometry / 90 Racket cases. The repository-wide suite has one
separately reproduced, pre-existing packet-bootstrap test failure; see the root
review rather than interpreting local green checks as a wholly green repository.

The required fresh Python solve was completed after generator work: three visible
examples matched; masked correctness is unknown. Earlier reference exposure was
declared, and no reference was consulted during the solve phase. Notes are a
reviewer-authored work log, not a captured token trace.

Limitations: monotone-column construction, bounded dimensions and path lengths,
disjoint input column bands, a deterministic two-profile schedule, finite tests,
and no per-lesson identifiability guarantee or learning-curve experiment.
Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b6b2f5c0872fe92583cf63168b0bda683a8746ccd0181d71b18e142c4daf02b9`.

# Distribution decisions and rejected alternatives

Assignment: `review-222f5dfc78c493dd`. No original author interview or intent record
was available; original rationales below are labeled unknown unless stated by the
supplied code or metadata. The implementation changes inputs, not canonical labels.

## D1 — construct the packed chain before scattering inputs

Original behavior: arbitrary small walks in separated bands with independently
chosen rows. Original rationale: unknown, plausibly diversity, not asserted as fact.
Probe: 696/900 geometry violations and 198/450 Racket outputs losing pixels.
Decision: choose each next path from the previous packed exit, within retained
height, before varying its input row. Reserve enough width for every later piece.
Alternative rejected: keep generating unsafe scenes and filter/retry. That hides
rejection bias and makes override support unreliable. Alternative rejected: grow
the output canvas or preserve clipped pixels by changing Racket, because it would
change the established rule. Limitation: safe construction is a restricted family,
not an exhaustive enumerator of every possible valid path scene.

Reasoning: every new path starts where the intended transform will place it. A
forced east step makes its first cell the sole leftmost cell. Later growth uses
only east/up/down and touches only the previous tip, so it does not create forks,
cycles, or a filled 2x2. Its other endpoint remains rightmost. Packed rows stay in
bounds; later pieces occupy new column bands. Scattering is a translation that
does not alter shape; executing endpoint joins reverses those translations. This
explains the construction; independent tests still check its implementation.

## D2 — preserve a canonical-style floor, not only expanded scenes

The old summary claimed fixed 9x20 grids; actual v3 dimensions varied and the
baseline profile-floor diagnostic found no strict canonical-like sample. Canonical
examples have three rows and small widths. Original historical mismatch rationale:
unknown. Decision: deterministic alternating profiles, with even indices h=3,
w=9–11, 3–4 paths, zero anchor, and lengths 2–4; odd indices h=4–12, w=14–30,
2–5 paths, positive anchors, and longer paths. Set strict floor 0.4 and expose
schedule labels. The final profile gate passes without relaxing its threshold.
Alternative rejected: all large cases, which risks losing the near-canonical
lesson. Alternative rejected: only canonical-size bank samples, which leaves
shortcuts and long-path transfer unexplored. Limitation: alternating indices are
predictable; this is a transparent sampling schedule, not evidence of a superior
curriculum. No learning comparison or arbitrary per-lesson coverage guarantee.

## D3 — paths, lengths, and difficulty

Original observed lengths were 3–6. New growth permits length 2 (including canonical
short pieces) through 11. Default core cap is 4; expanded easy/medium/hard caps are
5/8/11, with unspecified difficulty cap 9. Growth can stop earlier when no safe
step exists, so “cap” is not an exact requested length. Maximum component width is
5 and total canvas width is bounded. Alternative rejected: promise a length axis
that the geometry cannot always realize. Limitation: no westward turns or arbitrary
self-avoiding polyominoes; path length alone is not a complete difficulty metric.
The final census observes every length 2–11 and all object counts 2–5.

## D4 — component identity must not be color identity

Original palette sampling used one distinct color per path. That shortcut is
unjustified because canonical examples can reuse a color in disconnected objects.
Decision: choose an exact distinct-color count k in 1..n, place each selected color
at least once, and reuse colors for the remaining paths. Eight-neighbor separation
still defines objects. Alternative rejected: force every path to one color, which
would remove useful palette diversity. Measured: 6,156/9,000 final draws reuse a
color; a linked executable rival that drops later same-color paths is actually
refuted. Color-reuse presence alone was not accepted as sufficient semantic proof.

## D5 — anchor, gaps, and input rows

The first object must remain fixed, including a nonzero left margin. Core samples
anchor at zero; expanded defaults anchor at 1–3. Gap ranges 1–3; gaps keep even
same-colored neighboring paths as distinct eight-connected components. First
path rows remain their packed rows, while later input rows are sampled independently
among fits. Alternatives rejected: always left-justify (fits canonical but loses
rule information); always keep packed rows (teaches horizontal-only compaction);
zero gaps (can merge components and change the rule's object extraction).
The exact left-margin counterexample and measured 150/300 default disagreements
are in QUESTION_ANSWER.md and checks/adversarial-audits.json.

## D6 — six real, measured integer axes

Expose grid_h 3–12, grid_w 8–30, n_paths 2–5, n_distinct_colors 1–5,
gap 1–3, anchor_col 0–3. Explicit axes use these public domains rather than being
silently restricted by difficulty bands. Unconstrained coordinates adapt to fit;
explicitly incompatible combinations raise IncompatibleLayout with implicated
axes. Unknown names, non-integers including bool, and values outside the domains
raise clear errors. observe_overrides measures the resulting grid, not requested
metadata. Alternative rejected: clamp values or drop objects, because that makes
the control contract false. Twelve boundary cases plus invalid combinations are
regression-tested; the final override battery passes. Not every cross-product of
these domains is feasible, as separation consumes width.

## D7 — semantic checker and malformed inputs

The old checker only enforced basic background/color presence. Decision: verify
rectangular 1..30 grids, exact ARC integer colors, at least two separated objects,
monochromy, genuine four-connectivity after eight-connected extraction, two degree-1
endpoints, degree-2 interior pixels, unique left entry, right exit, disjoint bands,
and no clipping/overlap after translation. Alternative rejected: endpoint counts
alone; a diagonal cycle plus a line can fool degree-only validation. This checker
is deliberately an input-domain guard, not a label generator. Its accepted domain
can include safe cases outside the narrower constructor's monotone family.

## D8 — synchronize active authorities without rewriting history

The canonical program was already correct for this domain. The two active target
copies were behaviorally agreeing on sampled examples but source-divergent. Change
only their racket_target.target_code to canonical text; preserve raw_code and all
other fields. Alternative rejected: edit the rule to hide sampler defects, change
canonical demonstrations, or patch archival source. The exact field-only diff and
canonical ledger hash are in checks/authority-sync-repair.json. A canonical
solution test failed before the sync and passed after it.

## D9 — executable adversaries, not witness labels alone

The first semantic contract labeled features but the gate reported WEAK because
no rival implementation demonstrated a real output difference. Retain that failed
iteration and add executable rivals with explicit witness links. Test left-justify,
drop-repeated-color paths, and horizontal-only packing. Only the first is claimed
to fit all canonical pairs; the others are useful anti-shortcut contrasts, not
misrepresented as canonical-consistent. Rival renderers are diagnostic code and
are never used for training labels. Limitation: three rivals are not an exhaustive
hypothesis class and do not certify lesson identifiability.

## D10 — reusable tools remain task-local

Build independent geometry/Racket probes, a relocated-runtime check, fixed unsafe
fixtures, and findings-only audit probes under the allowed selected workspace.
Do not alter shared runtime or the two audited generators. Runtime mapping predates
new tests/workspace files, so portable_check copies those explicitly before moving
the runtime. Alternative rejected: global packaging changes without assigned scope
or broad compatibility tests. General improvements are separate F-numbered feedback.

## D11 — preserve failure and solve provenance

Retain red tests, intermediate batteries, the invalid CLI phase attempt, the audit
probe's first test-record-shape error, and the unrelated full-suite failure.
The fresh solve is not blind: prior rule exposure is declared. Its intentional
negative and the notes-only 3/3→2/3 correction remain visible. No private answers,
masked correctness, token traces, training gains, or admission status are inferred.

## D12 — a diagnostic census exit is not an acceptance verdict

Final self-review found the portability runner originally combined child exit
codes only, but path_probe intentionally exits zero after reporting old-generator
defects. Added a failing-first portable-verdict regression and a fail-closed
semantic adapter: require the complete 600/90 counts, five canonical matches, and
zero generation, geometry, self-check, pixel-loss, mismatch, or Racket errors.
Missing/incomplete reports fail. Reran 29 focused tests and the relocated runtime.
The generator source and solve episode hash are unchanged by this tooling fix.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/664a918eb273/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-parametric-tail-order:start -->
## D13 — native tail-order parametric family (review-86ca2328d7bac9f9)

Retain the canonical path-concatenation rule byte-for-byte as
`tail_order=left_to_right`. Add two private, episode-fixed alternatives that keep
the first path fixed and sort only the remaining paths by input-derived cell
count: `shortest_first` and `longest_first`, with original left-to-right order as
the deterministic tie-break. Every setting then uses the same sequential
endpoint-to-entry placement. This is a meaningful local rule change rather than
a palette remap, and the same seed/count request uses identical inputs across
settings.

The adapter supports 2–6 demonstrations and exactly four queries. Its six demo
profiles cover canonical scale, color reuse, single-color objects, dense five-path
layouts and larger grids. Four query profiles are independent of the demo count;
the last is a lawful 30×30 lifted input with colored content on rows 0 and 29.
The lift is parametric-only and does not change the approved production
generator's published axes. Sampling is bounded to 768 attempts per profile and
fails closed when all settings are not total, distinct, or safe.

The first demonstration is selected to distinguish all three settings and the
finite shortcut family: anchor removal, horizontal-only packing, color-order,
reversed tail and identity. A bug in the first audit draft built every rival at
once, so one clipping shortcut could incorrectly invalidate a valid selected
rule. Rival execution is now isolated per candidate; an invalid rival is a
refutation of that rival only. The retained 18-case audit covers seeds 0 and 17,
demo counts 2/3/6, all settings and four queries. This is finite evidence, not a
universal identifiability proof.

The public projection check writes exact `reviewer_support.public_challenge_bytes`
under full SHA-256 names. It verifies masked query answers and invariance to
private settings, seed, program and query-label mutations. A separate end-to-end
negative case leaks one query answer and confirms the saved-file verifier rejects
it with `public_schema` and `public_id` findings.

Native qualification passed for all three settings at seeds 0 and 17 with three
demonstrations and four distinct queries, totaling 78 protected-Racket
evaluations. The source-bound sequential witness names Step A as path extraction,
endpoint tracing, length measurement and tail ranking; Step B consumes that
ordered intermediate and the previous exit to place each next path. Replacing the
qualified shortest-first intermediate with the qualified longest-first order
changes the final grid under protected Racket. Reviewer status is `ready` only;
owner replay and exact integrated-source acceptance remain mandatory, and no
training admission is claimed.
<!-- arcpuzzles-parametric-tail-order:end -->
