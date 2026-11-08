(rule!
 ;; The magenta baseline intersects solid cyan-background bars.
 ;; Measure each bar's vertical height; keep its color, width and column span.
 ;; Reassign the sorted height multiset from left to right, centered on the
 ;; original baseline (even heights extend one cell farther upward). Equal heights retain multiplicity; colors may repeat.
 (lambda (g)
  (let ()
   (define height (rows g))
   (define width (cols g))
   (define axis (for/first ((r (range height)) #:when (member 6 (list-ref g r))) r))
   (define bars
    (for/list ((c (range width))
      #:when (and (not (member (at g axis c) '(6 8)))
                  (or (= c 0) (not (= (at g axis c) (at g axis (- c 1)))))))
     (let* ((color (at g axis c))
            (end (or (for/first ((j (range (+ c 1) width)) #:when (not (= (at g axis j) color))) j) width))
            (length (for/sum ((r (range height))) (if (= (at g r c) color) 1 0))))
       (list c end color length))))
   (define lengths (sort (map fourth bars) <))
   (define blank (for/list ((r (range height)))
                  (for/list ((c (range width))) (if (= r axis) 6 8))))
   (for/fold ((out blank)) ((bar bars) (length lengths))
    (for*/fold ((canvas out)) ((r (range (- axis (quotient length 2)) (+ (- axis (quotient length 2)) length)))
                               (c (range (first bar) (second bar))))
      (set-cell canvas r c (third bar)))))))
