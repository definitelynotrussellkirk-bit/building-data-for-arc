# Review — c4f6a0585dbf

Status: **repair verified; parametric extension remains prototype-only and needs maintainer review**.
Source: generator `3.2.0`, SHA-256 `8bd3985cceaa93dc8d74e394e7b3b43166e6eb6741bf54e47a86ee5ede659225`.
Defect → repair: advertised palette aliases produced non-`4` ports that the canonical Racket authority ignored; generation and validation now require literal port/target color `4`, obsolete palette aliases are rejected, and malformed identity-only templates with missing, boundary, excess, or non-port holes are rejected.
Reference rule: unchanged `RULE_HASH = d401b3cd92ff`; no canonical Racket or canonical-example edits.
Focused verification: `37 passed` in `checks/c4f6a0585dbf-focused-suite.log`.
Repair evidence: a lawful control changes on canonical Racket, both declared identity boundaries stay identity, and recolor/alias misuse is rejected (`checks/canonical-repair/c4f6a0585dbf-literal-port-v1/result.json`).
Prototype: `min_visible_ports ∈ {2,3}`, fixed once per episode; each retained episode has 3 demonstrations and 4 distinct queries, with setting `2` byte-for-byte canonical.
Prototype evidence: paired settings share inputs, every demonstration rejects the rival, every query differs, all canonical labels reproduce, and public files use exact visible bytes/full SHA-256 IDs (`checks/parametric/c4f6a0585dbf-min-visible-ports-v2/report.json`).
Adversarial scope: 238 generated grids plus 14 fresh intended and 14 rival Racket labels; numeric, masking, parity, and duplicate-rejection checks found no bounded defect (`checks/parametric/c4f6a0585dbf-adversarial-v1/result.json`).
Supplementary tickets: one pinned audit witness reproduced exactly without changing its disposition; one seeded three-record allocation study produced a bounded 10-record shadow experiment proposal.
Limits: no exhaustive sampler proof, no production parameter API, no variant approval/training admission, and no ARC-GEN/RE-ARC comparison because the seeded packet sample exposed neither source label.
