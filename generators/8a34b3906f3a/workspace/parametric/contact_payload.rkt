(rule!
 (let* ((ctr (quotient (rows g) 2))
        (completed
         (for/fold ((out g)) ((p (in-list (find-color g 2))))
           (let loop ((k 0) (rr (first p)) (cc (second p)) (acc out))
             (if (= k 3)
                 acc
                 (let* ((dr (- rr ctr))
                        (dc (- cc ctr))
                        (nr (+ ctr dc))
                        (nc (- ctr dr)))
                   (loop (+ k 1) nr nc (set-cell acc nr nc 2)))))))
        (selected
         (for*/first ((p (in-list (find-color completed 2)))
                      #:when (= (at g (first p) (second p)) 0)
                      (d (in-list '((-1 0) (1 0) (0 -1) (0 1))))
                      #:when
                      (let ((rr (+ (first p) (first d)))
                            (cc (+ (second p) (second d))))
                        (and (in-bounds? rr cc (rows g) (cols g))
                             (>= (at g rr cc) 3)
                             (<= (at g rr cc) 5))))
           (let ((rr (+ (first p) (first d)))
                 (cc (+ (second p) (second d))))
             (at g rr cc)))))
   (if selected (recolor completed selected 8) completed)))
