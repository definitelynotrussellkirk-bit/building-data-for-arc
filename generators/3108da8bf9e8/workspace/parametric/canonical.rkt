(rule! (lambda (g)
         (let* ((cells (for/list ((br (range 0 3)))
                         (for/list ((bc (range 0 3)))
                           (list br
                                 bc
                                 (for/sum ((dr (range 0 3)))
                                   (for/sum ((dc (range 0 3)))
                                     (if (= 1 (at g (+ (* br 4) dr) (+ (* bc 4) dc)))
                                         1
                                         0)))))))
                (flat (reduce append (list) cells))
                (sorted (sort-by flat (lambda (x) (third x))))
                (targets (list (list 2 0)
                               (list 2 1)
                               (list 2 2)
                               (list 1 0)
                               (list 1 1)
                               (list 1 2)
                               (list 0 0)
                               (list 0 1)
                               (list 0 2))))
           (grid-from-fn 11
                         11
                         (lambda (r c)
                           (if (or (= (mod r 4) 3) (= (mod c 4) 3))
                               0
                               (let* ((tbr (floor (/ r 4)))
                                      (tbc (floor (/ c 4)))
                                      (idx (find-first (lambda (i)
                                                         (and
                                                           (= tbr (fst (nth targets i)))
                                                           (= tbc (snd (nth targets i)))))
                                                       (range 0 9)))
                                      (src (nth sorted idx))
                                      (sbr (fst src))
                                      (sbc (snd src))
                                      (dr (mod r 4))
                                      (dc (mod c 4)))
                                 (at g (+ (* sbr 4) dr) (+ (* sbc 4) dc)))))))))