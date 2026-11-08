# Working notes: 5666b68dd4b9

## 2026-09-29 full review

### Canonical reading

- `(0,0)` is the selected body color.
- `(0,w-1)` is a transform code: 1 clockwise, 2 rotate 180°, 3 flip left-right, otherwise identity. The canonical test uses 4.
- The selected-color tight crop is transformed and transparently centered relative to the interior of the unique color-8 rectangular frame on a blank output.
- The authority uses floor-half placement in whole-grid coordinates; when a crop is wider than the frame interior, nonzero motif cells can overwrite a frame edge.

### Baseline findings

The imported generator rejected the canonical code-4 input, provided almost no canonical-profile support, exposed fake/dead axes and invalid textures, silently accepted unknown overrides, and had no semantic contract. Before battery: 6 green, 1 advisory, 5 failed.

### Selected design

- Exact canonical grid profiles: 10x11, 10x12, 11x12, 11x13.
- Canonical frame profiles: 6x5 and 7x4.
- Four-example schedule cycles codes 1..4 while holding selector and source shape fixed.
- Source motifs are asymmetric for every non-identity transform.
- A wrong-color object is always larger than the selected motif.
- Alternating examples put wrong-color noise inside the frame; the output must clear it.
- Later lesson blocks change source placement to avoid a four-pair periodic stream.
- Public axes are only values that can be generated and observed exactly.

### Semantic rivals

Declared executable rivals cover ignoring the code, always rotating clockwise, selector→transform lookup, memorizing canonical selector/code pairs, selecting the largest body object, and preserving frame-interior content. Eight witnesses prove disagreement. An intermediate witness was too broad for code 4; retained failure evidence led to restricting unseen-pair claims to non-identity pairs.

### Verification

After battery: 12/12 green. Strict census 600/600, canonical accepted 4/4, witnesses 8/8, rival claims 8/8, lessons 12/12. Rule smoke checked 120 protected-Racket cases with zero mirror mismatch. Focused pytest suite: 8 passed.

### Reusable probe

Run `workspace/review_probe.py` to build a four-code lesson, evaluate rivals/witnesses, and produce a selector-code shortcut counterexample. Add `--racket` with an activated Racket runtime to verify the result against the protected authority.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a894ec3d03b38e2d7a91b9269cced43654b6e73d8c811c2309cf22fd4f5e485a`.

# Decisions: generator 5666b68dd4b9

Each decision records the observed baseline rationale when recoverable, alternatives considered, the falsifying probe, and the remaining limitation.

## D1 — Preserve the selected Racket authority

**Choice.** Leave the canonical Racket program and canonical row unchanged; repair the generator and validation contract around them.

**Original rationale.** Unknown. The imported generator had drifted away from the authority by treating only codes 1–3 as valid, but the authority itself already encoded the intended fallback: any other code is identity.

**Alternatives.** Rewrite the authority to reject code 4; change the canonical test; or special-case code 4 only in `self_check` without exposing it in generation.

**Probe.** Before repair, `rule_smoke`, `racket_lint`, and `authority_sync` were green, while `self_check` alone rejected the canonical code-4 input. After repair, protected Racket/Python mirror parity is 120/120 and the explicit shortcut probe also matches.

**Failure mode / limitation.** This preserves the authority’s surprising transparent-paste spill-over on tight frames. Changing it would require a rule/canonical review, not a generator-local cleanup.

## D2 — Treat code 4 as a first-class identity branch

**Choice.** Schedule exactly codes 1, 2, 3, and 4; map them to clockwise, 180 degrees, left-right flip, and identity fallback.

**Original rationale.** The old generator apparently tried to avoid identity as “degenerate,” but that rationale was not documented and contradicted the canonical held-out case.

**Alternatives.** Continue generating only 1–3; admit code 4 only as a canonical exception; or add arbitrary codes beyond 4.

**Probe.** A regression test runs one fixed selector/shape through all four codes and requires four valid outputs with non-identity source asymmetry. Semantic coverage observed all four profiles in every difficulty band; code 4 fired 152/600 draws and refuted “always rotate clockwise” on all 60 checked witness cases.

**Failure mode / limitation.** Normal generation uses only code 4 for the fallback branch even though the authority treats every other code as identity. This keeps the visible code language aligned with the canonical task instead of inventing unsupported symbols.

## D3 — Use exact canonical grid and frame profiles

**Choice.** Cycle grid profiles `10x11`, `10x12`, `11x12`, `11x13` and frame profiles `6x5`, `7x4`.

**Original rationale.** The old broad dimension axes were likely intended to add variety, but difficulty-specific ranges made declared values false and generated almost no canonical-profile support.

**Alternatives.** Keep broad dimensions with carefully constrained packing; sample around the canonical envelope; or weight canonical profiles while permitting extras.

**Probe.** Baseline exact support was 1/60 with one canonical input rejected. Final profile gate accepts 4/4 canonical inputs and records exact/envelope support 60/60, 20/20 in each band.

**Failure mode / limitation.** Dimension diversity is intentionally bounded. The generator varies structure within profiles rather than claiming unsupported size generalization.

## D4 — Declare only observable, overrideable axes

**Choice.** Expose `transform_code`, `grid_profile`, `frame_profile`, and `distractor_layout`; reject unknown keys.

**Original rationale.** Unknown. The old metadata mixed dimensions, fixed descriptive labels, palette counts, and negative fixtures; several axes were unprobeable or contradicted actual draws.

**Alternatives.** Mark fixed labels diagnostic; retain every historical axis and repair each draw path; or expose raw height/width separately.

**Probe.** Each declared value is generated, recovered by `observe_overrides`, and round-tripped in tests. Final override gate reports PASS, zero findings, and unknown-key verdict `rejected`.

**Failure mode / limitation.** Palette and shape identity remain internal variation rather than public axes. They can be promoted later only with truthful domains and observation logic.

## D5 — Decouple selector color from transform code inside lessons

**Choice.** Keep selector and source shape fixed for four demonstrations while cycling code 1→4.

**Original rationale.** The canonical training examples correlate selector 6/7/9 with code 1/2/3, so an imported generator that changes both together risks reinforcing the strongest shortcut.

**Alternatives.** Randomize both independently without lesson structure; randomize selector only; or rely on the canonical code-4 test as the sole counterexample.

**Probe.** The semantic rival `selector_color_lookup` maps 6→clockwise, 7→180, 9→flip-left-right. The `selector_code_decorrelation` witness fires on 441/600 strict draws and disagrees with the rival on all 60 checked firings. Four-demo lessons are identifiable 12/12.

**Failure mode / limitation.** A single generated example does not by itself teach the code mapping; the contract assumes four demonstrations, matching `EXAMPLES_NEEDED = 4`.

## D6 — Include adversarial distractors that survive structural validation

**Choice.** Always include a wrong-color body object larger than the selected motif; alternate whether another wrong-color distractor appears inside the frame.

**Original rationale.** The old generator contained distractors, but no evidence showed they refuted plausible rivals. Negative “textures” instead produced invalid scenes.

**Alternatives.** Use only outside distractors; make the selected motif always largest; or keep invalid no-frame/no-selector fixtures in the normal domain.

**Probe.** `selector_beats_larger_wrong_colour` fires 600/600 and refutes the largest-object rival on all 60 checked cases. Frame-interior noise fires 324/600 and refutes preserve-interior on all 60 checked cases. A focused test confirms those cells are cleared from output.

**Failure mode / limitation.** Distractors are intentionally compact and do not cover every possible object topology.

## D7 — Mirror the authority exactly, including centering spill-over

**Choice.** Parse selector, selected-color crop, code, and color-8 frame; clear the output; redraw the frame; then transparently paste the transformed crop using the authority’s floor-half whole-grid coordinates.

**Original rationale.** Unknown. The imported implementation approximated the rule but lacked an executable parity contract.

**Alternatives.** Clip paste to the frame interior; force the crop to fit; or infer placement from generated metadata rather than the input grid.

**Probe.** Canonical examples, 120 protected-Racket smoke cases, and the replayable shortcut case all match the Python mirror exactly. Tests include the canonical tight-frame spill-over behavior.

**Failure mode / limitation.** The visual frame can be partially overwritten when the transformed crop is wider than its interior. This is authority parity, not a packing bug.

## D8 — Vary placement between lesson blocks

**Choice.** Hold structure constant within each four-example lesson, then flip source placement/order in later blocks.

**Original rationale.** The first repaired schedule accidentally repeated only four input/output pairs forever for one seed because every axis cycled with period four.

**Alternatives.** Add random jitter to every demonstration; expand the lesson to five examples; or ignore diversity because semantic gates already passed.

**Probe.** A new regression demanded at least five unique input/output pairs from eight consecutive draws. It failed at four before this change and passes afterward; full diversity gate remains green.

**Failure mode / limitation.** Variation is deterministic and finite, which is desirable for replay but can still have longer-period correlations.

## D9 — Make semantic claims executable

**Choice.** Declare six rival implementations, eight witness predicates, a witness-to-rival map, strict canonical validation, and lesson-identifiability logic.

**Original rationale.** None existed; the baseline semantic stage explicitly reported `NO_CONTRACT`.

**Alternatives.** Document shortcuts only in prose; declare witnesses without executable rivals; or rely solely on generic distribution tests.

**Probe.** Final semantic gate is strict 600/600, 8/8 witnesses firing, 8/8 rival claims verified, and 12/12 lessons identifiable. An intermediate warning exposed an overbroad unseen-pair witness; the retained failure drove a stronger test requiring every firing to refute its rival.

**Failure mode / limitation.** The rival catalog is deliberately finite. New shortcut hypotheses should be added as executable functions plus counterexample witnesses.

## D10 — Ship a replayable reviewer tool and focused tests

**Choice.** Add `workspace/review_probe.py` and eight generator-local tests.

**Original rationale.** The workspace was empty, so future agents had no one-command way to reproduce the semantic reasoning or protected-authority check.

**Alternatives.** Store only static JSON evidence; rely on the full battery; or put one-off scripts outside the selected generator.

**Probe.** The tool builds a four-code lesson, evaluates all competitors and witnesses, emits the exact selector/code counterexample, and optionally executes protected Racket. It runs from both source-tree and exported-runtime layouts. The focused suite passes 8/8.

**Failure mode / limitation.** Protected execution still requires the supplied/installed Racket runtime and `RACKET_PATH`; without `--racket`, the tool reports mirror-based evidence only and labels it accordingly.
