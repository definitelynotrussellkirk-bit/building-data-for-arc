(rule!
 ;; The gray table has square top templates, middle layout fragments and
 ;; bottom recoloring swatches. Overlay the middle fragments; each nonzero
 ;; layout cell selects its source-color template, recolored by that template's
 ;; bottom legend. Default stamps as drawn; the alternative rotates each tile.
 (lambda (g)
  (let ()
   (define n (for/first ((c (in-range w)) #:when (= (at g 0 c) 5)) c))
   (define starts
    (filter (lambda (x)
     (for*/or ((r (in-range n)) (c (in-range n)))
      (and (not (= (at g r (+ x c)) 0)) (not (= (at g r (+ x c)) 5)))))
     (range 0 (+ (- w n) 1) (+ n 1))))
   (define templates
    (for/list ((x starts))
     (let* ((source (for*/first ((r (in-range n)) (c (in-range n))
                       #:when (not (= (at g r (+ x c)) 0))) (at g r (+ x c))))
            (target (for*/first ((r (in-range (+ (* 2 n) 2) h)) (c (in-range n))
                       #:when (and (not (= (at g r (+ x c)) 0))
                                   (not (= (at g r (+ x c)) 5)))) (at g r (+ x c))))
            (offsets (for*/list ((r (in-range n)) (c (in-range n))
                         #:when (= (at g r (+ x c)) source)) (list r c))))
       (list source target offsets))))
   (define layout
    (build-grid n n (r c)
     (let ((v (for/first ((x starts) #:when (not (= (at g (+ n 1 r) (+ x c)) 0)))
                (at g (+ n 1 r) (+ x c))))) (if v v 0))))
   (for*/fold ((out (build-grid (* n n) (* n n) (r c) 0)))
               ((r (in-range n)) (c (in-range n)) #:when (not (= (at layout r c) 0)))
    (let* ((entry (for/first ((t templates) #:when (= (first t) (at layout r c))) t))
           (offsets (for*/list ((rr (in-range n)) (cc (in-range n))) (list rr cc))))
     (for/fold ((result out)) ((p offsets))
      (let ((rr (second p)) (cc (- n 1 (first p))))
       (set-cell result (+ (* r n) rr) (+ (* c n) cc) (second entry)))))))))
