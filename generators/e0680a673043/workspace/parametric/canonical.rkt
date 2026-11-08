(rule!
  (let* ((k (at g 0 0))
         (cmd (at g 0 (- (cols g) 1)))
         (clean (grid-from-fn (rows g) (cols g)
                  (lambda (r c) (if (or (and (= r 0) (= c 0)) (and (= r 0) (= c (- (cols g) 1)))) 0 (at g r c)))))
         (objs (sort (objects clean 0)
                     (lambda (a b)
                       (if (= (obj-size a) (obj-size b))
                           (< (obj-color a) (obj-color b))
                           (> (obj-size a) (obj-size b))))))
         (obj (list-ref objs (- k 1)))
         (crop (grid-from-fn (obj-h obj) (obj-w obj)
                 (lambda (r c)
                   (let ((rr (+ (obj-r1 obj) r)) (cc (+ (obj-c1 obj) c)))
                     (if (member? (list rr cc) (obj-cells obj)) (at clean rr cc) 0))))))
    (cond [(= cmd 1) (rotate-cw crop)]
          [(= cmd 2) (rotate-180 crop)]
          [(= cmd 3) (flip-lr crop)]
          [else (flip-ud crop)])))