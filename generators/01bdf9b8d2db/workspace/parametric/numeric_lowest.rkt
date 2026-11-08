(rule!
  (let ((dummy 0))
    (define (chamber-cells grid start)
      (connected-region grid (first start) (second start)
        (lambda (r c v) (not (= v 5)))
        4))
    (define (marker-color grid cells)
      (let ((hit (find-first (lambda (p)
                               (let ((v (at grid (first p) (second p))))
                                 (and (not (= v 0)) (not (= v 5)))))
                             cells)))
        (if hit (at grid (first hit) (second hit)) 0)))
    (define (fill-chambers grid)
      (let loop ([remaining (filter-cells grid (lambda (r c v) (not (= v 5))))]
                 [out (keep-only grid 5)])
        (if (empty? remaining)
            out
            (let* ((region (chamber-cells grid (first remaining)))
                   (color (marker-color grid region)))
              (loop (filter (lambda (p) (not (member? p region))) remaining)
                    (paint-cells out region color))))))

    (let* ((filled (fill-chambers g))
           (colors (sort (remove-duplicates
                           (filter (lambda (v) (and (not (= v 0)) (not (= v 5))))
                                   (apply append filled))) <))
           (selected (first colors)))
      (paint-cells filled (find-color filled selected) 9))))
