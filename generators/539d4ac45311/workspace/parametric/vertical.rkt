(rule!
  (let ((dummy 0))
    (for/fold ((out g)) ((c (in-range (cols g))))
      (let ((colors (remove-duplicates
                     (filter (lambda (v) (not (= v 0)))
                             (for/list ((r (in-range (rows g)))) (at g r c))))))
        (for/fold ((acc out)) ((color (in-list colors)))
          (let ((rows-hit (filter (lambda (r) (= (at g r c) color))
                                  (range 0 (rows g)))))
            (if (= (length rows-hit) 2)
                (let ((r1 (first rows-hit)) (r2 (second rows-hit)))
                  (if (all? (lambda (r) (= (at g r c) 0))
                            (range (+ r1 1) r2))
                      (paint-cells acc
                                   (for/list ((r (in-range r1 (+ r2 1)))) (list r c))
                                   color)
                      acc))
                acc)))))))
