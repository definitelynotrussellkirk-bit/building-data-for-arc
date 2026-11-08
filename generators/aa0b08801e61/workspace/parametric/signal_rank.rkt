(rule!
  (let ((dummy 0))
    (define (mask obj)
      (let ((crop (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj))))
        (grid-from-fn (rows crop) (cols crop)
          (lambda (r c) (if (not (= (at crop r c) 0)) 1 0)))))
    (define (v-sym? m) (equal? m (flip-lr m)))
    (define (h-sym? m) (equal? m (flip-ud m)))
    (define (class-color obj)
      (let* ((m (mask obj))
             (vs (v-sym? m))
             (hs (h-sym? m)))
        (if (and vs hs) 8 (if vs 2 (if hs 3 4)))))
    (let* ([objs (objects g 0)]
           [signal (find-first (lambda (obj) (= (obj-color obj) 1)) objs)]
           [rank (obj-size signal)]
           [payloads (filter (lambda (obj) (!= (obj-color obj) 1)) objs)]
           [chosen (list-ref payloads (- rank 1))])
      (paint-cells (empty-grid (rows g) (cols g) 0)
                   (obj-cells chosen)
                   (class-color chosen)))))
