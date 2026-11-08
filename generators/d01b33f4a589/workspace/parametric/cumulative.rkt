(rule!
  (let ((dummy 0))
    (define (transform-code grid code)
      (cond [(= code 1) (rotate-cw grid)]
            [(= code 2) (rotate-180 grid)]
            [(= code 3) (flip-lr grid)]
            [else (flip-ud grid)]))
    (define (crop-cells base cells)
      (let* ((bb (bbox-of-cells cells))
             (r0 (first bb)) (c0 (second bb))
             (r1 (third bb)) (c1 (fourth bb)))
        (grid-from-fn (+ 1 (- r1 r0)) (+ 1 (- c1 c0))
          (lambda (r c)
            (let ((rr (+ r0 r)) (cc (+ c0 c)))
              (if (member? (list rr cc) cells) (at base rr cc) 0))))))
    (define (cumulative-variants motif codes)
      (let loop ((remaining codes) (current motif) (acc (list)))
        (if (empty? remaining)
            (reverse acc)
            (let ((next-grid (transform-code current (first remaining))))
              (loop (rest remaining) next-grid (cons next-grid acc))))))
    (define (paste-nonzero out pat top left)
      (for*/fold ([acc out])
                 ([r (in-range (rows pat))]
                  [c (in-range (cols pat))]
                  #:when (not (= (at pat r c) 0)))
        (set-cell acc (+ top r) (+ left c) (at pat r c))))
    (let* ((h (rows g))
           (w (cols g))
           (codes (list (at g 0 0) (at g 0 (- w 1)) (at g (- h 1) 0) (at g (- h 1) (- w 1))))
           (ignore (list (list 0 0) (list 0 (- w 1)) (list (- h 1) 0) (list (- h 1) (- w 1))))
           (motif-cells
             (filter-cells g
               (lambda (r c v) (and (not (= v 0)) (not (member? (list r c) ignore))))))
           (motif (crop-cells g motif-cells))
           (variants (cumulative-variants motif codes))
           (cell-h (apply max (map rows variants)))
           (cell-w (apply max (map cols variants))))
      (for/fold ([out (empty-grid (* 2 cell-h) (* 2 cell-w) 0)])
                ([variant (in-list variants)] [idx (in-naturals)])
        (paste-nonzero out variant (* (quotient idx 2) cell-h) (* (modulo idx 2) cell-w))))))