## Audit 4056ed281704 — bounded semantic check passed; public controls remain inconsistent

**Result:** no semantic failure was found in the bounded check. One real canonical Racket application matched the selected parity formula and refuted two plausible rivals that fit all four supplied canonical examples. A separate, reproducible public-interface issue remains: advertised side and helpful-texture controls are ignored. No task source was changed.

**Source binding:** generators/4056ed281704/generator.py, VERSION 2.0.1, SHA-256 2698786e876862ebb136a10f0038dcfeffd0ce71ef03e2dff7a7102aec5f9095. Exact canonical registration-text SHA-256 541f398019aeb39e6798b679e3d24e7f77bcfe2c45e18721016abc19f9e2a3f9; executed callable-text SHA-256 07e0cfe3b071133c911ab2685d5b40b52054651699ca72c84f4ba97571a2ccef; executed/catalog normalized source hash b837a7dd9877. The public apply tool hashes its wrapped callable in rule_text_sha256, so that field is not the raw registration-text hash.

### Actual witness and rival check

The selected call was generate(seed=0, sample_index=0, difficulty=None). It produced a literal 10×6 all-zero input accepted by public normalize_grid and the selected self_check (errors=[]). Input SHA-256: 3ac7aeb0efacb79b3f967c7edfe0f8d687c294db4db474e38c591250eb18d27d.

The actual canonical Racket command exited 0 and returned a valid 10×6 output with SHA-256 b71b97078052fef2cf127d38877746ce9c55f39c6bb5918280ebeba8d7b9409b. It equals the expected fixed lattice: 0 where both zero-based coordinates are odd, and 1 elsewhere. Input-content independence is the task's rule and was not treated as a shortcut defect.

All four supplied canonical pairs are odd squares of sides 5, 7, 9, and 11. Both exploratory rivals fit all four of those complete labeled pairs:

| Rival | Actual result on the 10×6 generated input |
| --- | --- |
| Assume output width equals input height | Produces 10×10 instead of the actual 10×6; 40 excess cells. |
| Force all perimeter cells of the parity lattice to 1 | Same dimensions, but disagrees with Racket on 7 cells, including (row 1, column 5): Racket 0, rival 1. |

The generator's rectangular/even support therefore provides a distinguishing example against these two canonical-fitting assumptions. This is evidence of coverage for those rivals, not a claim about every possible shortcut.

### Confirmed public-interface discrepancy

At the same seed and sample index, both advertised legal overrides side=5 and side=13 return the unchanged 10×6 grid, so neither honors its requested square size. All five declared HELPFUL_TEXTURES— all_zero, random, sparse, blob, structured—also return the identical untextured draw.

AXES and HELPFUL_TEXTURES advertise those controls at generator.py lines 27–39. The actual implementation only dispatches DEGENERATE_TEXTURES, then draws grid_h and grid_w at lines 56–74; it never consumes the side override or helpful texture values. The source explicitly describes independent rectangular dimensions at lines 64–67, while its opening summary/invariants still describe odd squares. The repository specification names dead texture branches as contract warnings (docs/reference/PUZZLE_GENERATOR_SPEC.md lines 264–269).

Recommended follow-up: align advertised axes, textures, summary, and invariants with the intended all-zero rectangular sampler, or implement the promised controls where semantically appropriate. This audit does not propose adding decorated input content merely to satisfy obsolete metadata. Diagnostic degenerate-texture rejection was not reported as a defect.

### Exact command and bounded scope

The actual command, from the packet root /tmp/arc_review_121953_mount, was:

    /tmp/arc_review_121953_mount/WORK/.venv/bin/python review.py run /tmp/arc_review_121953_mount/WORK/.venv/bin/python -m arcpuzzles apply 4056ed281704 --input ../checks/audit/4056ed281704/input.json --out ../checks/audit/4056ed281704/racket.json

The effective payload cwd was /tmp/arc_review_121953_mount/WORK/repo. Exit code: 0. The main reviewer ran this single application in the serialized Racket window; the independent comparison started no additional runtime.

Scope: one default draw, one determinism repeat, two legal side controls, five helpful-texture controls, four canonical labeled pairs, two described rivals, and one actual Racket input. Global Python RNG state was preserved. No exhaustive seed/difficulty battery was run, no unavailable-file claim was made, and approval/training-admission state was not changed.

Evidence under checks/audit/4056ed281704/: probe.py, probe-command.json, probe.stdout.txt, probe.json, input.json, canonical-program.rkt, python_formula_output.json, rival_outputs.json, racket.json, apply-command.receipt.json, apply-command.log, and comparison.json. probe.json records the pre-Racket stage; comparison.json is the final source-bound outcome.
