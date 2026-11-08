(rule! (let ((dummy 0))
  (define (t10-alist-ref pairs key default)
    (let ((hits (filter (lambda (p) (= (first p) key)) pairs)))
      (if (empty? hits) default (second (first hits)))))
  (let* ((pairs
           (filter (lambda (p)
                     (and (not (= (first p) 0))
                          (not (= (second p) 0))))
                   (map list (row g 0) (row g 1))))
         (raw-body
           (grid-from-fn (- (rows g) 3) (cols g)
             (lambda (r c) (at g (+ r 3) c))))
         (stage
           (grid-from-fn (- (rows g) 3) (cols g)
             (lambda (r c)
               (let ((v (at g (+ r 3) c)))
                 (t10-alist-ref pairs v v)))))
         (separator-col (second (first (find-color stage 9))))
         (intermediate
           (length
             (filter (lambda (o)
                       (and (= (obj-color o) 1)
                            (< (obj-c2 o) separator-col)))
                     (objects raw-body 0))))
         (payloads
           (sort
             (filter (lambda (o)
                       (and (= (obj-color o) 6)
                            (> (obj-c1 o) separator-col)))
                     (objects stage 0))
             (lambda (a b)
               (or (< (obj-r1 a) (obj-r1 b))
                   (and (= (obj-r1 a) (obj-r1 b))
                        (< (obj-c1 a) (obj-c1 b)))))))
         (target (list-ref payloads (- intermediate 1))))
    (recolor-cells stage (obj-cells target) 8))))
