# API boundary disposition

The advertised `scene_profile` override behaves as a closed, observable API boundary on the pinned generator source.

- A valid `cell3_corner_template` override generates an 11×11 lesson, is reported exactly by `observe_overrides`, passes `self_check`, and produces a visible rule change.
- An undeclared profile is rejected with `ValueError` before construction by `GenCtx.draw_choice`: `override 'not-a-declared-profile' not in options`.
- No peer source was changed and no safety finding is claimed.

The first authoring assertion expected the later generator-local wording (`unknown scene_profile`) and failed. Static tracing showed that override validation correctly occurs earlier in `GenCtx`; the final retained probe asserts the actual layer and wording. This is a probe correction, not a generator repair.
