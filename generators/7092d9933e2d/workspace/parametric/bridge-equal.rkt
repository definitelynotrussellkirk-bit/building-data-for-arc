(rule!
  (let* ((h (rows g))
         (w (cols g)))
    (define (source-color r)
      (let ((colors (filter (lambda (v) (not (= v 0))) (row-at g r))))
        (if (empty? colors) 0 (first colors))))
    (define filled
      (grid-from-fn h w
        (lambda (r c) (source-color r))))
    (define (filled-color r) (at filled r 0))
    (define (nearest-above-color r)
      (let ((hits (filter (lambda (rr) (not (= (filled-color rr) 0))) (range r))))
        (if (empty? hits) 0 (filled-color (first (reverse hits))))))
    (define (nearest-below-color r)
      (let ((hits (filter (lambda (rr) (not (= (filled-color rr) 0)))
                          (range (+ r 1) h))))
        (if (empty? hits) 0 (filled-color (first hits)))))
    (grid-from-fn h w
      (lambda (r c)
        (let ((own (at filled r c)))
          (if (not (= own 0))
              own
              (let ((above (nearest-above-color r))
                    (below (nearest-below-color r)))
                (if (and (not (= above 0)) (= above below)) above 0))))))))
