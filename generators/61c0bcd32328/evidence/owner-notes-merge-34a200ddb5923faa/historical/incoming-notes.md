# Working notes: 61c0bcd32328

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/61c0bcd32328/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current repair

The selected generator remains the canonical clockwise corner-copy task. Version
`2.1.0` changes only the general-scene sampler: corner objects may now use the
one-cell shape as well as larger shapes. The previous `_SHAPES[1:]` choice made
singleton corner components unreachable even though the rule copies them, so an
`ignore_singleton_corner_components` shortcut was never taught. The retained
seed-0 `easy/single_tl` lesson contains a singleton at `(0,0)`; exact canonical
Racket copies it to `(0,9)`, while that shortcut leaves the grid unchanged.

Current selected-source SHA-256:
`4f45d334880485ba8e7926f352f6f9c919dad53df3a9b868af43703964dff4ec`.
The canonical rule source was not edited. Its exact SHA-256 remains
`0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e`
and its normalized rule hash remains
`e3835c9a174e5fd8b8be9b2c3a7bd754629ce5f5197d6e25d7be704d40d32692`.

## Parametric proposal and reconciled export

`workspace/parametric/` remains an unselected task-local prototype with one
setting, `direction ∈ {clockwise, counterclockwise}`, fixed once per episode.
Clockwise returns the canonical source byte-for-byte; counterclockwise changes
only the corner-to-corner translation. Each retained setting has three
demonstrations and four distinct queries. Exact Racket labels match all 14
stored pairs, every demonstration refutes the opposite direction, all four
queries are setting-sensitive, and public challenge IDs hash only visible bytes.

The verifier now materializes the complete two-setting batch in memory, checks
all visible-payload IDs for duplicates or collisions before creating output
directories, and sorts records by public ID before any program, private, or
public artifact is written. This removes the former dependence on private
setting enumeration and prevents a duplicate batch from leaving a partial
public export. The regression reverses the private setting order while reusing
the retained Racket-backed episodes, and a second regression proves duplicate
visible payloads fail before the first public write.

Prototype SHA-256:
`ff6e6e8f2fdc5cd5ccdec9f57eee5854369b31bcb58952e7e20b898322732854`.
Verifier SHA-256:
`be1b1d50f49c17e214eca6c609f886364bd1f80f52b45676206f92eddb0c4039`.
Focused-test SHA-256:
`745aef7344e52c97002fd7efdb2e0ab969714c49f3fb7664aff0f276d5355c1f`.
The proposal is evidence only: it does not select a variant, approve a source,
or admit training data.

## Verification, limits, and next action

The selected task suite has 20 passing tests. The two focused materializer
regressions pass independently, and the protected-Racket verifier reproduces
both directions, the canonical default, public masking/identity invariants, and
the singleton-corner repair. Evidence is retained under
`checks/reconcile-public-order/`, including
`61c0bcd32328-direction.json`, `task-tests-console.log`, and
`adversarial-materializer-tests.log`.

Earlier bounded coverage remains 192 finite episodes, three count schedules,
both directions, all 12 single-corner profile/band cells within seeds `0..127`,
public masking/ID invariance, and invalid numeric/setting inputs. These checks
are not a proof over all seeds or all rival programs. The next useful maintainer
action is to decide whether the direction parameter is worth selecting and,
separately, assess the source-bound peer API finding recorded in `AUDIT.md`.

<!-- arcpuzzles-current-public-order:start -->
## Current prototype public emission-order follow-up

Resolved in this return. The batch is precomputed and globally validated before
writes, public artifacts are emitted in visible public-ID order, and duplicate
visible payloads abort without creating a public file. No variant or training
approval follows. Original static receipt:
`generators/61c0bcd32328/evidence/parametric-export-inspection-69a7900174b5588a/manifest.json`.
<!-- arcpuzzles-current-public-order:end -->
