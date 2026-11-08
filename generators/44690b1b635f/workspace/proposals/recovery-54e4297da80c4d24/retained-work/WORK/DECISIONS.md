# Decisions for 44690b1b635f

## D1 — Preserve the canonical rule

**Prior choice:** Four-neighbor BFS from the singleton marker with parity color
fill. **New choice:** unchanged. **Reason:** the retained audit found no label
defect, and an independent Python oracle matched the selected rule. **Failure
mode avoided:** changing Racket authority to fix a distribution problem would
create a new task rather than repair this generator.

## D2 — Add one procedural profile rather than replace anchors

**Alternatives:** remove fixed profiles; randomly flip arbitrary walls; add a
bounded procedural grammar. **Choice:** retain all 16 current profiles and add
`procedural_maze`. **Reason:** public anchors and targeted semantic lessons stay
available while topology support grows. **Failure modes:** arbitrary wall flips
can create disconnected noise, cycles, or trivial scenes; deleting anchors can
lose exact canonical-profile support.

## D3 — Use a perfect-maze grammar

Every odd/odd room is open, DFS opens one connector per spanning-tree edge, the
perimeter and even/even cells remain walls, and the validator independently
checks connectivity and acyclicity. This makes generation and recognition
source-bound. **Limit:** perfect mazes do not cover loops, multiple components,
or open rooms; the retained fixed profiles continue to teach those cases.

## D4 — Keep uniform profile selection

`SCENE_PROFILES` now has 17 unique entries, so ordinary sampling selects the
procedural profile about 1/17 of the time. A weighted pool would create more
novel mazes but could reduce anchor frequency and introduce an unadvertised
sampling policy. The 800-draw census retained 151 public draws per band and 47
unique procedural topologies. A future allocation experiment can evaluate
higher procedural weight without changing this repair.

## D5 — Place one center and three arms on traversable cells

Four keyed samples from the carved maze supply one singleton and three arm
markers. This preserves the canonical role contract and leaves enough zero cells
to fill. **Alternative rejected:** choose marker locations from wall geometry or
encode parameters spatially; either would leak hidden settings or change the
canonical semantics.

## D6 — Keep rule parameters out of production

The prototype's `neighbor_mode` and `phase` axes alter executed transformation,
use a fixed setting per episode, and preserve the canonical default. They live
under `workspace/parametric/` because production still binds one canonical rule.
Python evidence is complete; alternate Racket execution is pending. Acceptance
of the generator repair does not approve these variants.

## D7 — Return a recovery overlay, not a counterfeit official response

The original 350 MB upload exceeded the file service's 100 MB rematerialization
limit after the extracted workspace reset. Reconstructing official `INTAKE.json`,
audit assignments, or packet receipts would be misleading. The package instead
contains a preimage-hash-bound overlay, exact replay commands, local evidence,
and explicit blockers. The original source preimage is
`bb35eded97d3630896e16b409b8c80dd6f5b7439aa2c00f6f08302740db18356`.
