## 733d5c4a475a

**Reproduced defect: the existing unresolved axis-aligned-vector coverage gap remains.**
The findings-only target is unchanged at generator SHA-256
`e7799d8f26d57bd514a3c2869706a22d38e8aad63c4ee3d9f6a1192461c2aacb`.
Its current `evidence/review_index.json` already contains two unresolved audits
of this defect on the same source. This audit independently reproduced it with
a bounded check rather than repeating their 3,000-draw census.

All **3 usable labeled canonical pairs**, **18 generated inputs** (seeds 0–5,
sample index 0, in each of easy, medium, and hard), and **2 handmade inputs**
were executed through public `arcpuzzles apply`. All 23 were accepted by both
the local and public generator-domain checks; all reference outputs agreed
with the Python translation mirror, and all 3 canonical outputs matched their
recorded labels. The executed rule hash was `78b2753024a2`, with callable text
SHA-256 `85c2cdf0c542214266a89f29f1ccc7e932bc2b91ccaf74ed356e726dd4504618`.

The generated vectors were diagonal in **18/18** draws. Source inspection
establishes the absence of horizontal and vertical cases beyond this small
sample: `dr_options` starts at 1 and `dc_options` explicitly excludes 0. A
plausible rival that performs the correct copy for diagonal vectors but only
erases markers for axis-aligned vectors fits **3/3 canonical pairs and 18/18
generated pairs**. It fails on both lawful witnesses:

- **Vertical witness:** a 6×6 grid with markers `(0,4)` and `(3,4)`, and a
  color-4 shape at `(1,1)`, `(1,2)`, `(2,1)`. The reference additionally colors
  `(4,1)`, `(4,2)`, `(5,1)` with 4; the rival leaves those three cells black.
  Input SHA-256: `b568f47b5c9cc47ddabf584358f79cb84babe66f2ed35a2893f4cca804147a7d`.
- **Horizontal witness:** a 6×7 grid with markers `(0,0)` and `(0,3)`, and a
  color-4 shape at `(2,1)`, `(2,2)`, `(3,1)`. The reference additionally colors
  `(2,4)`, `(2,5)`, `(3,4)` with 4. Input SHA-256:
  `0e21aeeedb684f25986db3bd73cd8d6a02004db3782d88a2453a27936d2989f7`.

Coordinates are zero-based. These witnesses cannot be emitted by the ordinary
sampler, although its validator and documented nonzero-vector domain accept
them. Exact inputs, reference outputs, rival predictions, and differing cells
are retained in `checks/audit/733d5c4a475a/cases.json` (indices 21 and 22), with
the authoritative receipt in `checks/audit/733d5c4a475a/racket.json`.

**Additional observed canonical coverage restriction:** every ordinary draw
also satisfies `abs(dc) <= 2`, while the labeled canonical test pair has vector
`(2,-3)`. Its T tetromino, normalized to
`[(0,1),(1,0),(1,1),(1,2)]`, is absent from the four-entry `_SHAPES` bank.
This canonical input passes `self_check` and the reference rule; it cannot be
sampled by the present generator. A rival that suppresses copies for
`abs(dc)>2` matches all 18 generated pairs but fails the canonical test at
`(4,0)` (reference 4, rival 0). It therefore fits only **2/3 canonical pairs**
and is a partial lesson competitor, not an all-canonical shortcut.

**Focused public lint also fails:**
`arcpuzzles check 733d5c4a475a --stage lint --phase audit` reports the missing
required `RULE_HASH` constant (1 error, 4 axis-contract warnings). The outer
CLI exited 1; the retained native lint stage exited 2 without timing out.
Evidence: `checks/audit/733d5c4a475a/lint/result.json` and
`checks/audit/733d5c4a475a/lint/checks/733d5c4a475a_audit_lint.log`.

**Suggested repair:** add ordinary horizontal and vertical vector branches,
include explicit lesson witnesses that rule out the diagonal-only rival, and
cover the canonical test's displacement and T shape. Reverify before pinning
the selected authority hash. Keep the prior audits unresolved until an actual
repair addresses their source-bound findings.

**Limits:** this was a focused coverage audit, not a whole battery or an
exhaustive check of overrides, clipping, collisions, or multicolor objects. No
incorrect authoritative label was observed among the 23 checked inputs. No
audit-target source, authority, approval, notes, or status was changed. The
exact executable probe, commands, exit statuses, source/rule bindings, and
summary are in `checks/audit/733d5c4a475a/`; `verification_commands.json` records
the outer wrapper invocations, and `commands.json` records the public apply
invocation.
