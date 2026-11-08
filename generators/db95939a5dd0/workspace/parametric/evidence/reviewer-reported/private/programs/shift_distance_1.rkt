(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg (mode g))
                  (all-cells (for*/list ((r (range 0 h)) (c (range 0 w))
                                 #:when
                                 (!= (at g r c) bg))
                               (list r c)))
                  (cell-set (make-hash))
                  (_cs (for ((p all-cells)) (hash-set! cell-set p #t)))
                  (vis (make-hash))
                  (components (let loop
                                   ((cells all-cells) (acc (list)))
                                   (cond
                                     ((null? cells) (reverse acc))
                                     ((hash-has-key? vis (car cells)) (loop (cdr cells) acc))
                                     (else (let bfs
                                                ((queue (list (car cells))) (comp (list)))
                                                (cond
                                                  ((null? queue) (loop (cdr cells) (cons comp acc)))
                                                  ((hash-has-key? vis (car queue)) (bfs (cdr queue) comp))
                                                  (else (hash-set! vis (car queue) #t)
                                                        (let* ((r (first (car queue)))
                                                               (c (second (car queue)))
                                                               (nbrs (filter (lambda (n)
                                                                               (and
                                                                                 (hash-has-key? cell-set
                                                                                                n)
                                                                                 (not (hash-has-key? vis
                                                                                                     n))))
                                                                             (list (list (- r
                                                                                            1)
                                                                                         c)
                                                                                   (list (+ r
                                                                                            1)
                                                                                         c)
                                                                                   (list r
                                                                                         (- c
                                                                                            1))
                                                                                   (list r
                                                                                         (+ c
                                                                                            1))))))
                                                          (bfs (append (cdr queue) nbrs)
                                                               (cons (car queue) comp))))))))))
                  (result (make-hash)))
             (for ((comp components))
               (let* ((colors (remove-duplicates (map (lambda (p)
                                                        (at g (first p) (second p)))
                                                      comp)))
                      (c1 (first colors))
                      (c2 (second colors))
                      (c1-cells (filter (lambda (p) (= (at g (first p) (second p)) c1))
                                        comp))
                      (c2-cells (filter (lambda (p) (= (at g (first p) (second p)) c2))
                                        comp))
                      (c1-min-r (min-of first c1-cells))
                      (c2-min-r (min-of first c2-cells))
                      (top-color (if (< c1-min-r c2-min-r) c1 c2))
                      (bot-color (if (< c1-min-r c2-min-r) c2 c1))
                      (top-cells (if (= top-color c1) c1-cells c2-cells))
                      (bot-cells (if (= top-color c1) c2-cells c1-cells)))
                 (for ((p top-cells))
                   (hash-set! result (list (first p) (- (second p) 1)) top-color))
                 (for ((p bot-cells))
                   (hash-set! result (list (first p) (+ (second p) 1)) bot-color))))
             (cellmap g (r c v) (hash-ref result (list r c) bg))))))
