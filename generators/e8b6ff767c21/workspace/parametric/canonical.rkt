(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (dirs (list (list 0 1) (list 1 0) (list 0 -1) (list -1 0)))
                (start (set-cell (cellmap g (r c v) 0) 0 0 3)))
           (let loop
                ((s 0) (rr 0) (cc 0) (acc start))
                (let* ((base (if (zero? (remainder s 2)) (- w 1) (- h 1)))
                       (shrink (if (< s 3) 0 (* 2 (quotient (- s 1) 2))))
                       (len (- base shrink)))
                  (if (<= len 0)
                      acc
                      (let* ((dir (nth dirs (remainder s 4)))
                             (dr (fst dir))
                             (dc (snd dir)))
                        (let step
                             ((i 0) (cr rr) (cur-c cc) (a acc))
                             (if (= i len)
                                 (loop (+ s 1) cr cur-c a)
                                 (let* ((nr (+ cr dr))
                                        (nc (+ cur-c dc)))
                                   (step (+ i 1)
                                         nr
                                         nc
                                         (if (in-bounds? nr nc h w)
                                             (set-cell a nr nc 3)
                                             a))))))))))))