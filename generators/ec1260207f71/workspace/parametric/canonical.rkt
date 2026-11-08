(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define red-cells
               (filter (lambda (p) (= (at g (first p) (second p)) 2))
                       (for*/list ((r (range 0 h)) (c (range 0 w))) (list r c))))
             (define red-by-col (make-hash))
             (for-each (lambda (p)
                         (define c (second p))
                         (hash-set! red-by-col
                                    c
                                    (cons (first p) (hash-ref red-by-col c (list)))))
                       red-cells)
             (define cols-with-red (hash-keys red-by-col))
             (define (segment-info col)
               (define rows-list (sort (hash-ref red-by-col col) <))
               (define start-row (first rows-list))
               (define dots
                 (filter (lambda (p) p)
                         (for/list ((r rows-list))
                           (define dot-col #f)
                           (for ((c (range 0 w)))
                             (when
                               (and (= (at g r c) 8) (not dot-col))
                               (set! dot-col c)))
                           (and dot-col (list (- r start-row) dot-col)))))
               (list col start-row (length rows-list) dots))
             (define seg1 (segment-info (first cols-with-red)))
             (define seg2 (segment-info (second cols-with-red)))
             (define dot-seg (if (empty? (fourth seg1)) seg2 seg1))
             (define plain-seg (if (empty? (fourth seg1)) seg1 seg2))
             (define dot-offsets (map first (fourth dot-seg)))
             (define dot-col-map (make-hash))
             (for-each (lambda (d) (hash-set! dot-col-map (first d) (second d)))
                       (fourth dot-seg))
             (cellmap g
                      (r c __cm_v)
                      (begin
                        (define v __cm_v)
                        (cond
                          ((let* ((seg-col (first dot-seg))
                                  (seg-start (second dot-seg))
                                  (seg-len (third dot-seg))
                                  (offset (- r seg-start)))
                             (and
                               (>= offset 0)
                               (< offset seg-len)
                               (member offset dot-offsets)
                               (let ((dcol (hash-ref dot-col-map offset 0)))
                                 (cond
                                   ((= c dcol) 4)
                                   ((and (< seg-col dcol) (> c seg-col) (< c dcol)) 8)
                                   ((and (> seg-col dcol) (< c seg-col) (> c dcol)) 8)
                                   (else #f))))) =>
                            (lambda (x) x))
                          ((let* ((seg-col (first plain-seg))
                                  (seg-start (second plain-seg))
                                  (seg-len (third plain-seg))
                                  (offset (- r seg-start)))
                             (and
                               (>= offset 0)
                               (< offset seg-len)
                               (member offset dot-offsets)
                               (!= c seg-col)
                               (!= v 2))) 8)
                          (else v))))))))