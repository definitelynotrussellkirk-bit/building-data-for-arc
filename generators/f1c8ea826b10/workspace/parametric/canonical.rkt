(rule!
  (let ((dummy 0))
    (define (chamber-cells start)
      (connected-region g (first start) (second start)
        (lambda (r c v) (not (= v 5)))
        4))
    (define (paint-chamber out region)
      (let ((colors (sort (remove-duplicates
                            (filter (lambda (v) (and (not (= v 0)) (not (= v 5))))
                                    (map (lambda (p) (at g (first p) (second p))) region)))
                          <))
            (bb (bbox-of-cells region)))
        (cond [(empty? colors) (paint-cells out region 0)]
              [(= (length colors) 1) (paint-cells out region (first colors))]
              [else
               (for/fold ([acc out]) ([p (in-list region)])
                 (set-cell acc (first p) (second p)
                           (if (= (modulo (+ (- (first p) (first bb)) (- (second p) (second bb))) 2) 0)
                               (first colors)
                               (last colors))))])))
    (let loop ([remaining (filter-cells g (lambda (r c v) (not (= v 5))))] [out (keep-only g 5)])
      (if (empty? remaining)
          out
          (let ((region (chamber-cells (first remaining))))
            (loop (filter (lambda (p) (not (member? p region))) remaining)
                  (paint-chamber out region)))))))