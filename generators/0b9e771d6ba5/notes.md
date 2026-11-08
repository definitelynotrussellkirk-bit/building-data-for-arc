# Working notes: 0b9e771d6ba5

## Current native parametric acceptance

The retained prototype is now native-qualified and accepted on its exact current source; see `parametric/accepted.json` and `evidence/parametric-acceptance/`. A thin adapter adds independent 2–6 demonstration and 1–4 query counts, with the normal three-demo/four-query request verified across both settings and seeds 0/17. Original rule/sampler code remains selected within that adapter. Earlier proposed-status descriptions below are superseded only for these exact accepted bytes; canonical audit findings and training admission are separate.

## Current decision — proposed `line_span_policy` extension

Keep the approved production generator and canonical rule unchanged. The task-local prototype in `workspace/parametric/` adds one episode-fixed rule parameter:

- `foreground_only` is the exact canonical/default program (normalized rule hash `654b94529e3a`; full source SHA-256 `654b94529e3a166bdc4e18d5135af93164f69d26e77c671e6abff3ed20618eca`).
- `entire_span` changes only the final line-span paint predicate so original background gaps are filled (full source SHA-256 `e3285e7e301c2f881bb5c25df936f5147eeab8e161521bdd6b3360e13bbbea40`).

Invariant reasoning remains: infer the unique modal background; restore impure foreground-only rectangles; detect complete horizontal, vertical, or diagonal spans; use the same endpoints, colors, and ascending overwrite order. The alternative is meaningful because it changes the bridge substrate rather than geometry or palette.

Retained evidence uses seeds `20261023` and `20261028`, three demonstrations plus four distinct queries per setting, 14 unique lawful `background_gap_stays` inputs, eight observed background colors, 28 Racket rule applications plus two canaries, and exact Racket/Python parity. In both episodes the demonstrations refute the other declared setting; all eight queries also differ. Public challenge names hash only visible bytes.

The prototype remains proposed and task-local. It does not change canonical authority, production approval, or training admission. Pairwise evidence does not prove uniqueness against arbitrary programs.

## Verification limitation

The authored prototype test file passes independently. The unchanged legacy `test_generator_0b9e771d6ba5.py` cannot collect in this rotating packet because it imports `puzzle_generators.per_puzzle.0b9e771d6ba5`, while the packet exposes the selected generator through `reviewer_support.load_selected_generator` and does not include that per-puzzle runtime module. Preserve the diagnostic rather than treating the aggregate as green.

## Next useful action

Before any shared integration, independently replay the evidence writer on the exact returned prototype hash and decide whether the `entire_span` setting merits a separately reviewed parametric API. Do not refresh canonical approval hashes for this proposal.

<!-- arcpuzzles-current-public-order:start -->
## Current prototype public emission-order follow-up

Public filenames match visible bytes, but physical writes still follow private seed/setting order. Preserve exact code/Racket evidence; precompute and sort the batch before writes with one focused regression. No variant or training approval. Static receipt: `generators/0b9e771d6ba5/evidence/parametric-export-inspection-759f39d84b9afb4c/manifest.json`.
<!-- arcpuzzles-current-public-order:end -->

## Portable task-test repair — 2026-10-24

Production `generator.py` and canonical authority remain unchanged.  The legacy
test now resolves its source tree with `reviewer_support.find_root`, loads the
selected generator with `load_selected_generator`, reads canonical rows through
`canonical_path`, and resolves task-bound base authorities from either
`data/base/...` (relocated runtime) or `shared/data/base/...` (source checkout).
This replaces the fixed `Path(__file__).parents[1]` assumption that failed before
pytest in rotating packets.  The earlier verification-limitation paragraph is
superseded by the relocated task-test result retained with this repair.

## Public emission order repair — 2026-10-24

The task-local parametric writer now prepares both episode exports, computes their
visible-byte IDs, sorts the batch by public ID, and only then writes public and
private episode files.  A focused regression records the actual `Path.write_bytes`
order: the previous seed/setting order was `6904…`, `0226…` and failed; the repaired
writer emits `0226…`, `6904…`.  Canonical production code and authority remain
unchanged.

## Assignment-contract hardening — 2026-10-24

The bounded final review found two inherited prototype gaps: counts were any positive pair up to 20, and retained episodes did not guarantee the required maximum-size stress. The sampler now accepts only 2–6 demonstrations and exactly four queries. Its final input is padded with the inferred background to 30×30, then revalidated through the selected production generator; the two policies still disagree and real Racket/Python parity remains exact. Current evidence is `WORK/checks/0b9e771d6ba5-parametric-final-evidence/` (28 rule applications, two canaries, 28/28 mirror matches, both rivals refuted, eight query disagreements).
