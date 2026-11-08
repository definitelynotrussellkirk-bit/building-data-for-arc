(rule!
  (let* ((midpoints
          (cellmap g (r c v)
            (if (zero? v)
                0
                (let* ((start (last (filter (lambda (cc)
                                              (or (zero? cc)
                                                  (!= (at g r (- cc 1)) v)))
                                            (range 0 (+ c 1)))))
                       (end (find-first (lambda (cc)
                                          (or (= cc (- (cols g) 1))
                                              (!= (at g r (+ cc 1)) v)))
                                        (range c (cols g))))
                       (mid (quotient (+ start end) 2)))
                  (if (= c mid) v 0))))))
    (for/fold ((out midpoints)) ((c (in-range (cols midpoints))))
      (let ((colors
             (remove-duplicates
              (filter (lambda (v) (not (= v 0)))
                      (for/list ((r (in-range (rows midpoints))))
                        (at midpoints r c))))))
        (for/fold ((acc out)) ((color (in-list colors)))
          (let ((hits
                 (filter (lambda (r) (= (at midpoints r c) color))
                         (range 0 (rows midpoints)))))
            (if (= (length hits) 2)
                (let ((r1 (first hits)) (r2 (second hits)))
                  (if (all? (lambda (r) (= (at midpoints r c) 0))
                            (range (+ r1 1) r2))
                      (paint-cells acc
                                   (for/list ((r (in-range r1 (+ r2 1))))
                                     (list r c))
                                   color)
                      acc))
                acc)))))))
