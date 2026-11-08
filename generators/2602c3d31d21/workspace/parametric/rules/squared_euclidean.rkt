(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (key-colors (filter (lambda (v) (!= v 0))
                                    (map (lambda (r) (at g r (- w 1))) (range 0 h))))
                (n (length key-colors))
                (objs (objects g 0))
                (shapes (filter (lambda (o) (> (obj-size o) 1)) objs))
                (spd-for (lambda (color)
                           (let* ((obj (find (lambda (o) (= (obj-color o) color))
                                             shapes)))
                             (if (not obj)
                                 -1
                                 (let* ((cells (obj-cells obj))
                                        (sz (obj-size obj)))
                                   (for/sum ((i (range 0 sz)))
                                     (for/sum ((j (range (+ i 1) sz)))
                                       (let* ((c1 (nth cells i))
                                              (c2 (nth cells j)))
                                         (+ (* (- (first c1) (first c2))
                                               (- (first c1) (first c2)))
                                            (* (- (second c1) (second c2))
                                               (- (second c1) (second c2))))))))))))
                (total (- (* (+ n 1) 3) 1)))
           (grid-from-fn total
                         total
                         (lambda (r c)
                           (let* ((bi (quotient r 3))
                                  (bj (quotient c 3))
                                  (lr (modulo r 3))
                                  (lc (modulo c 3)))
                             (if (or (= lr 2) (= lc 2))
                                 0
                                 (if (and (zero? bi) (zero? bj))
                                     0
                                     (if (zero? bi)
                                         (nth key-colors (- bj 1))
                                         (if (zero? bj)
                                             (nth key-colors (- bi 1))
                                             (if (= bi bj)
                                                 0
                                                 (if (= (spd-for (nth key-colors
                                                                      (- bi 1)))
                                                        (spd-for (nth key-colors
                                                                      (- bj 1))))
                                                     2
                                                     5))))))))))))