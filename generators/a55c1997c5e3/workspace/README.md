# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Path curriculum probe

`probe_path_curriculum.py` reads the selected generator through the public
`reviewer_support` helper. It discovers every `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS` binding, preserves same-name callable aliases, checks all
labeled canonical pairs, and samples one explicit representative of each current
profile. It also includes the minimal three-node left/up tie and reconstructs
the previous four-demo endpoint ambiguity from the existing profile controls.

Run from the repository root, using a fresh evidence directory:

```bash
python3 generators/a55c1997c5e3/workspace/probe_path_curriculum.py prepare \
  --out ../checks/path-curriculum-final
python3 ../run_with_racket.py python3 \
  generators/a55c1997c5e3/workspace/probe_path_curriculum.py apply \
  --out ../checks/path-curriculum-final
python3 generators/a55c1997c5e3/workspace/probe_path_curriculum.py score \
  --out ../checks/path-curriculum-final
```

The packet wrapper supplies Racket and the public CLI environment. In an
installed checkout with Racket already on `PATH`, invoke the `apply` stage
directly. The preparation defaults to seed 0, medium difficulty, and exact
16-by-18 dimensions; `--seed`, `--difficulty`, `--grid-h`, and `--grid-w` can
select another representative population.

The three stages retain inputs, alternative predictions, the public `arcpuzzles
apply` receipt, and scored findings separately. Preparation never labels inputs
with a Python mirror. Apply and score reject changes to the selected generator
after preparation, and evidence files are never overwritten. Scoring validates
canonical-fit declarations and generated counterexamples, then evaluates every
declared cyclic start and every held-out position using the labeled profile
representatives. Nonzero exit means a reference mismatch, unsupported shortcut,
hook warning, or ambiguous query occurred.

These symbolic windows deliberately reuse profile representatives. Their
rotation count is not a count of independent production lessons, and they do not
exercise duplicate rejection or accepted sample indices. Run the public
`lesson-census` separately for production generation evidence. A passing finite
rival census does not establish universal identifiability or training admission.
