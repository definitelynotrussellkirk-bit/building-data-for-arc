(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (bg 7)
                (grays (find-color g 5)))
           (reduce (lambda (acc gpos)
                     (let* ((gr (fst gpos))
                            (gc (snd gpos))
                            (start-d (find-first (lambda (d)
                                                   (let* ((nr (+ gr (fst d)))
                                                          (nc (+ gc (snd d))))
                                                     (and
                                                       (in-bounds? nr nc h w)
                                                       (= (at g nr nc) 3))))
                                                 cardinal-deltas)))
                       (if (not start-d)
                           acc
                           (let* ((start (list (+ gr (fst start-d))
                                               (+ gc (snd start-d))))
                                  (path (reduce (lambda (p step)
                                                  (let* ((cur (fst p))
                                                         (prev (snd p))
                                                         (trail (nth p 2))
                                                         (next-d (find-first (lambda (d)
                                                                               (let* ((nr (+ (fst cur)
                                                                                             (fst d)))
                                                                                      (nc (+ (snd cur)
                                                                                             (snd d))))
                                                                                 (and
                                                                                   (in-bounds? nr
                                                                                               nc
                                                                                               h
                                                                                               w)
                                                                                   (= (at g
                                                                                          nr
                                                                                          nc)
                                                                                      3)
                                                                                   (not (and
                                                                                          (= nr
                                                                                             (fst prev))
                                                                                          (= nc
                                                                                             (snd prev)))))))
                                                                             cardinal-deltas))
                                                         (next (if next-d
                                                                   (list (+ (fst cur)
                                                                            (fst next-d))
                                                                         (+ (snd cur)
                                                                            (snd next-d)))
                                                                   #f)))
                                                    (if next
                                                        (list next
                                                              cur
                                                              (append trail (list next)))
                                                        p)))
                                                (list start (list gr gc) (list start))
                                                (range 0 (max h w))))
                                  (trail (nth path 2)))
                             (if (< (length trail) 2)
                                 acc
                                 (let* ((cleared (reduce (lambda (a cell)
                                                           (set-cell a
                                                                     (fst cell)
                                                                     (snd cell)
                                                                     bg))
                                                         acc
                                                         trail))
                                        (last (nth trail (- (length trail) 1)))
                                        (second (nth trail (- (length trail) 2))))
                                   (set-cell (set-cell (set-cell cleared
                                                                 (fst last)
                                                                 (snd last)
                                                                 3)
                                                       (fst second)
                                                       (snd second)
                                                       5)
                                             gr
                                             gc
                                             bg)))))))
                   g
                   grays))))