(rule!
 ;; Find every orthogonal color-4 plus, group its center by the original
 ;; four-connected color-4 component, select the earliest component containing
 ;; the greatest number of plus centers, and recolor only those plus cells.
 (lambda (g)
  (let ()
   (define (plus-center? r c)
    (and (= (safe-at g r c -1) 4)
         (= (safe-at g (- r 1) c -1) 4)
         (= (safe-at g (+ r 1) c -1) 4)
         (= (safe-at g r (- c 1) -1) 4)
         (= (safe-at g r (+ c 1) -1) 4)))
   (define components (filter (lambda (o) (= (obj-color o) 4)) (objects g 2)))
   (define plus-components
    (filter (lambda (o) (any? (lambda (p) (plus-center? (first p) (second p))) (obj-cells o))) components))
   (define (score o)
    (count-if (lambda (p) (plus-center? (first p) (second p))) (obj-cells o)))
   (define selected (if (null? plus-components) #f (pick-max plus-components score)))
   (define selected-cells (if selected (obj-cells selected) '()))
   (define (selected-center? r c)
    (and (plus-center? r c) (member? (list r c) selected-cells)))
   (define (selected-plus-cell? r c)
    (or (selected-center? r c)
        (selected-center? (- r 1) c)
        (selected-center? (+ r 1) c)
        (selected-center? r (- c 1))
        (selected-center? r (+ c 1))))
   (cellmap g (r c v) (if (and (= v 4) (selected-plus-cell? r c)) 8 v))))))
