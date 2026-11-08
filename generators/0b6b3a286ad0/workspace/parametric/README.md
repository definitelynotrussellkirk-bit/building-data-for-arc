# One or two key-to-value lookups

This task-local candidate adds the episode-fixed parameter `lookup_depth` to
`0b6b3a286ad0`. It leaves production generator version 4.0.0 and its selected
canonical rule unchanged. The default program is the exact 1,931-byte selected
source in `canonical.rkt`; depth 2 composes a second lookup with the first.
Qualification is reviewer evidence. Owner acceptance of the integrated source
and any downstream training decision remain separate.

## Rule and dependency

Every input has five vertical panels, separated by full-height color-9 columns:
`KEY1 | VALUE1 | KEY2 | VALUE2 | QUERY`. Crop the four library panels to their
nonzero, non-divider content. A lookup searches a state for KEY1 in its exact
orientation and colors, treating KEY1's zero cells as wildcards. A match selects
VALUE1; absence selects VALUE2. The grammar also supplies an exact KEY2 whenever
KEY1 is absent, although the executable canonical else branch does not require it.

| Setting | Transformation |
| --- | --- |
| `{"lookup_depth": 1}` | Look up QUERY and return the selected value crop. |
| `{"lookup_depth": 2}` | Look up QUERY, use that selected value crop as the next state, look it up, and return the resulting value crop. |

Step A selects a value from the external query. The intermediate is that selected
**grid**, not just a fixed instruction to swap the answer. Step B searches that
grid for KEY1. A swap-map example, an identity-map example, and a constant-map
example make composition distinguishable from one lookup, unconditional
inversion, fixed intermediate choices, and constant outputs. The causal witness
uses a swap-map input: A selects VALUE1, whose contents select VALUE2. Forcing
VALUE2 as the intermediate instead makes B return VALUE1. The native witness
helper independently executes both final answers; its intermediate description
remains an authored interpretation of the code.

This is sequential lookup composition, not a moving-object simulation. It is
possible to compute both map branches in advance; the branch actually consumed
by B still depends on A's input-dependent selection.

## Supported grammar and counts

- Exact integer seeds: `0..2**63-1`; booleans are rejected.
- Exact settings: one key, `lookup_depth`, with integer value 1 or 2.
- Demonstrations: **3..6**, independently of **1..4** queries. Defaults are 3 and 4.
- Rectangular list grids, each dimension 1..30, exact integer colors 0..9.
- Generated keys are connected asymmetric 3×3 masks with distinct colors; value
  panels are four columns wide, have different heights, and share a third color.
- A state contains one intended key type, possibly repeated. Other-key motifs
  are rotations, reflections, one-cell omissions, or wrong-color decoys.
  Filled wildcard cells distinguish exact-background matching from the rule.

Three demonstrations are a meaningful minimum here. With just two examples
covering both initial branches, unchanged results allow the one-lookup rule,
two flipped results allow unconditional inversion, and one flipped result allows
a constant output. The three core demonstrations use initial branches 1,2,2 and
depth-2 results 2,2,1. They all have shape 15×26 so overall dimensions cannot
alone select the answer in those teaching examples. This minimum is declared in
the promotion contract; the candidate does not claim two-demo support.

| Query profile | Input shape | Value heights | Initial key | Successor keys of values 1 and 2 |
| --- | --- | --- | --- | --- |
| Compact identity | 8×25 | 4, 7 | 1 | 1, 2 |
| Constant-to-2 | 22×29 | 21, 16 | 2 | 2, 2 |
| Large swap | 30×30 | 30, 27 | 1 | 2, 1 |
| Reverse swap | 26×28 | 25, 21 | 2 | 2, 1 |

Their order is independently permuted by seed and is shared across settings.
The same seed yields the same input grids for both depths. Per-example local
random streams keep demo and query prefixes unchanged when counts change, do
not alter Python's global random state, and return fresh mutable grids.

The 30×30 case has dense value crops spanning 30 and 27 rows, motif content
reaching the query's first and last rows and last column, and a tall output. It
is substantive boundary stress rather than an empty padded canvas. Layouts are
always the same five vertical panels; only the key masks use dihedral diversity.
Geometry and transition roles come from a finite declared profile set.

## Teaching audit and repaired shortcuts

`rivals.py` supplies independent Python and Racket alternatives. `audit.py`
checks count boundaries and matched inputs, then evaluates protected-Racket
programs against visible demonstrations before considering queries. The bank
includes constants, wrong depth, inversion, fixed or wrong intermediates, wrong
orientation, strict zeros, colorblind and missing-cell matches, mere color
presence, value-size shortcuts, and key-color frequency shortcuts. Depth-2
variants apply faulty predicates to either hop or both. A finite rival bank is
not a proof of unique inference among arbitrary programs.

Self-review found and repaired two concrete sampling weaknesses:

1. The first query was always the compact identity case. A separate seeded
   permutation now varies its size, first branch, and whether depth changes its
   answer, without changing prefix stability.
2. A single true key amid many decoys made the correct key color consistently
   rarer. Demo 1's query now repeats the true key five times, and demo 0's VALUE1
   repeats it twice. Both lookup stages therefore have teaching examples where
   the true key color is rarer and where it is more frequent. Dedicated tests
   were observed failing before these changes and passing afterwards.

The earlier shortcut probe and receipts are retained under
`checks/0b6b3a286ad0/` in the review return. Current evidence is copied into
`evidence/current/` before the native source inventory is built. The task tests
also cover manual composition, canonical byte identity, exact numeric types,
prefixes, fresh grids, wildcard semantics, and meaningful boundary content.

## Reproduce with the packet interpreter

Run these from the outer packet folder. Payloads execute in `WORK/repo`, so
`../checks` means `WORK/checks`. Use a new output path for a new source version.

```bash
WORK/.venv/bin/python review.py task-tests 0b6b3a286ad0 \
  --phase after --out ../checks/0b6b3a286ad0/task-tests-replay
WORK/.venv/bin/python review.py run python3 \
  generators/0b6b3a286ad0/workspace/parametric/audit.py \
  --out ../checks/0b6b3a286ad0/self-review-replay.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  0b6b3a286ad0 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/0b6b3a286ad0/qualification-replay --summary
```

The existing manifest binds the native adapter, every prototype source/resource,
explicit tests, current evidence, production generator, and selected rule.
After edits, regenerate the native manifest with the new evidence and refresh
qualification. Do not reuse receipts across source changes.

## Single-query public projection for reviewers

`export_qualified.py` is a reusable task-local projection and verification tool.
It consumes a current native qualification and its sibling execution receipt,
uses the packet's exact public serializer, and writes one hash-named public
challenge for each of an episode's four private queries. Each public challenge
contains only the same visible demonstrations and **one** query input. It has
no future-query list, turn index, total count, answer, parameter, seed, or program.
Private ordering and answers remain in `private/` with the source receipts.

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/0b6b3a286ad0/workspace/parametric/export_qualified.py export \
  --qualification ../checks/0b6b3a286ad0/qualification/qualification.json \
  --out ../checks/0b6b3a286ad0/sequential-public-replay
WORK/.venv/bin/python review.py run python3 \
  generators/0b6b3a286ad0/workspace/parametric/export_qualified.py verify \
  --bundle ../checks/0b6b3a286ad0/sequential-public-replay
```

A consumer chooses views using the private ordering and releases the next query
after the preceding answer. The tool prepares and checks those views; it does
not implement an interactive turn controller. The first view supports stopping
after one query without a public cue that more queries exist.

It refuses an existing destination, duplicate visible payloads, source or receipt
drift, invalid grids, added public fields, missing or extra files, and symlinks.
It writes through a staged directory and checks again before publication.
Twenty-five focused tests cover the serialization boundary and rejection paths.
Verification checks serialized bytes and source bindings; it does not re-execute
Racket, authenticate maliciously forged receipts, grant owner acceptance, or
activate training. At each turn give the model only the selected public file;
keep the directory listing, future public files, and all private files hidden.
