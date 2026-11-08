(rule!
 ;; Settle first; then select the largest 4-connected liquid pool (row-major ties).
 (lambda (g)
  (let ()
   (define settled ((lambda (g)
  (let ()
   (define (drop a r c)
    (if (= r (- h 1)) a
     (let* ((lo (let left ((x c))
                  (if (and (> x 0) (member (at a r (- x 1)) '(0 1))) (left (- x 1)) x)))
            (hi (let right ((x c))
                  (if (and (< x (- w 1)) (member (at a r (+ x 1)) '(0 1))) (right (+ x 1)) x)))
            (holes (filter (lambda (x) (= (at a (+ r 1) x) 0)) (range lo (+ hi 1)))))
       (if (null? holes) a
        (let ((x (pick-min holes (lambda (x) (abs (- x c))))))
         (drop (set-cell (set-cell a r c 0) (+ r 1) x 1) (+ r 1) x))))))
   (for*/fold ((out g)) ((r (range (- h 2) -1 -1)) (c (range w)))
     (if (= (at out r c) 1) (drop out r c) out)))) g))
   (define liquids (filter (lambda (o) (= (obj-color o) 1)) (objects settled 0)))
   (if (null? liquids) settled
    (let ((winner (obj-cells (pick-max liquids obj-size))))
     (for/fold ((out settled)) ((p (find-color settled 1)))
      (if (member p winner) out (set-cell out (first p) (second p) 0))))))))
