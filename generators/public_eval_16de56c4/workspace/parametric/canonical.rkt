(rule!
 ;; Find the common source edge. Every active line has two same-color seeds,
 ;; the first on that edge, and optionally one later different-color marker.
 ;; The seed separation defines a periodic lattice extending inward.
 ;; Only a marker on the lattice is hit: recolor the whole run to its color
 ;; and stop there. Off-lattice markers remain unchanged and do not stop it.
 ;; The alternate extent preserves the hit color but continues to the edge.
 (lambda (g)
   (let ()
     (define height (rows g))
     (define width (cols g))
     (define continue-after-hit #f)
     (define (line-values side index)
       (cond ((= side 0) (row g index))
             ((= side 1) (reverse (row g index)))
             ((= side 2) (col g index))
             (else (reverse (col g index)))))
     (define (count-lines side) (if (< side 2) height width))
     (define (occupied values)
       (filter (lambda (i) (> (list-ref values i) 0)) (range 0 (length values))))
     (define (valid-edge? side)
       (and
         (for/or ((i (range 0 (count-lines side)))) (not (null? (occupied (line-values side i)))))
         (for/and ((i (range 0 (count-lines side))))
           (let* ((values (line-values side i)) (ps (occupied values)))
             (or (null? ps)
                 (and (or (= (length ps) 2) (= (length ps) 3))
                      (= (first ps) 0)
                      (= (list-ref values (first ps)) (list-ref values (second ps)))
                      (or (= (length ps) 2)
                          (not (= (list-ref values (third ps)) (list-ref values (first ps)))))))))))
     (define side (first (filter valid-edge? (range 0 4))))
     (define line-length (if (< side 2) width height))
     (define (position line offset)
       (cond ((= side 0) (list line offset))
             ((= side 1) (list line (- width 1 offset)))
             ((= side 2) (list offset line))
             (else (list (- height 1 offset) line))))
     (for/fold ((out g)) ((line (range 0 (count-lines side))))
       (let* ((values (line-values side line)) (ps (occupied values)))
         (if (null? ps) out
             (let* ((spacing (second ps))
                    (seed-color (first values))
                    (marker (if (= (length ps) 3) (third ps) #f))
                    (hit (and marker (= (modulo marker spacing) 0) marker))
                    (ink (if hit (list-ref values hit) seed-color))
                    (end (if (and hit (not continue-after-hit)) hit (- line-length 1)))
                    (points (for/list ((offset (range 0 (+ end 1) spacing))) (position line offset))))
               (recolor-cells out points ink))))))))
