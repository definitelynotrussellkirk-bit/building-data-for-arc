(rule!
 (let ((midr (quotient (rows g) 2))
       (midc (quotient (cols g) 2)))
   (define top
     (for*/fold ((out g)) ((r (in-range midr)) (c (in-range midc)))
       (let ((v (at g r c)))
         (if (= v 0)
             out
             (set-cell out r (- (cols g) 1 c) v)))))
   (define chosen (pick-max (objects top 0) obj-size))
   (for/fold ((out top)) ((p (in-list (obj-cells chosen))))
     (let ((r (first p)) (c (second p)))
       (set-cell out (- (rows g) 1 r) c (at top r c))))))
