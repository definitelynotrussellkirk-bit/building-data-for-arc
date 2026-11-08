(rule!
  (let ((dummy 0))
    (define (area obj)
      (* (obj-h obj) (obj-w obj)))
    (define (frame-perimeter obj)
      (- (+ (* 2 (obj-h obj)) (* 2 (obj-w obj))) 4))
    (define (border-cell? bbox p)
      (let ((r (first p))
            (c (second p))
            (r1 (first bbox))
            (c1 (second bbox))
            (r2 (third bbox))
            (c2 (fourth bbox)))
        (or (= r r1) (= r r2) (= c c1) (= c c2))))
    (define (rect-frame? obj)
      (let ((bbox (obj-bbox obj)))
        (and (= (obj-color obj) 4)
             (> (obj-h obj) 1)
             (> (obj-w obj) 1)
             (= (obj-size obj) (frame-perimeter obj))
             (all? (lambda (p) (border-cell? bbox p)) (obj-cells obj)))))
    (define frames
      (sort
        (filter rect-frame? (objects g 0))
        (lambda (a b)
          (let ((aa (area a)) (ab (area b)))
            (cond
              [(> aa ab) #t]
              [(< aa ab) #f]
              [(< (obj-r1 a) (obj-r1 b)) #t]
              [(> (obj-r1 a) (obj-r1 b)) #f]
              [else (< (obj-c1 a) (obj-c1 b))])))))
    (define k (count-where (lambda (v) (= v 2)) (row-at g 0)))
    (if (or (empty? frames) (< k 1) (> k (length frames)))
        g
        (let* ((target (nth frames (- k 1)))
               (inner (if (< k (length frames)) (nth frames k) #f))
               (tr1 (obj-r1 target))
               (tc1 (obj-c1 target))
               (tr2 (obj-r2 target))
               (tc2 (obj-c2 target)))
          (grid-from-fn h w
            (lambda (r c)
              (let ((v (cell-at g r c)))
                (if (and (= v 0)
                         (> r tr1) (< r tr2) (> c tc1) (< c tc2)
                         (or (not inner)
                             (not (and (> r (obj-r1 inner)) (< r (obj-r2 inner))
                                       (> c (obj-c1 inner)) (< c (obj-c2 inner))))))
                    8
                    v))))))))