# Working notes: 25d47dde0246

## 2026-10-24 semantic teaching repair

- **Observed defect:** the retained seed-11 default lesson used three single-component demonstrations, so the canonical-fitting shortcut “crop only the largest nonzero component” survived and changed the disconnected query.
- **Decision:** keep the canonical joint-nonzero bounding-box rule unchanged and declare `largest_component_only` as the named rival/shortcut.
- **Teaching schedule:** use a four-sample cycle `ordinary_mix, joint_bbox_witness, canonical_support, joint_bbox_witness`. Any three consecutive demonstrations contain a disconnected witness; any query rotation of a four-pair lesson leaves at least one witness; every period also contains an exact public/canonical-profile input.
- **Override contract:** an explicit `scene_profile` always wins over the default schedule.
- **Certificate contract:** `lesson_identifiable` validates demonstration inputs and labels, validates the query input, and rejects lessons that do not refute the declared rival.
- **Portability repair:** task tests now use `reviewer_support.find_root`, `canonical_path`, and `load_selected_generator` instead of assuming a fixed checkout depth.
- **Authority:** `RULE_HASH` remains `88475e062f41`; no canonical or Racket source changed.
- **Verification:** staged tests 30/30; lint, self-check, rule smoke, profile floor, diversity, and fixed-seed schedule enumeration all pass. Five authored inputs also matched canonical Racket exactly.
- **Bounded limits:** adversarial coverage is finite and addresses the declared largest-component rival, schedule/query rotations, explicit overrides, and certificate rejection paths; undeclared rival families remain outside this repair.
- **Next useful action:** maintainer replay of the packaged source-bound evidence before any approval or training admission.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-b1e0b02aa4b00790:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `f30282ade2fc2044ed4a95a30094ab31653da14f2e5c086994ff0a5b2232b7b2`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source-bound repair explicitly addresses this finding; focused checks and Racket parity are reviewer-reported, not a new owner battery. Current task notes and retained integration record specify scope and finite limitations.

### Assessment or prior finding

## 25d47dde0246

**Reproduced possible shortcut in an exact default lesson window.** Generator hash `f30282ade2fc2044ed4a95a30094ab31653da14f2e5c086994ff0a5b2232b7b2`; executed rule hash `88475e062f41`.

At seed `11`, consecutive default sample indices `0..3` produce profiles `touches_horizontal_edge`, `touches_horizontal_edge`, `touches_horizontal_edge`, then `disconnected_objects`. Treating the first three as demonstrations and the fourth as query, the rival **“crop to the tight bounding box of only the largest 4-connected nonzero component”** matches all three official demo outputs because each has one component, but changes the query: the authority's joint crop is `3×8`, while the rival returns `3×3`. All four inputs pass `self_check`, so this is inside the documented ordinary generator domain.

Evidence: `checks/audit/25d47dde0246/input.json`, `rival.json`, `racket.json`, and `finding.json`; the authoritative match vector is `[true,true,true,false]`. The focused semantic gate in `semantic-check/` independently fails because the generator declares no strict/witness/lesson contract. This is a concrete lesson-assembly risk, not a claim that every production scheduler will select seed 11. No source was changed for this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-b1e0b02aa4b00790-v0001/audit_assets.json), manifest SHA-256 `108540c88ffaacce796953686b89d8d36b4c218ac64827b3cb0abaf31d095e8a`.
<!-- arcpuzzles-current-audit-assessment:end -->

## 2026-10-25 native parametric family

- **Base decision:** retain the existing production generator and exact canonical Racket program unchanged; the prior joint-bounding-box teaching repair remains authoritative.
- **Family:** `followup=canonical|boundary_fill`. The alternative first performs the canonical crop, then recolors only zero components touching the newly exposed crop boundary cyan (`8`), preserving enclosed zero holes.
- **Sequential dependency:** Stage B reads boundary status on the cropped intermediate. The protected wrong-order counterfactual fills original-grid boundary zeros before cropping; that expands the crop and changes the final result.
- **Teaching/export contract:** matched inputs, 2–6 demonstrations, four distinct private queries, stable query prefixes, and one-query public projections with no hidden settings, programs, answers, future inputs, or total-count hint.
- **Bounded evidence:** 42 focused tests; 32 seeds; 8,320 labeled pairs; 320 causal separations; 640 plausible-rival rejections; 40 protected family labels plus 20 protected counterfactual labels; substantive 30×30 coverage; 16 public views and 24 private-field invariance mutations. No findings in that finite scope.
- **Status:** reviewer-ready prototype only. Exact-source owner integration, native qualification/acceptance, variant approval, and any training admission remain pending.
- **Next useful action:** integrate these exact source bytes and rerun owner qualification/acceptance without substituting editable receipts for execution.
