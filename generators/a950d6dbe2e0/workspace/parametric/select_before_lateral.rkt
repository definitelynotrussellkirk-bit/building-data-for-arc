(rule!
 (let ((midr (quotient (rows g) 2))
       (midc (quotient (cols g) 2)))
   (define chosen-before (pick-max (objects g 0) obj-size))
   (define top
     (for*/fold ((out g)) ((r (in-range midr)) (c (in-range midc)))
       (let ((v (at g r c)))
         (if (= v 0)
             out
             (set-cell out r (- (cols g) 1 c) v)))))
   (define carried
     (append
      (obj-cells chosen-before)
      (map (lambda (p) (list (first p) (- (cols g) 1 (second p))))
           (obj-cells chosen-before))))
   (for/fold ((out top)) ((p (in-list carried)))
     (let ((r (first p)) (c (second p)))
       (set-cell out (- (rows g) 1 r) c (at top r c))))))
