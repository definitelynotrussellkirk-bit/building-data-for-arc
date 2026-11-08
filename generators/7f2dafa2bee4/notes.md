# Working notes: 7f2dafa2bee4

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 review repair

### D1. Canonical rule and authority

The unchanged rule segments nonzero cells into same-color 4-connected objects, connects distinct objects that touch across a side, and recolors each object by contact-graph degree: 0→1, 1→2, 2→3, and 3+→4. The exact canonical Racket source remains the default rule in the parametric prototype.

### D2. Close the degree-zero lesson hole

The retained audit contained a legal three-demo lesson with no isolated object while the query contained one. A lesson-only competitor that maps degree zero to color 2 therefore fit every demonstration and changed the query. Canonical examples already refute this heuristic, so `CANONICAL_SHORTCUTS` remains empty. Version 1.3.0 uses a period-three profile schedule with degree-zero evidence in two residues. Exhaustive four-pair windows and all held-out-query rotations now retain a degree-zero witness, and the declared `degree_zero_as_two` rival is rejected from demonstrations alone.

### D3. Pixel-derived validation and semantic declarations

`self_check` validates the generated grid and exact canonical label from pixels. `rule_mirror` independently computes object degrees. `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `WITNESS_RIVALS`, and `lesson_identifiable` expose the bounded teaching contract directly to future audits.

### D4. Proposed episode-level contact parameter

`workspace/parametric/` adds one bounded hidden setting, `contact_mode`:

- `cardinal`: exact canonical shared-side contact;
- `eight_neighbor`: shared-side or shared-corner contact.

For a fixed seed, both settings receive byte-identical inputs. Every demonstration contains a corner-only distinction, so the alternate declared setting is eliminated by demonstration fit. The generator supports 2–6 demonstrations and 1–4 distinct queries; query projection is count-independent, and the first query is a substantive 30×30 scene with separated boundary, center, and far-corner motifs.

The promotion adapter and manifest are authoring interfaces only. The prototype's public projection emits demonstrations plus one query input, strips settings/rule/query answer, and computes its public ID from exactly those visible canonical bytes.

### D5. Verification boundary

Protected Racket execution matched the generated Python labels for both parameter settings over retained multi-seed episodes. These checks establish bounded source/label parity and declared-setting identifiability; they do not prove universal uniqueness against arbitrary programs. No acceptance or training admission is implied by this review return.
