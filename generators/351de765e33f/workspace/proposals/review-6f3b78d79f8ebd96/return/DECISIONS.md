# Decisions

## Keep the authority fixed
The transformation was correct; the input grammar and lesson ordering were not. The Racket rule and hash are unchanged.

## Remove the moat at the root
Canonical objects are color-specific and 4-connected. Accepting cross-color contacts is the general semantic fix; whitelisting canonical grids would only mask the defect.

## Construct counterexamples
Contact pairs use the top-ranked objects so colorblind merging necessarily changes the ranking. Repeated-largest and all-equal profiles directly test rank multiplicity.

## Declare a finite schedule
An eight-step schedule permits exhaustive cyclic-window verification while a seed-dependent topology shift avoids binding one topology to one size profile.

## Fail closed
Boolean/float coercion and invalid difficulty/profile values are rejected before any draw.

## Make rivals executable
The retained shortcuts are pure functions with witness mappings, canonical-fit tests, and input-purity checks.

## Keep rule-changing research separate
The `target_rank` experiment lives only under `workspace/parametric/`; rank two remains production.

## Preserve uncertainty
The official packet builder, randomized audit draw, and post-reset Racket execution were not fabricated. Their absence is explicit in every report.
