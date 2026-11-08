(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((dots (find-color g 8))
                  (n (length dots)))
             (reduce (lambda (acc i)
                       (reduce (lambda (acc2 j)
                                 (if (<= j i)
                                     acc2
                                     (let* ((r1 (fst (nth dots i)))
                                            (c1 (snd (nth dots i)))
                                            (r2 (fst (nth dots j)))
                                            (c2 (snd (nth dots j))))
                                       (cond
                                         ((and
                                            #f
                                            (= r1 r2)
                                            (not (find (lambda (k)
                                                         (and
                                                           (!= k i)
                                                           (!= k j)
                                                           (= (fst (nth dots k)) r1)
                                                           (> (snd (nth dots k))
                                                              (min c1 c2))
                                                           (< (snd (nth dots k))
                                                              (max c1 c2))))
                                                       (range 0 n)))) (reduce (lambda (g3 c)
                                                     (if (zero? (at g3 r1 c))
                                                         (set-cell g3 r1 c 8)
                                                         g3))
                                                   acc2
                                                   (range (+ (min c1 c2) 1) (max c1 c2))))
                                         ((and
                                            (= c1 c2)
                                            (not (find (lambda (k)
                                                         (and
                                                           (!= k i)
                                                           (!= k j)
                                                           (= (snd (nth dots k)) c1)
                                                           (> (fst (nth dots k))
                                                              (min r1 r2))
                                                           (< (fst (nth dots k))
                                                              (max r1 r2))))
                                                       (range 0 n)))) (reduce (lambda (g3 r)
                                                     (if (zero? (at g3 r c1))
                                                         (set-cell g3 r c1 8)
                                                         g3))
                                                   acc2
                                                   (range (+ (min r1 r2) 1) (max r1 r2))))
                                         (else acc2)))))
                               acc
                               (range 0 n)))
                     g
                     (range 0 n))))))
