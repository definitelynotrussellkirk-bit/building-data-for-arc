# Solve notes

This is a human work log written after the generator repair, with earlier rule exposure declared honestly.

## Visible hypothesis

Every input has height `s` and width `3s+2`. Two full gray/color-5 columns split it into three `s x s` panels. In every visible example, panel 2 is one of the eight square symmetries of panel 1, and the output is that same symmetry applied to panel 3.

I tested the hypothesis against all five visible pairs by enumerating identity, quarter/half/three-quarter rotations, horizontal/vertical reflections, transpose, and anti-transpose. Each visible example has a matching transform and reproduces its shown output exactly. The implementation therefore splits by the known geometry, finds the first exact full-panel match, and transforms the query panel. It does not infer from bounding boxes or foreground coordinates alone, so zero padding is part of the match.

No reference file, Racket rule, private label, generator source, or previous solution explanation was consulted during this solve episode. I had already seen the intended rule while repairing the generator, so this is exposed rather than blind.
