(rule!
 ;; Color 8 is a rectangular occluder. The 4b-2 square is generated from a
 ;; 2b seed mirrored across both far axes; its off-diagonal b-blocks are
 ;; transposes. Recover each hidden cell from its full symmetry orbit.
 (lambda (g)
  (let ()
   (define crop-marker #f)
   (define n (rows g))
   (define b (/ (+ n 2) 4))
   (define axis (+ n 1))
   (define hidden (find-color g 8))
   (define r0 (min-of first hidden))
   (define r1 (max-of first hidden))
   (define c0 (min-of second hidden))
   (define c1 (max-of second hidden))
   (define (inside? p)
    (and (>= (first p) 0) (< (first p) n) (>= (second p) 0) (< (second p) n)))
   (define (mirrors r c)
    (filter inside?
     (list (list r c) (list (- axis r) c) (list r (- axis c))
           (list (- axis r) (- axis c)))))
   (define (orbit r c)
    (let* ((rr (min r (- axis r))) (cc (min c (- axis c)))
           (off-diagonal
            (or (and (< rr b) (>= cc b) (< cc (* 2 b)))
                (and (< cc b) (>= rr b) (< rr (* 2 b))))))
     (if off-diagonal (append (mirrors r c) (mirrors cc rr)) (mirrors r c))))
   (define (recover r c)
    (let ((source
           (first (filter (lambda (p) (!= (at g (first p) (second p)) 8))
                          (orbit r c)))))
     (at g (first source) (second source))))
   (define patch
    (build-list (+ 1 (- r1 r0))
     (lambda (dr)
      (build-list (+ 1 (- c1 c0))
       (lambda (dc) (recover (+ r0 dr) (+ c0 dc)))))))
   (if crop-marker
    (let* ((colors (grid-colors patch))
           (rare
            (for/fold ((best (first colors))) ((color (in-list (rest colors))))
             (if (< (count-color patch color) (count-color patch best)) color best)))
           (cells (find-color patch rare))
           (mr0 (min-of first cells)) (mr1 (max-of first cells))
           (mc0 (min-of second cells)) (mc1 (max-of second cells)))
     (subgrid patch mr0 mc0 mr1 mc1))
    patch))))
