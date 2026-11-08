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
    (define stamped (paste (empty-grid (rows g) (cols g) 0) crop (first marker) (second marker)))
    ;; Counterfactual: B consumes the wrong intermediate color, the crop's
    ;; top-left cell, instead of the majority color.
    (define wrong-color (at crop 0 0))
    (define top (- (first marker) 1))
    (define left (- (second marker) 1))
    (define bottom (+ (first marker) (rows crop)))
    (define right (+ (second marker) (cols crop)))
    (define framed
      (for*/fold ([out stamped]) ([r (in-range top (+ bottom 1))]
                                  [c (in-range left (+ right 1))])
        (if (or (= r top) (= r bottom) (= c left) (= c right))
            (set-cell out r c wrong-color)
            out)))
    (paste framed crop (first marker) (second marker))))
