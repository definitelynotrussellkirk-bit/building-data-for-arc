(rule!
  (let ((dummy 0))
    (define (rect-frame? obj)
      (let ((border
              (remove-duplicates
                (append
                  (for/list ([c (in-range (obj-c1 obj) (+ (obj-c2 obj) 1))]) (list (obj-r1 obj) c))
                  (for/list ([c (in-range (obj-c1 obj) (+ (obj-c2 obj) 1))]) (list (obj-r2 obj) c))
                  (for/list ([r (in-range (obj-r1 obj) (+ (obj-r2 obj) 1))]) (list r (obj-c1 obj)))
                  (for/list ([r (in-range (obj-r1 obj) (+ (obj-r2 obj) 1))]) (list r (obj-c2 obj)))))))
        (and (= (obj-size obj) (length border))
             (all? (lambda (p) (member? p border)) (obj-cells obj)))))
    (define (square-frame? obj)
      (and (rect-frame? obj)
           (= (- (obj-r2 obj) (obj-r1 obj))
              (- (obj-c2 obj) (obj-c1 obj)))))
    (define rects (filter square-frame? (objects g 0)))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (if (= (at g r c) 0)
            0
            (+ 1
               (count-where
                 (lambda (obj)
                   (and (>= r (obj-r1 obj)) (<= r (obj-r2 obj))
                        (>= c (obj-c1 obj)) (<= c (obj-c2 obj))))
                 rects)))))))
