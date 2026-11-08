(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg 7)
                  (comp-map (make-hash))
                  (comp-cells (make-hash))
                  (comp-id 0))
             (for* ((r (range 0 h)) (kc (range 0 w)))
                   (when
                     (and
                       (!= (at g r kc) bg)
                       (not (hash-has-key? comp-map (list r kc))))
                     (set! comp-id (+ comp-id 1))
                     (hash-set! comp-cells comp-id (list))
                     (let bfs
                          ((queue (list (list r kc))))
                          (unless
                            (null? queue)
                            (let ((cur (car queue)))
                              (cond
                                ((hash-has-key? comp-map cur) (bfs (cdr queue)))
                                ((or
                                   (< (first cur) 0)
                                   (>= (first cur) h)
                                   (< (second cur) 0)
                                   (>= (second cur) w)) (bfs (cdr queue)))
                                ((= (at g (first cur) (second cur)) bg) (bfs (cdr queue)))
                                (else (hash-set! comp-map cur comp-id)
                                      (hash-set! comp-cells
                                                 comp-id
                                                 (cons cur
                                                       (hash-ref comp-cells
                                                                 comp-id
                                                                 (list))))
                                      (let ((cr (first cur))
                                            (cc (second cur)))
                                        (bfs (append (cdr queue)
                                                     (list (list (- cr 1) cc)
                                                           (list (+ cr 1) cc)
                                                           (list cr (- cc 1))
                                                           (list cr (+ cc 1)))))))))))))
             (let ((result (make-hash)))
               (for* ((r (range 0 h)) (kc (range 0 w)))
                     (hash-set! result (list r kc) bg))
               (for ((id (range 1 (+ comp-id 1))))
                 (let* ((cells (hash-ref comp-cells id (list)))
                        (clr (at g (first (first cells)) (second (first cells))))
                        (rs (map first cells))
                        (cs (map second cells))
                        (n (length cells)))
                   (cond
                     ((= n 1) (hash-set! result (first cells) clr))
                     ((= (min-list rs) (max-list rs)) (let* ((rr (first rs))
                              (cmin (min-list cs))
                              (cmax (max-list cs))
                              (cctr (quotient (+ cmin cmax) 2))
                              (half (quotient (- cmax cmin) 2)))
                         (for ((i (range (- rr half) (+ rr half 1))))
                           (when
                             (and (>= i 0) (< i h))
                             (hash-set! result (list i cctr) clr)))))
                     ((= (min-list cs) (max-list cs)) (let* ((kc (first cs))
                              (rmin (min-list rs))
                              (rmax (max-list rs))
                              (rctr (quotient (+ rmin rmax) 2))
                              (half (quotient (- rmax rmin) 2)))
                         (for ((j (range (- kc half) (+ kc half 1))))
                           (when
                             (and (>= j 0) (< j w))
                             (hash-set! result (list rctr j) clr))))))))
               (cellmap g (r c v) (hash-ref result (list r c) bg)))))))