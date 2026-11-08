(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((dots (sort-by (reduce (lambda (acc c)
                                           (append acc
                                                   (map (lambda (p)
                                                          (list (fst p) (snd p) c))
                                                        (find-color g c))))
                                         (list)
                                         (range 1 10))
                                 (lambda (d) (fst d))))
                  (n (length dots))
                  (selected-i (reduce (lambda (best i)
                                        (if (< (snd (nth dots i))
                                               (snd (nth dots best)))
                                            i
                                            best))
                                      0
                                      (range 1 n))))
             (cellmap g
                      (r c v)
                      (let* ((bi (reduce (lambda (best i)
                                           (let* ((dr (fst (nth dots i)))
                                                  (bs (if (zero? i)
                                                          0
                                                          (+ (floor (/ (+ (fst (nth dots
                                                                                    (- i
                                                                                       1)))
                                                                          dr)
                                                                       2))
                                                             1)))
                                                  (be (if (= i (- n 1))
                                                          (- h 1)
                                                          (floor (/ (+ dr
                                                                       (fst (nth dots
                                                                                 (+ i 1))))
                                                                    2)))))
                                             (if (and (>= r bs) (<= r be)) i best)))
                                         0
                                         (range 0 n)))
                             (dr (fst (nth dots bi)))
                             (color (nth (nth dots bi) 2)))
                        (cond
                          ((= r dr) color)
                          ((and (zero? bi) (zero? r)) color)
                          ((and (= bi (- n 1)) (= r (- h 1))) color)
                          ((and (= bi selected-i)
                                (or (zero? c) (= c (- w 1)))) color)
                          (else 0))))))))
