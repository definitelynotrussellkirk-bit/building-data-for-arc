(rule! (lambda (g)
         (reduce (lambda (acc pos)
                   (let* ((r (fst pos))
                          (c (snd pos))
                          (v (at g r c)))
                     (if (zero? v)
                         acc
                         (reduce (lambda (g2 dir)
                                   (let ((dr (fst dir))
                                         (dc (snd dir)))
                                     (reduce (lambda (g3 d)
                                               (let ((nr (+ r (* dr d)))
                                                     (nc (+ c (* dc d))))
                                                 (if (and
                                                       (in-bounds? nr nc h w)
                                                       (zero? (at g nr nc))
                                                       (zero? (at g3 nr nc)))
                                                     (set-cell g3 nr nc v)
                                                     g3)))
                                             g2
                                             (range 1 (max h w)))))
                                 acc
                                 diagonal-deltas))))
                 g
                 (grid-positions g))))