(rule!
 (lambda (g)
  (define h (rows g))
  (define w (cols g))
  (define color
   (find-first (lambda (v) (!= v 0)) (grid-colors g)))
  (define marker
   (first
    (for*/list ((r (range h))
                (c (range w))
                #:when (!= (at g r c) 0))
     (list r c))))
  (define mr (first marker))
  (define mc (second marker))
  (define dr
   (cond ((or (= color 1) (= color 5) (= color 9)) -1)
         ((or (= color 3) (= color 7)) 1)
         (else 0)))
  (define dc
   (cond ((or (= color 2) (= color 6)) 1)
         ((or (= color 4) (= color 8)) -1)
         (else 0)))
  (define hit
   (let loop ((r (+ mr dr)) (c (+ mc dc)))
    (if (or (< r 0) (>= r h) (< c 0) (>= c w))
        #f
        (if (!= (at g r c) 0)
            (list r c)
            (loop (+ r dr) (+ c dc))))))
  (if hit
      (let ((hr (first hit)) (hc (second hit)))
       (build-grid h w (r c)
        (if
         (cond ((= hr 0) (and (= r 0) (>= c hc)))
               ((= hc (- w 1)) (and (= c (- w 1)) (>= r hr)))
               ((= hr (- h 1)) (and (= r (- h 1)) (<= c hc)))
               (else (and (= c 0) (<= r hr))))
         8
         (at g r c))))
      g)))
