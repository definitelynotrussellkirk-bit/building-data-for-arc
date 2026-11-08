(rule!
 ;; Recolor every color-4 cell that belongs to an orthogonal five-cell plus.
 ;; A plus is recognized by its color-4 center and four cardinal neighbors;
 ;; diagonal cells and additional connected clutter do not invalidate it.
 (lambda (g)
  (let ()
   (define (plus-center? r c)
    (and (= (safe-at g r c -1) 4)
         (= (safe-at g (- r 1) c -1) 4)
         (= (safe-at g (+ r 1) c -1) 4)
         (= (safe-at g r (- c 1) -1) 4)
         (= (safe-at g r (+ c 1) -1) 4)))
   (define (plus-cell? r c)
    (or (plus-center? r c)
        (plus-center? (- r 1) c)
        (plus-center? (+ r 1) c)
        (plus-center? r (- c 1))
        (plus-center? r (+ c 1))))
   (cellmap g (r c v) (if (and (= v 4) (plus-cell? r c)) 8 v))))))
