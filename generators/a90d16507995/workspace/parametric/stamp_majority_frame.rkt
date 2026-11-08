(rule!
  (let ((dummy 0))
    (define (paste grid pattern top left)
      (for*/fold ([out grid]) ([r (in-range (rows pattern))]
                               [c (in-range (cols pattern))])
        (let ((v (at pattern r c))
              (rr (+ top r))
              (cc (+ left c)))
          (if (and (not (= v 0)) (in-bounds? rr cc (rows out) (cols out)))
              (set-cell out rr cc v)
              out))))
    (define marker (first (find-color g 9)))
    (define source-cells
      (filter (lambda (p)
                (let ((v (at g (first p) (second p))))
                  (not (member? v (list 0 9)))))
              (grid-positions g)))
    (define bb (bbox-of-cells source-cells))
    (define crop (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
    ;; Step A: stamp the tight source crop at the color-9 marker.
    (define stamped
      (paste (empty-grid (rows g) (cols g) 0)
             crop (first marker) (second marker)))
    ;; Intermediate: the stamped crop and its unique majority color.
    (define values
      (filter (lambda (v) (not (= v 0)))
              (map (lambda (p) (at crop (first p) (second p)))
                   (grid-positions crop))))
    (define colors (remove-duplicates values))
    (define (frequency color)
      (length (filter (lambda (v) (= v color)) values)))
    (define majority
      (first
       (sort colors
             (lambda (a b)
               (or (> (frequency a) (frequency b))
                   (and (= (frequency a) (frequency b)) (< a b)))))))
    ;; Step B: frame the destination crop one cell outside its bbox using
    ;; the majority color derived from the stamped intermediate.
    (define top (- (first marker) 1))
    (define left (- (second marker) 1))
    (define bottom (+ (first marker) (rows crop)))
    (define right (+ (second marker) (cols crop)))
    (define framed
      (for*/fold ([out stamped]) ([r (in-range top (+ bottom 1))]
                                  [c (in-range left (+ right 1))])
        (if (or (= r top) (= r bottom) (= c left) (= c right))
            (set-cell out r c majority)
            out)))
    (paste framed crop (first marker) (second marker))))
