# Component threshold/connectivity prototype

**Status: proposed, task-local authoring prototype.** The approved v3 production
`generator.py`, canonical rule and approval records remain unchanged. No owner
qualification, acceptance, training admission or measured learning benefit is
claimed. The separate public-evaluation-inspired proposal is documented in
`LEGEND_TEMPLATES.md` and implemented by `legend_templates.py`/`.rkt`.

## Rule and supported domain

Determine the unique modal background. Find color-preserving non-background
components under the episode's connectivity. Recolor each component of at least
`min_size` cells to cyan (8); leave smaller components and background unchanged.
The two bounded rule parameters are:

| Parameter | Allowed exact integers | Canonical default | Reasoning changed |
|---|---|---|---|
| `min_size` | 2, 3, 4 | 2 | Which component sizes qualify |
| `connectivity` | 4, 8 | 4 | Whether diagonal contact joins same-color cells |

The six Cartesian settings are fixed across every demonstration and query.
Background inference, color-preserving object discovery, size measurement and
selective recoloring remain the same reasoning structure. Default `program()`
returns the canonical `program_solution` byte-for-byte, including whitespace.
Other settings materialize concrete Racket using the included `objects` or
`objects-8` primitive and an explicit threshold; there is no runtime text patch
or hidden parameter lookup in the Racket program.

All sampled inputs are two-color random fields, with a unique modal background
in `{1,7}`, foreground in `{0,3}`, and cyan absent. The grammar is independent of
the rule setting. Each candidate cycle begins with two independently seeded
13×13 draws from the unchanged canonical generator, then 16×20, 20×16, 24×24 and
30×30 fields with 16–31% foreground. These larger fields preserve the dense-field
reasoning pattern but are proposed distribution expansion, not canonical
fidelity claims. A greedy demo selector may skip a candidate that does not
refute a remaining setting. The semantic function supports exact integer grids
up to 30×30 with a unique mode, including multiple foreground colors; sampling
currently uses only the documented two-color subset.

`generate(seed, settings=None, demos=3, queries=4, max_attempts=512)` accepts exact
integer seeds from −2^63 through 2^63−1, 2–8 demos, and 1–8 queries. Explicit
settings must name both declared keys and no others. Booleans, floating-point
integers and invalid counts are rejected. Omitting settings selects one setting
once from an independent deterministic seed stream. Input candidates use their
own per-index streams and do not consume or mutate Python's global RNG.

Demonstrations are selected and fitted against the six settings before query
selection or query-answer checks. Exactly the chosen setting must survive.
Each query has a separate agreement certificate against these demo-fitting
survivors. Every input is distinct across train and test. Count shortfalls,
remaining ambiguity and exhaustion are errors; no query cloning or silent
shortening occurs. The finite certificate does **not** establish identification
against all plausible rules, the canonical generator's full shortcut registry,
or unrestricted programs.

## Reproduce retained evidence

From the extraction's outer directory (the directory containing `review.py`):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B review.py run python3 -B \
  generators/57bafcdde8c3/tests/test_parametric_components.py

PYTHONDONTWRITEBYTECODE=1 python3 -B review.py run python3 -B \
  generators/57bafcdde8c3/workspace/parametric/components.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/parametric/components-example
```

The output directory must be new. For a single alternative episode, use
`--min-size 3 --connectivity 8 --seed 23 --demos 2 --queries 4` and a new `--out`
path. Demo and query counts are independently configurable. These commands use
the included pinned Racket runtime through the packet wrapper. In a normal
checkout use the same payload command with an installed Racket executable;
NumPy/Pillow are the existing runtime dependencies, and tests use standard
library `unittest`.

The CLI runs a live protected Racket bridge. It executes **all six** programs on
every demonstration (errors fail the run), requires the chosen one alone to fit,
and executes it on all requested queries. Python proposals must agree with all
selected-rule Racket labels. This is bounded prototype evidence, not the owner
promotion worker's qualification receipt. `generate()` and the thin adapter
return deterministic Python claims explicitly marked `racket_checked: false`;
the independent promotion worker must re-execute them.

## Public/private export and evidence

`public/<sha256>.json` contains only demonstration input/output pairs and query
inputs, serialized exactly by `reviewer_support.public_challenge_bytes`.
Identifiers come from `public_challenge_id`; public filenames contain no seed,
parameter, episode ordinal or program. The public JSONL batch is sorted by those
visible-byte hashes. Duplicate visible challenges are rejected before creating
the output directory. An existing output root is refused.

`private.json` retains settings, seeds, query outputs, exact Racket text/hash,
source hashes, per-query certificates, runtime identity and actual payload argv.
Its episode-to-public mapping is private. `manifest.json` binds serialized file
hashes and states that the serializer itself does not execute Racket. It is
private/controller material; give only `public/` or `public.jsonl` to a solver.
Changing private metadata or a query answer cannot change the public filename,
order or bytes. The regression exercises the actual writer after a live Racket
label check, then mutates private fields and checks that property.

The retained batch contains six settings × two seeds × three demonstrations and
four queries: 12 episodes, 84 selected-rule pairs, 48 query certificates, and
216 finite-rival demonstration executions plus 48 query executions. Exact
source bindings and run results are in the evidence, not acceptance authority.
The retained seeds are bounded examples, not a census. Larger counts and other
seeds may exhaust the bounded sampler. Tests also check color-preserving contact,
size boundaries, invalid types, no global RNG mutation, exact default authority,
input distinctness, count independence and explicit exhaustion.

## Promotion contract

`adapter.py` forwards to this implementation. `promotion.json` declares the six
settings, canonical default, count bounds and prototype resource. It is prepared
for owner review under `docs/parametric-promotion.md`. The owner must update the
prototype inventory and perform fresh qualification and explicit exact-source
acceptance separately. No acceptance files or approval hashes are created here.
