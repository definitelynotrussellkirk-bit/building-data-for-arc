# Keyed rotation with a measured row selector

This separate native adapter retains the exact canonical Racket program and
adds two nearby rules. `line_rule` is fixed across an episode:

| Setting | Executed behavior |
| --- | --- |
| `canonical` | Clear the corner key, crop the object, rotate: 1=CW, 2=180°, 3=CCW. |
| `most_cells` | Perform the canonical rotation, then complete the topmost row having the greatest occupied-cell count. |
| `least_cells` | Perform the canonical rotation, then complete the topmost nonempty row having the least occupied-cell count. |

Completion uses the object's color and the full width of the rotated crop.
The input grammar is one nonzero monochrome 4-connected object on black,
distinct from the key and outside its reserved top-left 2×2 moat. The prototype
extends the production generator's linked small profiles; it does not claim
that those broader shapes pass the production profile validator.

## Dependency and teaching

**A** clears the key, crops, rotates, and measures the resulting row occupancies.
The **intermediate** is that input-dependent count vector and its topmost
extremal row. **B** completes the selected row. Shape contents and key jointly
determine which row is changed. Filling before rotating can change both the
orientation of the added cells and the selected line. The native causal witness
executes this wrong-order alternative on a qualified pair.

Three demonstrations are the supported minimum because the lesson must show
all three key meanings. The adapter accepts **3–6 demos and 1–4 queries** as
independent strict integer requests. The first two demos teach topmost ties and
occupied-cell count versus occupied span; later demos vary connected geometry.
Keys are permuted by seed, not fixed to a teaching slot across seeds. The first
two witness shapes vary by scale, horizontal reflection, color, and placement;
additional demonstrations and queries use sampled connected shapes. This
deliberate teaching scaffold is a limit on demo topology diversity, not a claim
that every demonstration shape is drawn from an unconstrained distribution.

Each setting receives exactly the same inputs for a shared seed. Train/query
prefixes do not depend on requested counts. Four novel queries use compact,
medium, large, and exact 30×30 objects. The largest connected object reaches all
four boundaries while avoiding the key moat; the 30×30 output therefore has
substantive content, rather than blank padding around a tiny object. Sampling
uses local, content-seeded RNGs; retries have explicit bounds and never silently
return a short batch. Seeds are exact integers in 0..2**63−1.

## Runnable checks

Commands below run from the review packet's outer directory; payloads run in
`WORK/repo`. Use a new output directory for each audit after source changes.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/80a3c4f25880/tests/test_parametric.py \
  generators/80a3c4f25880/tests/test_parametric_audit.py

WORK/.venv/bin/python review.py run python3 -B \
  generators/80a3c4f25880/workspace/parametric/audit.py \
  --seed 0 --seed 17 --out ../checks/80a3c4f25880/audit-new
```

The reusable audit verifies every selected label through protected Racket and
screens candidate rules on demonstrations only. It compares queries only for
survivors, retains a divergent lesson if one exists, and treats execution errors
as failures rather than as refutations. Named rivals cover the other settings,
rotation-key permutations and constant rotations, keeping the key/canvas,
bottommost/all-tie selection, occupied span, fixed first/last row, a selected
column, wrong order, and filling the bounding box. Its finite corpus and rivals
do not prove universal uniqueness or every-seed correctness.

`audit.py` also exports and verifies canonical hash-named public challenges.
`public_turn(episode, index)` reveals all demonstrations and exactly one query
input. It reveals no index, seed, setting, answer, future query, total count, or
last-turn flag. The caller advances after an answer; this is a projection, not
a new training controller. The first turn is byte-identical for one-query and
four-query requests with the same seed, setting, and demo count. `private.json`
and the audit report contain programs, answers, descriptions, and provenance;
they must remain authoring evidence. The serialized verifier checks hashes and
projection, not authenticity of an entirely rewritten bundle or a fresh replay.

Native handoff, after the evidence inventory is current:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  80a3c4f25880 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/80a3c4f25880/qualification-new --summary
```

`promotion.json` is the native contract. `canonical.rkt` copies the registered
default byte-for-byte. The Python mirror supplies claims for sampling; native
qualification independently executes all returned labels through Racket.
Qualification grants reviewer readiness only. The owner must qualify and
accept the exact integrated source; no acceptance or training admission is
performed by these tools.

## Separate production-mirror finding

`../mirror_probe.py` reproduces an admitted V5 object whose bounding box includes
the key. The existing production Python mirror crops before clearing the key,
so that mirror can leak the key into its output. Canonical Racket and this
adapter clear it correctly. The probe executes the witness plus all four
canonical regressions and emits a proposed repair patch tested in memory.
The production source stays unchanged and approved for this native handoff.
Applying the patch requires owner reapproval, a refreshed inventory, and a new
qualification on those modified bytes; it must not reuse this qualification.
