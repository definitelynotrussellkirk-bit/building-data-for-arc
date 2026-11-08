(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define (zero-row? r) (all? (lambda (c) (zero? (at g r c))) (range 0 w)))
             (define (zero-col? c) (all? (lambda (r) (zero? (at g r c))) (range 0 h)))
             (define rstarts
               (filter (lambda (r)
                         (and (not (zero-row? r)) (or (zero? r) (zero-row? (- r 1)))))
                       (range 0 h)))
             (define cstarts
               (filter (lambda (c)
                         (and (not (zero-col? c)) (or (zero? c) (zero-col? (- c 1)))))
                       (range 0 w)))
             (define (row-end s)
               (let ((zs (filter (lambda (r) (zero-row? r)) (range s h))))
                 (if (null? zs) (- h 1) (- (first zs) 1))))
             (define (col-end s)
               (let ((zs (filter (lambda (c) (zero-col? c)) (range s w))))
                 (if (null? zs) (- w 1) (- (first zs) 1))))
             (define bh (+ 1 (- (row-end (first rstarts)) (first rstarts))))
             (define bw (+ 1 (- (col-end (first cstarts)) (first cstarts))))
             (define row-idxs (range 0 (length rstarts)))
             (define col-idxs (range 0 (length cstarts)))
             (define interior-vals
               (flatmap (lambda (i)
                          (flatmap (lambda (j)
                                     (flatmap (lambda (dr)
                                                (map (lambda (dc)
                                                       (at g
                                                           (+ (nth rstarts i) dr)
                                                           (+ (nth cstarts j) dc)))
                                                     (range 1 (- bw 1))))
                                              (range 1 (- bh 1))))
                                   col-idxs))
                        row-idxs))
             (define common (mode-list interior-vals))
             (define colors
               (filter (lambda (v) (and (!= v 0) (!= v common))) (grid-colors g)))
             (define (has-special? color dr dc i j)
               (= (at g (+ (nth rstarts i) dr) (+ (nth cstarts j) dc)) color))
             (define (paint-row acc color dr dc i)
               (let ((js (filter (lambda (j) (has-special? color dr dc i j)) col-idxs)))
                 (if (< (length js) 2)
                     acc
                     (reduce (lambda (a j)
                               (set-cell a
                                         (+ (nth rstarts i) dr)
                                         (+ (nth cstarts j) dc)
                                         color))
                             acc
                             (range (min-list js) (+ (max-list js) 1))))))
             (define (paint-col acc color dr dc j)
               (let ((is (filter (lambda (i) (has-special? color dr dc i j)) row-idxs)))
                 (if (< (length is) 2)
                     acc
                     (reduce (lambda (a i)
                               (set-cell a
                                         (+ (nth rstarts i) dr)
                                         (+ (nth cstarts j) dc)
                                         color))
                             acc
                             (range (min-list is) (+ (max-list is) 1))))))
             (reduce (lambda (acc color)
                       (reduce (lambda (a dr)
                                 (reduce (lambda (a2 dc)
                                           (let ((a3 (reduce (lambda (x i)
                                                               (paint-row x
                                                                          color
                                                                          dr
                                                                          dc
                                                                          i))
                                                             a2
                                                             row-idxs)))
                                             (reduce (lambda (x j)
                                                       (paint-col x color dr dc j))
                                                     a3
                                                     col-idxs)))
                                         a
                                         (range 1 (- bw 1))))
                               acc
                               (range 1 (- bh 1))))
                     g
                     colors)))))