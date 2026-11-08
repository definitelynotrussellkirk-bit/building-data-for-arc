(rule!
 ;; Identify the large connected TEMPLATE, then classify its background holes
 ;; by shape up to all rotations/reflections. Count external GLYPHS of each
 ;; matching shape by color. Fill each hole with its most frequent matching
 ;; color; numeric minimum resolves exact vote ties. Preserve the template.
 (lambda (g)
  (let ()
   (define least-frequent? #f)
   (define background (mode g -1))
   (define objs (objects-8 g background))
   (define template (pick-max objs obj-size))
   (define bb (obj-bbox template))
   (define template-color (obj-color template))
   (define crop (apply subgrid g bb))
   (define holes (objects crop template-color))
   (define (in-template? p)
    (and (<= (first bb) (first p) (third bb)) (<= (second bb) (second p) (fourth bb))))
   (define glyphs (filter (lambda (o) (not (ormap in-template? (obj-cells o)))) objs))
   (define (matches? a b)
    (member (sort (normalize-cells (obj-cells a)) cell<) (all-transforms (obj-cells b))))
   (for/fold ((out crop)) ((hole (in-list holes)))
    (define matching (filter (lambda (o) (matches? hole o)) glyphs))
    (define palette (unique (map obj-color matching)))
    (define counts (map (lambda (color) (count-if (lambda (o) (= (obj-color o) color)) matching)) palette))
    (if (null? palette) out
     (let* ((best (apply (if least-frequent? min max) counts))
            (chosen (apply min (for/list ((color (in-list palette)) (n (in-list counts)) #:when (= n best)) color))))
      (recolor-cells out (obj-cells hole) chosen)))))))
