(rule!
  (let ((dummy 0))
    (define (border-cells bb)
      (append
        (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (first bb) c))
        (for/list ([c (in-range (second bb) (+ (fourth bb) 1))]) (list (third bb) c))
        (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (second bb)))
        (for/list ([r (in-range (+ (first bb) 1) (third bb))]) (list r (fourth bb)))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([color (in-list (grid-colors g 0))])
      (let ((cells (find-color g color)))
        (if (= (length cells) 2)
            (paint-cells out (border-cells (bbox-of-cells cells)) color)
            out)))))