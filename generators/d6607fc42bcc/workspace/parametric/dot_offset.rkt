(rule! (lambda (g)
         (let* ((objs (objects-multicolor g))
                (blue-objs (filter (lambda (o)
                                     (for/or ((cl (obj-cells o)))
                                             (= 1 (at g (fst cl) (snd cl)))))
                                   objs)))
           (reduce (lambda (acc obj)
                     (let* ((fr1 (obj-r1 obj))
                            (fr2 (obj-r2 obj))
                            (fc1 (obj-c1 obj))
                            (fc2 (obj-c2 obj))
                            (interior (positions-in-rect (+ fr1 1)
                                                         (+ fc1 1)
                                                         (- fr2 1)
                                                         (- fc2 1)))
                            (dot (find (lambda (p)
                                         (let* ((v (at g (fst p) (snd p))))
                                           (and (!= 0 v) (!= 1 v))))
                                       interior))
                            (dc (if dot (at g (fst dot) (snd dot)) 0)))
                       (if (zero? dc)
                           acc
                           (let* ((top-open (not (all? (lambda (kc) (= 1 (at g fr1 kc)))
                                                       (range (+ fc1 1) fc2))))
                                  (depth (if top-open
                                             (- (fst dot) fr1)
                                             (- fr2 (fst dot)))))
                             (cellmap g
                                      (r kc v)
                                      (cond
                                        ((and
                                           (> r fr1)
                                           (< r fr2)
                                           (> kc fc1)
                                           (< kc fc2)
                                           (zero? (at acc r kc))) dc)
                                        ((and
                                           top-open
                                           (= r fr1)
                                           (> kc fc1)
                                           (< kc fc2)
                                           (zero? v)) dc)
                                        ((and
                                           top-open
                                           (>= r (- fr1 depth))
                                           (< r fr1)
                                           (>= kc fc1)
                                           (<= kc fc2)) dc)
                                        ((and
                                           (not top-open)
                                           (= r fr2)
                                           (> kc fc1)
                                           (< kc fc2)
                                           (zero? v)) dc)
                                        ((and
                                           (not top-open)
                                           (> r fr2)
                                           (<= r (+ fr2 depth))
                                           (>= kc fc1)
                                           (<= kc fc2)) dc)
                                        (else (at acc r kc))))))))
                   g
                   blue-objs))))