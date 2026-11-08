# Proposed round-trip-count parameterization

This task-local prototype keeps the canonical vertical ping-pong reasoning and
varies only the number of complete down/up traversals. `round_trips=2` is the
original/default setting and materializes the exact canonical Racket program;
`round_trips=1` is the bounded alternate. The setting is selected once per
episode and remains fixed across every demonstration and query.

From the outer extracted packet, create the retained two-setting evidence with:

```bash
python3 review.py run python generators/222de43cc4aa/workspace/parametric/prototype.py evidence \
  --out ../checks/parametric/round-trip-count-v1 --seeds 0 1 --demos 3 --queries 4
```

Focused tests:

```bash
python3 review.py run pytest -q generators/222de43cc4aa/tests/test_parametric_round_trips.py
```

## Boundaries and limitations

- This is a proposed, unapproved authoring prototype. It does not alter the
  canonical rule, catalog state, or training admission.
- Allowed values are exactly `1` and `2`; the default `2` is byte-for-byte the
  canonical program after stripping outer whitespace.
- Inputs are distinct samples from the selected parent generator and retain its
  height `3..8`, width `9..21`, and color grammar. Both settings therefore stay
  within ARC's `30x30` output limit.
- Evidence covers one complete episode per setting, three demonstrations and
  four distinct queries each. Demonstrations distinguish the declared rival
  because the settings produce different output heights on every lawful input.
- Finite examples establish behavior only against this declared two-program
  family, not uniqueness against arbitrary programs or general training value.
- Public challenge files contain only demonstration inputs/outputs and query
  inputs. Seeds, settings, Racket text, query answers, and setting maps remain
  private; public names are hashes of the visible bytes only.
