# Component threshold/connectivity prototype

**Status: six component settings accepted through the source-bound adapter.**
The approved v3 production `generator.py`, canonical rule and production approval
remain unchanged. Training admission and learning benefit remain unestablished.
The retained standalone authoring exporter below keeps its original proposed
status; current acceptance is [accepted.json](../../parametric/accepted.json),
exposed by `arcpuzzles parametric status 57bafcdde8c3`.
The separate public-evaluation-inspired proposal remains unaccepted, documented in
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

`adapter.py` reuses the exact programs, sampler and observer in `components.py`.
It accepts seeds 0 through 2^63−1, 2–8 demonstrations and 1–8 queries independently.
It selects the same inputs for every setting at the same seed/counts. Teaching
inputs jointly distinguish all six settings and reject five extra production
shortcuts under every setting. Each setting has positive recoloring evidence for
both sampled foreground colors (0/3) and backgrounds (1/7). These finite checks
do not guarantee uniqueness among unrestricted rules.

Queries use separate input streams and independent palette choices. Four-query
episodes contain 13×13, 16×20, 24×24 and 30×30 fields, with equally sized answers.
The last three profiles extend the production distribution; they are not evidence
that the unchanged canonical sampler produces larger fields. Query prefixes do
not depend on demonstration counts. All episode inputs must be distinct.

Owner execution covered 24 focused tests, 264 protected Racket evaluations for
qualification, another 264 for fresh acceptance, and 828 at all four count
corners for every setting. A bounded Python-only check covered 171 episodes.
The exact evidence, including the earlier color-only teaching counterexample,
lives in [owner-parametric-promotion](../../evidence/owner-parametric-promotion/).
The counterexample concerns an intermediate adapter, not a new production defect.

Use the accepted route from the repository root:

```bash
arcpuzzles export --approved --id 57bafcdde8c3 --accepted-parameters \
  --style episodes --count 6 --seed 17 --train 3 --test 4 \
  --out var/datasets/accepted-components
arcpuzzles inspect-export var/datasets/accepted-components --sizes
```

`promotion.json` and the separate acceptance record bind the six settings and
their executable closure. Drift revokes usable acceptance. The separate legend
proposal and original hidden-answer uncertainty are outside this acceptance.
