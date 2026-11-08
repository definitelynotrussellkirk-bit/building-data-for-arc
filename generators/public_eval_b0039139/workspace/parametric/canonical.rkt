(rule!
 ;; Blue separators delimit template, green markers and two palette panels.
 ;; Normalize vertical layout by transposition. Count the 4-connected green
 ;; objects, crop the yellow template, recolor it and tile along the layout axis.
 ;; One background cell separates neighboring copies.
 (lambda (g)
  (let ()
   (define vertical (= (length (filter (lambda (r) (and (row-uniform? g r) (= (at g r 0) 1))) (range (rows g)))) 3))
   (define t (if vertical (transpose g) g))
   (define separators (filter (lambda (c) (and (col-uniform? t c) (= (at t 0 c) 1))) (range (cols t))))
   (define a (first separators))
   (define b (second separators))
   (define c (third separators))
   (define template (crop-to-content (subgrid t 0 0 (- (rows t) 1) (- a 1)) 0))
   (define markers (subgrid t 0 (+ a 1) (- (rows t) 1) (- b 1)))
   (define parts (filter (lambda (o) (= (obj-color o) 3)) (objects markers 0)))
   (define foreground (at t 0 (+ b 1)))
   (define background (at t 0 (+ c 1)))
   (define tw (cols template))
   (define th (rows template))
   (define sizes (map obj-size parts))
   (define result
    (build-grid th (- (* (length parts) (+ tw 1)) 1) (r col)
      (let* ((copy-index (quotient col (+ tw 1)))
             (offset (modulo col (+ tw 1)))
             (reflect #f))
       (if (= offset tw) background
         (if (= (at template r (if reflect (- tw 1 offset) offset)) 4) foreground background)))))
   (if vertical (transpose result) result))))
