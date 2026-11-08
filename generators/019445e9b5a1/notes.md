# Working notes: 019445e9b5a1

## Intended rule and authority

Column 0 is a per-row color header. In a row with a nonzero header, every
nonzero cell in columns 1 onward is recolored to that header. A row whose
column-0 cell is 0 keeps its payload colors. The selected Racket authority was
not changed; generator v2.0.0 pins canonical `RULE_HASH = "f0e910e5b6d0"`.

## Reversed decisions from v1.2.1

The prior generator exposed palette/texture controls that were dead aliases,
placed degenerate negative fixtures in the ordinary texture domain, accepted
unknown override keys, and validated declared axes against difficulty-local
ranges. It also had no executable semantic contract and gave zero exact
canonical-profile support in the easy and hard 20-draw bands.

Version 2.0.0 removes the misleading texture API and keeps four exact,
band-independent controls: `grid_h` 4..8, `grid_w` 6..12, `n_headers` 1..3,
and `n_payload` 4..12. Unknown keys, non-integer values (including booleans),
out-of-range values, and unknown difficulty names fail loudly.

## Production distribution

Default production draws use a deterministic three-profile schedule. Every
three consecutive sample indices contain a `canonical_core` draw with profile
4x8 and six total colors, plus broader/contrast draws. The ordinary sampler
uses two or three distinct nonzero headers. Every generated header row has a
payload whose color differs from its header, and every input has a nonzero
payload in a headerless row. These witnesses make the transformation visible,
distinguish per-row recoloring from a global color, and distinguish preserving
headerless payload from erasing it.

`self_check` intentionally describes the lawful task domain rather than forcing
all teaching witnesses on canonical inputs. The stronger default-teaching
requirements live in executable semantic witnesses and task tests.

## Shortcut evidence and reusable probes

The real canonical pairs do not falsify the wrong rule “header 0 erases
payload.” A minimal counterexample is retained at
`counterexamples/headerless-payload.json`. Executable rivals for identity,
global-first-header recoloring, and erase-headerless-payload are declared in
`generator.py`; `workspace/reference_probe.py` provides an independent mirror,
observables, and the same rival predictions for portable tests.

## Final evidence

Final generator SHA-256:
`a95dfe6dc79eb24c223a6dad735b64117dedae6d0769968e9571bfedbc9a5846`.
The after battery is 12/12 green. The focused task suite is 38/38 green. The
override gate accepted 20,970/20,970 draws with zero findings. The profile floor
found exact canonical-profile support in every band (19/60 pooled). All three
semantic witnesses fired on 600/600 default draws; the 12-lesson smoke had zero
ambiguities in production and 0/48 query rotations. The larger census materialized
300/300 lessons and 1,200 unique inputs, with zero production or rotation
ambiguities against the three declared rivals.

## Known limits

The rival set is finite and does not prove unique induction against every
possible program. Production lessons are certified for the default sampler;
callers assembling lessons entirely from explicit overrides (for example,
forcing one header in every demonstration) must rerun `lesson_identifiable`.
The schedule guarantees one exact canonical profile, not the full canonical
joint distribution.
## Current reviewer considerations

Source SHA-256: `a95dfe6dc79eb24c223a6dad735b64117dedae6d0769968e9571bfedbc9a5846`.

# Decisions for 019445e9b5a1

## D1 — Keep the selected Racket authority unchanged

The canonical rule and all three canonical inputs agree on per-row recoloring.
The defect was in sampling and contracts, not labels. I pinned
`RULE_HASH = "f0e910e5b6d0"` and changed no canonical/Racket source. Rule-smoke,
Racket lint, and authority sync are green in `checks/after/`.

Rejected alternative: changing the rule to erase payload in headerless rows.
That shortcut fits the available canonical labels but conflicts with the written
row-header semantics and with the retained minimal witness.

## D2 — Replace nine misleading controls with four exact controls

The prior texture/palette surface contained dead aliases and negative fixtures
inside the ordinary domain. The replacement API is only `grid_h`, `grid_w`,
`n_headers`, and `n_payload`, each exact and valid in every difficulty band.
This keeps controllable semantic variation without claiming controls that do
nothing.

Rejected alternative: preserve compatibility aliases. The defect lint measured
four helpful textures as byte-identical to the untextured draw, and aliases make
unknown/renamed controls look successful. A clean break at v2.0.0 is less
misleading.

## D3 — Use constructive placement rather than rejection sampling

The sampler first reserves one mismatch per header row and one headerless-row
payload, then realizes every selected palette color and fills remaining slots.
All legal joint axis values are constructible on the minimum canvas, so no
incompatibility declaration is needed. This is why the final override gate can
accept 20,970/20,970 draws with no findings or implicit rejections.

Rejected alternative: retry random layouts until witnesses happen. That gives
seed-dependent failure tails, makes exact counts fragile, and can silently bias
the accepted distribution.

## D4 — Make every default grid individually self-teaching

Default draws use two or three distinct headers, a visible mismatch in every
header row, and retained payload in a headerless row. One grid therefore refutes
identity, global-first-header recoloring, and erase-headerless-payload. This is
stronger than relying on witness coverage only after aggregating many lessons.

Rejected alternative: allow mostly ambiguous grids and hope a three-example
lesson combines the needed witnesses. The original generator had correct labels
but no executable guarantee that a lesson taught the intended rule.

## D5 — Separate lawful-domain validation from curriculum witnesses

`self_check` accepts canonical lawful inputs and checks shape, colors, header and
payload counts, and at least one visible transformation. It does not require all
three production witnesses. Stronger teaching constraints are declared as
`SEMANTIC_WITNESSES`, rival mappings, and `lesson_identifiable`.

Rejected alternative: force multiple headers and headerless payload in
`self_check`. That would falsely reject lawful canonical/task-domain inputs and
conflate data validity with lesson quality.

## D6 — Schedule canonical support deterministically

`sample_index % 3` selects `canonical_core`, `broad`, or `contrast`. The core
profile is exactly 4x8 with six total colors, while the other profiles preserve
shape/count diversity and difficulty effects. Every three consecutive default
samples contain canonical support; no probabilistic dry spell can remove an
entire band.

Rejected alternative: a fixed probability prior. The before profile gate found
zero exact hits in easy and hard at 20 draws each. A deterministic period makes
the support guarantee inspectable and replayable.

## D7 — Treat finite rival testing as evidence, not proof

The declared rivals are the three concrete shortcuts implicated by the task:
identity, one global header color, and erasing headerless payload. Production
lessons and every allowed query rotation were checked against them. The 300
lesson census covers 1,200 unique inputs but does not enumerate all programs.
This limitation is stated rather than converting a finite check into a universal
identifiability claim.

## D8 — Build portable reviewer tools with the repair

`tests/test_generator.py` uses portable canonical helpers and contains 38 focused
regressions. `workspace/reference_probe.py` is independent of production code and
exposes the rule mirror, observable counts, and rivals. The minimal canonical-
shortcut counterexample is stored as data rather than only prose, so later agents
can replay and extend the finding.
