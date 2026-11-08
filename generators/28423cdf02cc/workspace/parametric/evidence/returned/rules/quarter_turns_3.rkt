(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (pat (for/list ((r (range 0 3)))
                       (for/list ((c (range 0 3))) (at g r c))))
                (blues (filter (lambda (p) p)
                               (for*/list ((r (range 0 h)) (c (range 0 w)))
                                 (and (= (at g r c) 1) (list r c))))))
           (reduce (lambda (acc dot)
                     (let* ((dr (first dot))
                            (dc (second dot)))
                       (reduce (lambda (g1 pr)
                                 (reduce (lambda (g2 pc)
                                           (let* ((nr (+ (- dr 1) pr))
                                                  (nc (+ (- dc 1) pc)))
                                             (if (and
                                                   (>= nr 0)
                                                   (< nr h)
                                                   (>= nc 0)
                                                   (< nc w)
                                                   (or
                                                     (zero? (at g2 nr nc))
                                                     (= (at g2 nr nc) 1)))
                                                 (set-cell g2
                                                           nr
                                                           nc
                                                           (nth (nth pat pc) (- 2 pr)))
                                                 g2)))
                                         g1
                                         (range 0 3)))
                               acc
                               (range 0 3))))
                   g
                   blues))))