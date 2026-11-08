(rule!
 (lambda (g)
  (let ()
   (define (key-at r c)
    (if
     (and
      (for/and ((j (range 0 4))) (= (at g (+ r 3) (+ c j)) 3))
      (for/and ((i (range 0 4))) (= (at g (+ r i) (+ c 3)) 3)))
     (let ((markers
            (for*/list ((i (range 0 3)) (j (range 0 3))
              #:when (!= (at g (+ r i) (+ c j)) 7))
             (at g (+ r i) (+ c j)))))
      (if
       (and (= (length markers) 3)
            (= (length (remove-duplicates markers)) 3)
            (for/and ((v markers)) (and (!= v 0) (!= v 3) (!= v 7))))
       (list r c markers)
       #f))
     #f))
   (define key-candidates
    (filter
     (lambda (x) x)
     (for*/list ((r (range 0 (- (rows g) 3)))
                 (c (range 0 (- (cols g) 3))))
      (key-at r c))))
   (define key (first key-candidates))
   (define kr (first key))
   (define kc (second key))
   (define key-colors (third key))
   (define (inside-key? p)
    (and (<= kr (first p)) (< (first p) (+ kr 4))
         (<= kc (second p)) (< (second p) (+ kc 4))))
   (define panels
    (filter
     (lambda (o)
      (and (= (obj-size o) (* (obj-h o) (obj-w o)))
           (for/and ((p (obj-cells o))) (not (inside-key? p)))))
     (objects-multicolor g 7)))
   (define (panel-colors o)
    (remove-duplicates
     (map
      (lambda (p) (at g (first p) (second p)))
      (filter (lambda (p) (!= (at g (first p) (second p)) 0))
              (obj-cells o)))))
   (define (missing o)
    (count-if (lambda (v) (not (member v (panel-colors o)))) key-colors))
   (for/fold ((out g)) ((o panels))
    (if (= (missing o) 0) (paint-cells out (obj-cells o) 7) out)))))
