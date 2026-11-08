(rule!
 ;; Every cyan(8) object is repainted by REGION within its own bbox: an
 ;; interior belt (inset t = max(2, min(h,w)/4)) turns 4; the remaining ring
 ;; splits by bbox quadrant — top-left 6, top-right 1, bottom-left 2,
 ;; bottom-right 3.
 (lambda (g)
   (let ()
     (define (paint-object out obj)
       (let* ((r1 (obj-r1 obj))
              (c1 (obj-c1 obj))
              (hh (obj-h obj))
              (ww (obj-w obj))
              (t (max 2 (quotient (min hh ww) 3))))
         (for/fold ((acc out)) ((p (obj-cells obj)))
           (let* ((rr (- (first p) r1))
                  (cc (- (second p) c1))
                  (color (cond ((and (>= rr t) (< rr (- hh t))
                                     (>= cc t) (< cc (- ww t))) 4)
                               ((and (< (* 2 rr) hh) (< (* 2 cc) ww)) 6)
                               ((< (* 2 rr) hh) 1)
                               ((< (* 2 cc) ww) 2)
                               (else 3))))
             (set-cell acc (first p) (second p) color)))))
     (for/fold ((out g)) ((obj (filter (lambda (o) (= (obj-color o) 8))
                                       (objects g 0))))
       (paint-object out obj)))))