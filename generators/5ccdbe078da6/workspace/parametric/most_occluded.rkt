(rule!
  (let ((dummy 0))
    (define (colors-reading grid)
      (remove-duplicates
       (filter (lambda (v) (not (= v 0)))
               (map (lambda (p) (at grid (first p) (second p)))
                    (grid-positions grid)))))
    (define (border-cells r0 c0 r1 c1)
      (for*/list ([r (in-range r0 (+ r1 1))]
                  [c (in-range c0 (+ c1 1))]
                  #:when (or (= r r0) (= r r1) (= c c0) (= c c1)))
        (list r c)))
    (define (paint-outlines grid)
      (for/fold ([out (empty-grid (rows grid) (cols grid) 0)])
                ([color (in-list (colors-reading grid))])
        (let ((cells (find-color grid color)))
          (if (= (length cells) 2)
              (let ((bb (bbox-of-cells cells)))
                (paint-cells out
                             (border-cells (first bb) (second bb) (third bb) (fourth bb))
                             color))
              (paint-cells out cells color)))))
    (let* ((outlined (paint-outlines g))
           (paired (filter (lambda (color) (= (length (find-color g color)) 2))
                           (colors-reading g))))
      (if (empty? paired)
          outlined
          (let* ((loss
                  (lambda (color)
                    (let* ((bb (bbox-of-cells (find-color g color)))
                           (border (border-cells (first bb) (second bb) (third bb) (fourth bb))))
                      (- (length border)
                         (length
                          (filter (lambda (p)
                                    (= (at outlined (first p) (second p)) color))
                                  border))))))
                 (selected
                  (for/fold ([best (first paired)]) ([color (in-list (rest paired))])
                    (if (> (loss color) (loss best)) color best)))
                 (bb (bbox-of-cells (find-color g selected)))
                 (inside
                  (for*/list ([r (in-range (+ (first bb) 1) (third bb))]
                              [c (in-range (+ (second bb) 1) (fourth bb))])
                    (list r c))))
            (paint-cells outlined inside selected))))))
