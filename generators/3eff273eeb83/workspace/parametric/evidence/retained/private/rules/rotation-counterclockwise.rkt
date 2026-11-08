(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((five (first (find-color g 5)))
                  (r5 (fst five))
                  (c5 (snd five))
                  (twos (map (lambda (cell) (list (- (fst cell) r5) (- (snd cell) c5)))
                             (find-color g 2))))
             (cellmap g
                      (r c v)
                      (if (and (= r r5) (= c c5))
                          5
                          (if (for/or ((d twos))
                                      (and (= r (+ r5 (fst d))) (= c (+ c5 (snd d)))))
                              3
                              (if (for/or ((d twos))
                                          (and
                                            (= r (- r5 (snd d)))
                                            (= c (+ c5 (fst d)))))
                                  2
                                  0))))))))