(rule!
 ;; Blue cells are finite-volume liquid. All other nonzero cells are fixed solid.
 ;; Settle lower droplets first; a droplet crosses its horizontal fluid/air span
 ;; to the nearest empty cell one row below. Equal distances choose the left.
 ;; Each move descends, so it terminates; canvas edges are impermeable.
 (lambda (g)
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
     (if (= (at out r c) 1) (drop out r c) out)))))
