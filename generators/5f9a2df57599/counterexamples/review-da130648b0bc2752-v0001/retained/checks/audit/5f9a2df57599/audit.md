## 5f9a2df57599

**A3 — Suspected shortcut: a 4×4 component-size rule bypasses every gray-wall test on the checked generalized distribution. No reproduced generator/reference semantic defect.**

Audited the assigned live source without editing it. Generator SHA-256 is `f641de5c1ef15a254272dce952d0951d29a2be87c6d88873638543dcac41a51e`; canonical normalized rule hash is `5b73d3931a5c`; exact rule-text SHA-256 from public execution is `41c8ea7a1baa41ef98510fb1a7fbba816e25d3cdc863322eb327da4473279b03`.

### Checked evidence and result

Read `repo/AGENTS.md`, README/placement guide, target source, summary, notes, focused test source, both retained target evidence files, and the exact canonical rule and all four public examples. The prior retained audit already refuted an unrestricted enclosed-component shortcut; this finding is a different size-limited rival.

The rival in `checks/audit/5f9a2df57599/probe.py` segments orthogonal zero components and fills one when its bounding box has at most four rows and four columns, does not touch the top/bottom boundary, and is not the multi-row column-zero exclusion. It never inspects any of the four gray-wall conditions.

A census using seeds **0..99**, sample index **17*seed+1**, each of **easy/medium/hard**, no overrides, gives **300 calls, zero generation or validator failures**. There are **267 generalized draws** and **33 public-profile replays**. The rival agrees with the Python mirror on **267/267 generalized draws** and **291/300 overall**. These census comparisons are explicitly mirror-based, not independent Racket labels; all nine rival failures remain in `census.json`.

Fresh public `apply` labels check **65 applications over 65 unique inputs**, with **zero execution errors and 65/65 exact mirror matches**:

- **60 generalized scenes:** every one of the ten general profiles in each easy/medium/hard band, seeds **700 and 701**, indices **11901 and 11918**, forced `scene_profile`. Rival matches the official output **60/60**.
- **Four immutable public scenes:** seed **700**, index **11901**, no difficulty, forced `public_1..public_4`. Rival matches **3/4**; `public_2` refutes it. This generated failure is retained separately in `generated_refutation.json`, including its exact input, official output, rival output, hashes and sampler coordinates. It is also `parity_racket.json` result **61** (zero-based).
- **One compact hand-built admitted scene**, described below. Its official output refutes the rival while matching the mirror.

See `summary.json`, `comparisons.json`, `parity_metadata.json`, and `parity_racket.json` for exact counts, inputs and outputs. The official generalized set is a small targeted parity probe, not a full battery or a claim of universal coverage.

### Compact concrete counterexample

`counterexample.json` retains a minimal-dimension validator-accepted witness. It is an 8×8 gray grid with zeros at **(1,1), (1,2), (2,1), (3,2)**, using zero-based coordinates:

```text
55555555
50055555
50555555
55055555
55555555
55555555
55555555
55555555
```

`self_check(input)` returns **[]** and `observe_overrides(input)` reports **rect_n1**. The three-cell L has bounding box rows 1..2, columns 1..2. Its required bottom side is row 3, columns 1..2, namely **[5,0]**, so it must stay black. The isolated zero at (3,2) has all four walls and turns yellow. Official output is precisely the input with **(3,2)=4**. The rival additionally paints **(1,1), (1,2), (2,1)** yellow. Full rival/official arrays are in `counterexample.json` and the original public receipt is `compact_racket.json`.

**Sampler status:** this witness is hand-built, so seed/index/overrides are null. It passes the target validator and satisfies the documented 8..30 geometry/color/profile domain. The current sampler **cannot emit this exact 8×8 input**: general scenes have each dimension at least 12 and none of the four public inputs is 8×8. The generated `public_2` witness above separately proves that the rival is not universally correct on sampler outputs.

### Interpretation and limit

The source constructs intended eligible rooms with bounding boxes at most 4×4. In the checked generalized outputs the rejected nonexception components fall outside this size/boundary rule. Therefore a learner can achieve very high accuracy on these probes without learning complete bounding-box side quantification. The compact admitted scene exposes the missing contrast: a small, enclosed zero region can fail one complete-side test and remain black.

This is a **suspected distribution shortcut**, not a proved labeling defect or an assertion that the rival works for every seed. Public-profile sampling does provide a counterexample, and the retained audit demonstrates that broader rivals can fail. Owner investigation could add small rejected irregular regions and larger eligible regions so size alone cannot substitute for wall testing. No source fix, approval change, package operation, private solve, or full battery was performed.

### Reproduction

Run from `/workspace/scratch/5d8b66323a0c/work`:

```sh
python3 checks/audit/5f9a2df57599/probe.py
python3 run_with_racket.py python3 -m arcpuzzles apply 5f9a2df57599 --input ../checks/audit/5f9a2df57599/compact_input.json --out ../checks/audit/5f9a2df57599/compact_racket.json
python3 run_with_racket.py python3 -m arcpuzzles apply 5f9a2df57599 --input ../checks/audit/5f9a2df57599/parity_input.json --out ../checks/audit/5f9a2df57599/parity_racket.json
python3 checks/audit/5f9a2df57599/finalize.py
```

The wrapper executes payloads in `repo/`; the `../checks/...` paths are intentional. Exact command arrays, packet-root working directory, success statuses and retained evidence paths are in `commands.json`. Receipts also contain actual payload cwd/command and input/output hashes. Output paths may need to be renamed for a replay because public `apply` preserves existing evidence.
