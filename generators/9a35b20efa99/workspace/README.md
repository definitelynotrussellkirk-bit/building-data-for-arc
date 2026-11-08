# Review workspace for 9a35b20efa99

`reference_probe.py` is reusable source-bound support for this generator. It:

- finds the portable repository root through `reviewer_support.find_root`,
- loads canonical pairs through `reviewer_support.canonical_pairs`,
- analyzes the four declared asymmetric template families independently of the
  production generator,
- computes a direct crop/rotate/stamp oracle,
- implements the canonical-fitting `above_only` and `corner_l_only` rivals,
- constructs the retained branch-below witness, and
- can require the real selected Racket authority for parity checks.

The probe deliberately does not import geometry or rival implementations from
`generator.py`. Future tests should iterate the generator's actual rival
registries rather than maintaining a second copied name list.
