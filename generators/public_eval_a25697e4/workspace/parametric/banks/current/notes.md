# Working notes: public_eval_a25697e4

## 2026-10-25 current authoring result

The new family is reviewer-ready. Protected authoring preflight passed with
`authoring_preflight_not_owner_qualification`; this is an unapproved creation,
not owner registration, native qualification, acceptance, or training admission.
The immutable `workspace/public-parent.json` binds official parent `a25697e4`.
All three supplied training pairs and both provided test golds were executed
and matched by the general reference rule. No input or answer lookup is used.

### Rule and input-dependent composition

Infer the unique modal background. Group same-color four-connected fragments
attached to the same canvas edge into a socket. A socket's tight rectangle has
a background cutout. After excluding anchors, find the colorblind
four-connected free pieces, each containing exactly two colors. Match one
complete color region of each piece to a socket cutout under a D4 transform
and translation. Validate the whole moved piece against bounds and anchors;
choose a one-to-one assignment with disjoint final pieces. Clear all source
pieces simultaneously before painting destinations.

The fitted transformation supplies a reflection parity. In the default
`reflection_colors="swap"`, exchange a key's two colors exactly when its fit
reverses orientation; rotations preserve colors. The alternative `preserve`
retains both colors for every fit. Thus the geometric placement map is the
input-derived intermediate consumed by the final painting/color stage. Fitting
only the head is insufficient: attached-tail collisions disambiguate symmetric
heads in the originals and generated cores.

Root `reference.rkt` and adjacent `workspace/parametric/canonical.rkt` are
byte-identical, SHA-256
`1cd6941cca619e71eb7d7c4dcc35390792793590350d1e91139a6763ece8a863`.
The default adapter program equals them exactly; normalized rule hash
`3baf4daa1663` matches the root generator's pin. The preserve program has SHA-256
`b7bd4f7e69940aabe7262270910c2fa8a1ffc35faf776723e8552008ad5feae8`.

### Teaching and construction decisions

The supported minimum is two demonstrations, ordinary default three, maximum
six; query count is independently selectable from one through four, with four
as the ordinary target. Two rich cores combine rotational and reflected fits,
same-colored sockets on different edges, shared key/socket colors, equal-area
parts of different shapes, collision disambiguation, and misleading nearest
socket positions. All inputs in an episode are novel and distinct. Independent
streams control settings, demonstration augmentations and queries. Construct
the full bank before slicing, and shuffle the complete query bank before taking
a shorter prefix. Palette bijections and whole-canvas D4 transformations preserve
the geometric rule and fitted reflection parity.

The first palette design admitted a concrete shortcut: at seed17 in preserve
mode, swapping by numeric head/partner color order fit both demos and failed a
query. The repaired second core uses head/tail roles `(5,2)` and `(2,5)`, ensuring
opposite numeric orderings under every palette. The first core retains identical
color roles across opposite reflection parities, rejecting such gates under the
swap setting. The protected six-evaluation counterexample is retained in
`checks/public_eval_a25697e4/color-order-hole-v1/report.json`.

Scalable constructors enlarge sockets, heads and tails. The distinct 30x30 demo
and query contain 195 and 235 foreground cells, including 66 and 75 free-key
cells. Rectangular large profiles contain 159 and 178 foreground cells. Placement
is constructive, with no retry or fallback loop. Independent design templates
were explicitly copied into task-local source; provenance records the subsequent
teaching repair. An initial resource inventory check rejected root reference.rkt
outside the adapter home. The byte-exact adjacent canonical copy fixes that
boundary without changing the reference rule; the failed receipt is retained.

### Current evidence

Paths below are under `checks/public_eval_a25697e4/` in this packet.

- `native-and-audit-v2.xml`: 118 focused tests passed, zero failures or errors.
- `sampler-v2.json`: 96/96 Python sampler requests passed across both settings,
  supported count combinations and 16 seeds; 160 distinct inputs, 64 distinct
  query inputs, and 32 distinct 30x30 inputs. This is structural/sampling
  evidence, not an independent protected-label certificate.
- `teaching-v1/private/audit.json`: 45 executed reference labels (five official,
  forty generated), 104 fits across 24 named rivals plus two settings, 96
  refutations and eight survivors. All 32 survivor/query comparisons agree.
  Fits are frozen from only the minimum two demos before query scoring. The
  ledger records 285 requests, 233 protected evaluations and 52 cache hits.
- `preflight/preflight.json`, `execution.json`, and `original-pairs.json`:
  authoring preflight passed, including all official labels and the minimum
  two-demo/four-query setting checks. This does not constitute owner qualification.
- `causal-observations.json`: four protected evaluations measure two selected
  placement maps and counterfactual maps with only their reflection flags set
  false. The downstream renderer is byte-identical and sources stayed unchanged.
  `causal/witness.json` and `causal/replay.json` retain the two disagreeing cases
  with status `reviewer_replayed`.
- `preview-verify.json`: four episodes and sixteen single-query public views
  verified as a preflight projection. Labels, settings, programs, placement
  maps, source indices and future queries remain controller-private.

### Limits and next action

The validator admits exact rectangular ARC grids up to 30x30 with a unique modal
background, one to four noncorner edge sockets, one two-color key per socket,
and exactly one complete placement assignment. The sampler covers a structured
one/two-socket subset, not every admitted grid. The finite audit does not prove
universal identifiability: `ignore_bounds` remains unrefuted but agrees on every
scored query. Finite geometric checks and causal replay do not prove universal
algorithmic depth or measured training gains. The final read-only source review
found no remaining concrete semantic/count/domain issue after the palette and
resource corrections.

Next, the owner must verify the official parent linkage, register the exact
source/provenance, accept its source review, and run unchanged native
qualification and fresh acceptance. Training remains unadmitted. Keep the
retained failed iterations and exact-source receipts with this handoff.
