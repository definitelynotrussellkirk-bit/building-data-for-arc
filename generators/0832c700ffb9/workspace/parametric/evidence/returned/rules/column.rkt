(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((dots (for*/list ((r (range 0 h)) (c (range 0 w)) #:when (!= (at g r c) 0))
                          (list r c (at g r c))))
                  (result (make-hash)))
             (for* ((r (range 0 h)) (c (range 0 w))) (hash-set! result (list r c) 0))
             (for ((dot dots))
               (let* ((dr (first dot))
                      (dc (second dot))
                      (color (third dot))
                      (other-color (for/first ((d dots) #:when
                                                (and
                                                  (= (second d) dc)
                                                  (!= (first d) dr)))
                                              (third d))))
                 (for* ((ddr (range -1 2)) (ddc (range -1 2)))
                       (let ((nr (+ dr ddr))
                             (nc (+ dc ddc)))
                         (when
                           (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                           (hash-set! result
                                      (list nr nc)
                                      (if (and (zero? ddr) (zero? ddc))
                                          color
                                          other-color)))))))
             (for ((d1 dots))
               (for ((d2 dots))
                 (when
                   (and (= (first d1) (first d2)) (< (second d1) (second d2)))
                   (let* ((dr (first d1))
                          (lc (second d1))
                          (rc (second d2))
                          (mid (/ (+ 0.0 lc rc) 2.0)))
                     (let loop
                          ((c (+ lc 2)))
                          (when
                            (<= (+ c 0.0) mid)
                            (hash-set! result (list dr c) 5)
                            (loop (+ c 2))))
                     (let loop
                          ((c (- rc 2)))
                          (when
                            (>= (+ c 0.0) mid)
                            (hash-set! result (list dr c) 5)
                            (loop (- c 2))))))))
             (for ((d1 dots))
               (for ((d2 dots))
                 (when
                   (and (= (second d1) (second d2)) (< (first d1) (first d2)))
                   (let* ((dc (second d1))
                          (tr (first d1))
                          (br (first d2))
                          (mid (/ (+ 0.0 tr br) 2.0)))
                     (let loop
                          ((r (+ tr 2)))
                          (when
                            (<= (+ r 0.0) mid)
                            (hash-set! result (list r dc) 5)
                            (loop (+ r 2))))
                     (let loop
                          ((r (- br 2)))
                          (when
                            (>= (+ r 0.0) mid)
                            (hash-set! result (list r dc) 5)
                            (loop (- r 2))))))))
             (cellmap g (r c v) (hash-ref result (list r c) 0))))))
