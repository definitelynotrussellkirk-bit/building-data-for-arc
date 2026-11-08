# Review notes — review-5994a478cf362114, round 2

## Scope and authority

Only this task's generator, documentation, task-local tests, and workspace tools
changed. The canonical Racket rule and both audit-only target generators remain
byte-identical. Associated notes are retained in `evidence/associated_notes.jsonl`.

## Cumulative repaired defects

- **R1:** the packet baseline omitted keys 2/4, restricted frames to squares,
  and rejected all five canonical inputs.
- **R2:** ordinary shapes could fail to distinguish all four rotations. The
  first key-contrast probe found 32/96 nonseparating intervention families.
- **R3:** retry placement and inaccurate metadata could under-realize requested
  geometry or fail exact-axis provenance. Constructive slots and observed-axis
  reporting repaired this.
- **R4:** the v3.2 fresh lesson used an asymmetric query key absent from all
  three demonstrations. The public-only lesson gate retained four rival outputs.
- **R5:** v3.2 replayed the exact same grid across difficulty bands for 36/128
  sampled seeds because generic `GenCtx` RNG salt excluded difficulty while
  canonical-scale supports overlapped.
- **R6:** 69/128 sampled three-demonstration lessons, and 38/128 naïve
  four-demonstration lessons, remained ambiguous under independent per-key
  quarter-turn maps because examples selected keys independently.
- **R7:** non-key-2 objects were sometimes already centered, leaving a
  key-correlated position shortcut and uneven evidence for recentering.
- **R8:** the reusable distribution probe inherited `puzzle_generators` only
  through caller `PYTHONPATH`, so its documented standalone command failed in a
  clean shell. It now bootstraps `repo/shared/runtime` from its own location and
  has a subprocess regression with `python3 -E -s` and no `PYTHON*` variables.

Version 3.3.0 salts all task-local free RNG labels by difficulty, schedules the
first-frame key across four consecutive samples, declares `EXAMPLES_NEEDED = 4`,
and forces every ordinary object off-center. The normal key override remains
explicit and broadcast to every frame.

## Final evidence

The final source passed all 12 inherited battery stages in source-bound isolated
runs, plus all 53 task-local tests. The input-only distribution probe sampled
256 seeds in each of three bands: 768 primary grids, all unique, no cross-band
same-seed duplicates, no centered ordinary objects, and no failed four-sample
key windows. A final Racket differential probe sampled 192 grids; all 192 matched
the independent Python transform, and all 48 selected-frame key families yielded
four distinct interiors.

Sixteen actual Racket-labeled episodes (four demonstrations/two queries each)
passed the public-only lesson gate. There were zero candidate rejections, zero
skipped sample indices, and query outputs were discarded before analysis. A
fresh public solve then found exactly one fit among 1,024 declared
key-rotation/centering hypotheses; all query keys were visibly demonstrated.
Private query correctness remains withheld.

## Boundaries

These are finite probes under explicit rival families, not general ARC
identifiability or model-training evidence. The key schedule introduces a
predictable four-sample curriculum pattern; it should not be represented as
IID key sampling. The slot packer is conservative rather than exhaustive. The
inherited override checker still uses legacy compatibility policy for combined
rejections. No shared admission code was changed, and `training_admitted`
remains false.

## Handoff

Run the commands in `workspace/README.md` after applying the cumulative delta.
Read source hashes before comparing evidence from v2.3, v3.0, v3.1, v3.2, and
v3.3. Failed runs and older probes are retained intentionally. Open separate
repair tickets for audit targets `40dea3d45f2a`, `e4cb0224ca42`, and the shared
subprocess-fixture failure; none belongs in this selected-task patch.
## Current reviewer considerations

Source SHA-256: `b3adc8e5389ad39d70f4b5dd9828f3352f9de1195c9d67f29139c7d5c3e10b92`.

# Decisions and rejected alternatives

Final decisions refer to generator v3.3.0, SHA256
`b3adc8e5389ad39d70f4b5dd9828f3352f9de1195c9d67f29139c7d5c3e10b92`.
They are engineering choices supported by retained probes, not model-training
ablations or claims of optimal probabilities.

## D1 / R1 — preserve the authoritative four-branch task

The unchanged task has keys 2/3/4/5 and square or rectangular frames. The packet
baseline sampled only 3/5 and rejected canonical inputs. Restore the actual
domain instead of narrowing labels to fit the old sampler. Every canonical input
is now valid and its recorded output still matches the unchanged Racket rule.

Rejected: ban key 2 because its rotation is zero; edit the Racket rule; retain a
square-only validator. Zero rotation can still move an off-center object through
recentring, and none of those alternatives represents the canonical task.

## D2 / R2/R7 — separate validity from informative ordinary sampling

Ordinary objects have four distinct normalized rotations and start away from
their eventual centered target for **every** key. This makes both the keyed turn
and recentering observable without changing semantics. The validator remains
broader and accepts symmetric/already-centered canonical inputs.

Rejected: require only `output != input`, test only the sampled turn, or force
asymmetry in all valid inputs. Those checks miss clockwise/counterclockwise
collisions or incorrectly reject valid domain members. Also rejected: keep the
F1 key-2-only off-center rule; it introduced a key-correlated pose shortcut and
uneven evidence for recentering.

Limitation: ordinary shapes intentionally cover a strong teaching subset, not
the full semantic domain. A future mixed curriculum can add invariant examples
with explicit lesson-level witnesses.

## D3 — guarantee that every key intervention fits

Objects remain connected monochromatic polyominoes whose bounding dimensions
fit the smaller frame-interior dimension. This permits all four rotations in
rectangular frames. The bounded shape search falls back to a known asymmetric L
and sorts set choices before random selection for deterministic reproduction.

Rejected: sample a large one-orientation-only object and hope the selected key
fits; silently crop after rotation; or return an empty object after bounded
search. The fallback frequency is not separately optimized and should not be
interpreted as a learned distribution.

## D4 / R3 — construct geometry before placing it

The generator chooses a feasible row/column/2×2 slot layout, draws exact canvas
and maximum interior axes through `GenCtx`, and places the requested number of
frames. A successful return never silently reduces `n_frames`. Explicit interior
or key pins broadcast to every frame; default observations report maxima and the
first spatial frame's key.

Rejected: retry placement then return fewer frames; silently shrink sampled
axes; report requested rather than observed values; or retrofit provenance after
drawing. Conservative slot rejection is not proof that an arbitrary packer
could not realize a tuple, so the limitation remains explicit.

## D5 — retain broad geometry plus canonical-scale support

Unpinned draws retain a one-third canonical-scale branch in every band so the
inherited canonical-profile gate has support, while two-thirds retain broader
band-dependent sizes/counts. Objects, offsets, colors, and placement are newly
sampled; no canonical grid is replayed.

Rejected: opt out of the profile gate, force every sample to canonical scale,
or loosen acceptance thresholds. One third is a transparent heuristic, not an
optimized mixture weight. Difficulty bands overlap in support by design.

## D6 / R5 — salt task-local free RNG by difficulty

F1 used overlapping canonical-scale support while generic `GenCtx` free-RNG
streams did not include difficulty. Exact same-seed grids therefore repeated
across bands for 36/128 sampled seeds. F2 appends an explicit band salt to every
task-local free RNG label (`layout`, regime, canonical scale, packing, keys,
objects). Axis draws still use normal `GenCtx` names for override provenance.

Rejected: make the bands geometrically disjoint, deduplicate only after export,
or change shared `GenCtx` globally. Disjoint support would turn difficulty into
a trivial size classifier; post-hoc deduplication hides wasted draws and cannot
repair episode construction; a shared runtime change is outside this task and
could alter thousands of generators.

The final 256-seed probe produced 768/768 unique primary grids. This is finite
evidence, not a mathematical guarantee of no collision at larger sample sizes.

## D7 / R4/R6 — use four coordinated demonstrations

Set `EXAMPLES_NEEDED = 4`. For unpinned draws, first-frame key is
`2 + ((seed + sample_index) mod 4)`, so any four consecutive samples cover every
branch. Additional frame keys remain sampled. Explicit `key=` overrides still
broadcast normally.

This directly addresses the retained F1 evidence: 69/128 three-demo lessons and
38/128 naïve four-demo lessons were ambiguous under independent per-key turns.
Sixteen actual F2 episodes subsequently passed the public-only gate without
resampling or skipped indices.

Rejected alternatives:

- **Only increase demo count to four.** F1 evidence shows independent random keys
  still fail 38/128 sampled lessons.
- **Rejection-sample whole episodes in shared admission.** That is a larger
  shared-interface change and can hide unbounded candidate rejection costs.
- **Assume the arithmetic key-angle relation.** Valid for a curriculum that
  explicitly teaches that prior, but the query-relevant gate intentionally
  checks a more conservative independent-key rival family.
- **Read query answers to decide admission.** The gate needs only demonstrations
  and query inputs.

Trade-off: the schedule is predictable and non-IID. Keep consecutive samples
inside the same lesson and disclose the curriculum structure.

## D8 — maintain two complementary semantic gates

`key_contrast_probe.py` checks single-input branch contrast with actual Racket
outputs, comparing frame interiors so the changed marker cannot fake success.
`lesson_key_gate.py` checks whether visible demonstrations resolve each actual
query frame under a declared rival family. `episode_identifiability_probe.py`
applies the latter to real generated episodes after stripping query outputs.

Rejected: treat a green generator battery, marginal key frequency, or successful
query execution as proof of lesson identifiability. Also rejected: describe the
finite rival family as a universal definition of learnability. Symmetric query
objects can legitimately pass despite an unseen key when all rival outputs agree.

## D9 — keep diagnostic textures separate from training axes

`no_key`, `no_frame`, and `no_object` remain explicit negative fixtures and fail
semantic validation. They are not ordinary texture-domain values and cannot be
combined with geometric overrides. Removed/no-op palette controls raise instead
of pretending to affect sampling.

Rejected: advertise diagnostic invalid examples as normal distribution support
or silently ignore unsupported axes. Callers relying on ignored arguments must
be corrected rather than receiving misleading provenance.

## D10 — preserve audit, solve, and authority boundaries

Only the selected task is patched. Audit targets `40dea3d45f2a` and
`e4cb0224ca42` retain source-bound counterexamples but no edits. The fresh solve
was generated only after F2 was frozen; it declares earlier rule exposure and
uses no private answers or reference source during the solve. Masked correctness
remains unknown.

Rejected: repair audit targets opportunistically, inspect hidden answers to
validate the generator, or call the solve blind. Separate tickets preserve clear
source identity and prevent evidence contamination.

## D11 / T1 — report the shared suite failure rather than hiding it

The final repository run again produced 165 passed / 1 failed. The tiny exported
packet fixture has `solve_episode.py` but no importable `arcpuzzles` package, and
subprocess isolation intentionally removes parent `PYTHONPATH`. The actual packet
solve flow succeeds.

Rejected: alter shared fixture construction from this selected-task patch,
disable subprocess isolation, or claim the repository suite is green. A separate
shared-tooling ticket should copy `repo/src` into the fixture or use a complete
packet fixture.

## D12 — stage-isolate the inherited battery under command caps

The full battery legitimately exceeded the caller window. The documented
fallback runs each of the twelve official stages in a fresh portable runtime and
aggregates their source-bound `result.json` receipts. All twelve passed on the
same generator and authority hashes.

Rejected: infer the remaining stages from a partial monolithic log, lower gate
sample sizes, or call each per-stage native summary a complete battery. The
aggregate explicitly records that each local summary has eleven pending stages
by construction.

## D13 / R8 — make reusable probes self-contained in a clean shell

A clean-room replay applied the packaged patch to the untouched assignment and
ran the documented distribution command with no inherited `PYTHONPATH`. The
probe failed before sampling because dynamically loading the generator required
`puzzle_generators` from `repo/shared/runtime`. The tool now derives the packet
root from `__file__` and prepends only that packet-local runtime path before
loading the selected generator. A subprocess regression removes every
`PYTHON*` variable and uses `python3 -E -s`; the final 256-seed probe was rerun
through that exact isolation and retained in
`checks/round2-distribution-contract-final-v3.json`.

Rejected: document a required caller `PYTHONPATH`, depend on the active virtual
environment, or import the full `arcpuzzles` package merely to find one runtime
module. A reusable review probe should execute from an extracted packet with the
command it advertises, and the narrow runtime bootstrap keeps that contract
visible and testable.
