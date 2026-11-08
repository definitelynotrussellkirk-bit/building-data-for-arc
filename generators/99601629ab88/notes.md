# Working notes: 99601629ab88

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 reviewer portability repair

The retained task test derived `ROOT` with a fixed `Path(__file__).parents[1]`,
which resolves inside the task home in the staged portable runtime and failed
before any semantic checks. It now binds the nearest supplied library with
`reviewer_support.find_root`, reads the canonical ledger through
`canonical_path`/`canonical_pairs`, and derives base-solution paths from that
ledger's data root.

Once the preflight failure was removed, `test_source_sync` exposed a second
false negative: canonical source is pretty-printed while both base records carry
the exact same Racket tokens compacted onto one line. Their whitespace-normalized
SHA-256 is identical (`c856d06245d41405f852c5680d714171a56f9d11e3b1e712fe8f5687e6efd148`).
The test now compares normalized Racket text, matching the generator's existing
`RULE_HASH` contract. No generator or canonical data changed. Staged task tests:
7 passed.

## 2026-10-24 native parametric handoff

Built a source-bound two-setting family under `workspace/parametric/` without
changing the production generator or canonical rule. `mirror_left_right` is the
exact canonical program. `largest_block_to_top_left` first recovers physical row
and column band sizes from the divider lattice, identifies the unique largest
block's corner, and then chooses the vertical/horizontal reorientation that moves
that corner to output top-left. The second step therefore consumes an
input-derived intermediate rather than selecting a fixed transform.

The sampler supports 2–6 prefix-stable demonstrations and 1–4 prefix-stable
queries, keeps inputs identical across settings, covers all four corner branches,
and includes a dense 30×30 query. A finite minimum-lesson audit tested ten
plausible fixed/partial/color/parity rivals on seeds 0 and 17 with no rival that
fit the two demonstrations and changed a query. This is a bounded certificate,
not a universal uniqueness claim.

Native qualification retained 4 jobs and 40 protected-Racket evaluations. The
counterfactual witness forces `bottom_left` in place of the qualified
`top_right` intermediate and changes the final output; independent replay passed.
Reviewer status is ready, but exact-source owner integration, fresh live-byte
qualification, owner acceptance, and any training admission remain pending.
