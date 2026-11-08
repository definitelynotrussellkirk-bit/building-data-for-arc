(rule! (lambda (g)
         (let ((blues (find-color g 1)))
           (let ((r1 (fst (nth blues 0)))
                 (c1 (snd (nth blues 0)))
                 (r2 (fst (nth blues 1)))
                 (c2 (snd (nth blues 1))))
             (let ((mr (floor (/ (+ r1 r2) 2)))
                   (mc (floor (/ (+ c1 c2) 2))))
               (let ((stage-a
                      (set-cell
                       (set-cell
                        (set-cell
                         (set-cell
                          (set-cell g mr mc 3)
                          (- mr 1) mc 3)
                         (+ mr 1) mc 3)
                        mr (- mc 1) 3)
                       mr (+ mc 1) 3)))
                 (let* ((remaining (find-color stage-a 1))
                        (target (nth remaining 0))
                        (tr (fst target))
                        (tc (snd target)))
                   (let walk ((r mr) (c mc) (step 0) (out stage-a))
                     (if (and (= r tr) (= c tc))
                         out
                         (let ((nr (cond ((< r tr) (+ r 1))
                                         ((> r tr) (- r 1))
                                         (else r)))
                               (nc (if (= r tr)
                                       (cond ((< c tc) (+ c 1))
                                             ((> c tc) (- c 1))
                                             (else c))
                                       c)))
                           (if (and (= nr tr) (= nc tc))
                               out
                               (walk nr nc (+ step 1)
                                     (if (= step 0)
                                         out
                                         (set-cell out nr nc 8))))))))))))))
