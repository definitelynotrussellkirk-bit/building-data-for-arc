(rule!
  (let ((dummy 0))
    (define base
      (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                ((color (in-list (grid-colors g 0))))
        (let ((cells (find-color g color)))
          (if (= (length cells) 2)
              (let* ((a (first cells)) (b (second cells)))
                (if (and (not (= (first a) (first b)))
                         (not (= (second a) (second b))))
                    (let ((r0 (min (first a) (first b)))
                          (r1 (max (first a) (first b)))
                          (c0 (min (second a) (second b)))
                          (c1 (max (second a) (second b))))
                      (paint-cells
                        out
                        (remove-duplicates
                          (append
                            (for/list ((c (in-range c0 (+ c1 1)))) (list r0 c))
                            (for/list ((c (in-range c0 (+ c1 1)))) (list r1 c))
                            (for/list ((r (in-range r0 (+ r1 1)))) (list r c0))
                            (for/list ((r (in-range r0 (+ r1 1)))) (list r c1))))
                        color))
                    out))
              out))))
    (define frames (objects base 0))
    (define winner
      (select-object-by
        frames
        (lambda (obj) (length (bbox-interior-cells obj)))
        'max))
    (if winner
        (fill-object-interior base winner (obj-color winner) 0)
        base)))
