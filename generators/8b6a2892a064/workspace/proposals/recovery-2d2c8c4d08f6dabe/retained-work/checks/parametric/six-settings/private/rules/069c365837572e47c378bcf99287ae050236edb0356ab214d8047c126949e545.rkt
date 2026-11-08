(rule!
 (lambda (g)
  ;; Orange 7 is the background; four-connected foreground lines are objects.
  ;; Rotate selected odd lines ninety degrees around their integer centers.
  ;; Preserve all other objects, keep colors, and crop target cells at the canvas.
  (let ()
   (define blank (cellmap g (r c v) 7))
   (for/fold ((out blank)) ((o (objects g 7)))
    (let* ((turn? (and (>= (obj-size o) 3) (= (obj-h o) 1)))
           (cr (quotient (+ (obj-r1 o) (obj-r2 o)) 2))
           (cc (quotient (+ (obj-c1 o) (obj-c2 o)) 2)))
     (for/fold ((canvas out)) ((p (obj-cells o)))
      (let* ((rr (if turn? (+ cr (- cc (second p))) (first p)))
             (kc (if turn? (+ cc (- (first p) cr)) (second p))))
       (if (in-bounds? rr kc (rows canvas) (cols canvas))
           (set-cell canvas rr kc (obj-color o))
           canvas))))))))
