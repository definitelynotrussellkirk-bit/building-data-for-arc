(rule!
 ;; Crop the unique largest perforated full-border template.  Every background
 ;; cavity is a shape slot.  Components outside the template vote only for
 ;; congruent slots, with rotations and reflections identified; fill each slot
 ;; with the modal vote color for its own shape class.
 (lambda (g)
  (let ()
    (define vote-policy "modal")
    (define bg (mode g -1))
    (define os (objects g bg))
    (define frame (pick-max os obj-size))
    (define base (obj-color frame))
    (define r1 (obj-r1 frame))
    (define c1 (obj-c1 frame))
    (define r2 (obj-r2 frame))
    (define c2 (obj-c2 frame))
    (define template (subgrid g r1 c1 r2 c2))
    (define holes (objects template base))
    ;; Perforations can isolate small islands of the base color.  All objects
    ;; touching the frame bounding box are template material, never votes.
    (define (overlaps-template? o)
      (for/or ((p (obj-cells o)))
        (and (<= r1 (first p) r2) (<= c1 (second p) c2))))
    (define pieces (filter (lambda (o) (not (overlaps-template? o))) os))
    (define (matching hole)
      (define target (sort (normalize-cells (obj-cells hole)) cell<))
      (filter (lambda (o) (member target (all-transforms (obj-cells o)))) pieces))
    (define (winner matches)
      (define colors (sort (remove-duplicates (map obj-color matches)) <))
      (define (frequency color)
        (length (filter (lambda (o) (= (obj-color o) color)) matches)))
      (if (equal? vote-policy "modal")
          (pick-max colors frequency)
          (pick-min colors frequency)))
    ;; Step B consumes the D4 class-specific vote histogram from Step A.
    (for/fold ((out template)) ((hole holes))
      (define matches (matching hole))
      (recolor-cells out (obj-cells hole) (winner matches))))))
