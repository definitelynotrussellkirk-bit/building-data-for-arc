(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define bg (mode g -1))
             (define objs (objects-8 g bg))
             (define (cell-in? cells r c) (member (list r c) cells))
             (define (neighbor-count cells p)
               (for/sum ((d all-8-deltas))
                 (if (cell-in? cells (+ (first p) (first d)) (+ (second p) (second d)))
                     1
                     0)))
             (define (line-endpoints obj)
               (let ((cells (obj-cells obj)))
                 (filter (lambda (p) (= (neighbor-count cells p) 1)) cells)))
             (define line-obj
               (find-first (lambda (obj)
                             (and
                               (> (obj-size obj) 1)
                               (= (length (line-endpoints obj)) 2)))
                           objs))
             (define line-color (obj-color line-obj))
             (define stamp-color
               (find-first (lambda (c) (!= c line-color)) (grid-colors g bg)))
             (define stamp-objs
               (filter (lambda (obj) (= (obj-color obj) stamp-color)) objs))
             (define source-stamp-cells (normalize-cells (obj-cells (first stamp-objs))))
             (define dilation-deltas
               (list (list 0 0) (list 1 0) (list -1 0) (list 0 1) (list 0 -1)))
             (define stamp-cells
               (normalize-cells
                 (remove-duplicates
                   (for*/list ((p source-stamp-cells) (d dilation-deltas))
                     (list (+ (first p) (first d))
                           (+ (second p) (second d)))))))
             (define stamp-bb (bbox-of-cells stamp-cells))
             (define stamp-cr (quotient (+ (first stamp-bb) (third stamp-bb)) 2))
             (define stamp-cc (quotient (+ (second stamp-bb) (fourth stamp-bb)) 2))
             (define endpoints (line-endpoints line-obj))
             (define centers
               (map (lambda (obj)
                      (list (quotient (+ (obj-r1 obj) (obj-r2 obj)) 2)
                            (quotient (+ (obj-c1 obj) (obj-c2 obj)) 2)))
                    stamp-objs))
             (define network
               (for*/fold ((acc (empty-grid h w bg)))
                          ((i (range 0 (length centers))) (j (range (+ i 1) (length centers))))
                          (let ((a (list-ref centers i))
                                (b (list-ref centers j)))
                            (draw-line acc
                                       (first a)
                                       (second a)
                                       (first b)
                                       (second b)
                                       line-color))))
             (foldl (lambda (endpoint acc)
                      (foldl (lambda (p acc2)
                               (let ((nr (+ (first endpoint) (- (first p) stamp-cr)))
                                     (nc (+ (second endpoint) (- (second p) stamp-cc))))
                                 (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                                     (set-cell acc2 nr nc stamp-color)
                                     acc2)))
                             acc
                             stamp-cells))
                    network
                    endpoints)))))