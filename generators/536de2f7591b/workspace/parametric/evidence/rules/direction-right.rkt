(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (reduce (lambda (grid r)
                     (let* ((threes (filter (lambda (c) (= (at grid r c) 3))
                                            (range 0 w))))
                       (if (null? threes)
                           grid
                           (let* ((gc1 (first threes))
                                  (gc2 (nth threes (- (length threes) 1)))
                                  (glen (+ 1 (- gc2 gc1)))
                                  (stops (filter (lambda (nc) (= (at grid r nc) 8))
                                                 (range (+ gc2 1) w)))
                                  (stop (and (> (length stops) 0) (- (first stops) glen)))
                                  (dest (if stop stop (- w glen))))
                             (if (= dest gc1)
                                 grid
                                 (reduce (lambda (g2 i)
                                           (let ((old-c (+ gc1 i))
                                                 (new-c (+ dest i)))
                                             (set-cell (if (!= old-c new-c)
                                                           (set-cell g2 r old-c 0)
                                                           g2)
                                                       r
                                                       new-c
                                                       3)))
                                         grid
                                         (reverse (range 0 glen))))))))
                   g
                   (range 0 h)))))
