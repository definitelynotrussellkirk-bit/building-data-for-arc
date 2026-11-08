(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define nines (find-color g 9))
             (if (empty? nines)
                 g
                 (let* ((c (snd (fst nines)))
                        (rmin (min-of fst nines))
                        (rmax (max-of fst nines))
                        (r1 (let loop
                                 ((r rmin))
                                 (if (and
                                       (> r 0)
                                       (let ((v (at g (- r 1) c))) (or (= v 8) (= v 9))))
                                     (loop (- r 1))
                                     r)))
                        (r2 (let loop
                                 ((r rmax))
                                 (if (and
                                       (< r (- h 1))
                                       (let ((v (at g (+ r 1) c))) (or (= v 8) (= v 9))))
                                     (loop (+ r 1))
                                     r)))
                        (top? (= rmin r1))
                        (target-len (+ 2 (+ 1 (- r2 r1))))
                        (block-len (+ 1 (length nines)))
                        (base (recolor-cells g nines 8))
                        (target #f))
                   (for* ((cc (range 0 w)) (rr (range 0 h)))
                         (when
                           (and
                             (not target)
                             (= (at base rr cc) 8)
                             (or (zero? rr) (!= (at base (- rr 1) cc) 8)))
                           (let ((end (let scan
                                           ((er rr))
                                           (if (and
                                                 (< er (- h 1))
                                                 (= (at base (+ er 1) cc) 8))
                                               (scan (+ er 1))
                                               er))))
                             (when
                               (= (+ 1 (- end rr)) target-len)
                               (set! target (list rr cc end))))))
                   (if target
                       (let* ((tr1 (fst target))
                              (tc (snd target))
                              (tr2 (nth target 2))
                              (start (if top? tr1 (+ 1 (- tr2 block-len)))))
                         (reduce (lambda (acc rr) (set-cell acc rr tc 9))
                                 base
                                 (range start (+ start block-len))))
                       base)))))))