(rule!
  (let* ((horizontal
          (for/fold ((out g)) ((r (in-range (rows g))))
            (let ((colors (remove-duplicates
                           (filter (lambda (v) (not (= v 0))) (row g r)))))
              (for/fold ((acc out)) ((color (in-list colors)))
                (let ((cols-hit (filter (lambda (c) (= (at g r c) color))
                                        (range 0 (cols g)))))
                  (if (= (length cols-hit) 2)
                      (let ((c1 (first cols-hit)) (c2 (second cols-hit)))
                        (if (all? (lambda (c) (= (at g r c) 0))
                                  (range (+ c1 1) c2))
                            (paint-cells acc
                                         (for/list ((c (in-range c1 (+ c2 1)))) (list r c))
                                         color)
                            acc))
                      acc)))))))
    (for/fold ((out horizontal)) ((c (in-range (cols horizontal))))
      (let ((colors (remove-duplicates
                     (filter (lambda (v) (not (= v 0)))
                             (for/list ((r (in-range (rows horizontal))))
                               (at horizontal r c))))))
        (for/fold ((acc out)) ((color (in-list colors)))
          (let ((rows-hit (filter (lambda (r) (= (at horizontal r c) color))
                                  (range 0 (rows horizontal)))))
            (if (= (length rows-hit) 2)
                (let ((r1 (first rows-hit)) (r2 (second rows-hit)))
                  (if (all? (lambda (r) (= (at horizontal r c) 0))
                            (range (+ r1 1) r2))
                      (paint-cells acc
                                   (for/list ((r (in-range r1 (+ r2 1)))) (list r c))
                                   color)
                      acc))
                acc)))))))
