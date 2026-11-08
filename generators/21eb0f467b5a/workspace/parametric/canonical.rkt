(rule!
  (let ((dummy 0))
    (define (paint-color out color)
      (let ((cells (find-color g color)))
        (if (not (= (length cells) 2))
            (paint-cells out cells color)
            (let* ((a (first cells))
                   (b (second cells))
                   (r1 (first a)) (c1 (second a))
                   (r2 (first b)) (c2 (second b)))
              (cond [(= r1 r2)
                     (paint-cells out (for/list ([c (in-range (min c1 c2) (+ (max c1 c2) 1))]) (list r1 c)) color)]
                    [(= c1 c2)
                     (paint-cells out (for/list ([r (in-range (min r1 r2) (+ (max r1 r2) 1))]) (list r c1)) color)]
                    [else (paint-cells out cells color)])))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)])
              ([color (in-list (grid-colors g 0))])
      (paint-color out color))))