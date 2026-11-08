(rule!
 (lambda (g)
  (define h (rows g))
  (define w (cols g))
  (define marker
   (first
    (for*/list ((r (range 2 h))
                (c (range w))
                #:when (= (at g r c) 9))
     (list r c))))
  (define mr (first marker))
  (define mc (second marker))
  (define hit
   (let loop ((c (+ mc 1)))
    (if (>= c w)
        #f
        (let ((v (at g mr c)))
         (if (!= v 0) (list c v) (loop (+ c 1)))))))
  (define relay-color (if hit (second hit) #f))
  (define swatch-col
   (if relay-color
       (find-first (lambda (c) (= (at g (- h 1) c) relay-color)) (range w))
       #f))
  (if swatch-col
      (build-grid h w (r c)
       (if (and (>= r 2) (= c swatch-col)) 9 (at g r c)))
      g)))
