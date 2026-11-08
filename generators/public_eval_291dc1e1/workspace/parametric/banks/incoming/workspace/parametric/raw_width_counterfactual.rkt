(rule!
 ;; Numbered borders define a two-axis reading order from the zero corner.
 ;; Recover multicolor strips against background 8. Rotate vertical strips CCW.
 ;; COUNTERFACTUAL: correct order/rotation, but jumps use raw pre-rotation widths.
 ;; Center each retained strip in the maximum retained width and stack tightly.
 (lambda (g)
  (let ()
   (define left (= (at g 0 0) 0))
   (define vertical (= (at g 1 (if left 0 (- (cols g) 1))) 1))
   (define body (subgrid g 1 (if left 1 0) (- (rows g) 1) (if left (- (cols g) 1) (- (cols g) 2))))
   (define pieces (objects-multicolor body 8))
   (define (secondary o)
    (if vertical (if left (obj-c1 o) (- (obj-c2 o))) (obj-r1 o)))
   (define (primary o)
    (if vertical (obj-r1 o) (if left (obj-c1 o) (- (obj-c2 o)))))
   (define ordered
    (sort pieces (lambda (a b)
     (or (< (secondary a) (secondary b))
         (and (= (secondary a) (secondary b)) (< (primary a) (primary b)))))))
   (define tiles
    (map (lambda (o)
     (let ((piece (subgrid body (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o))))
      (if vertical (rotate-ccw piece) piece))) ordered))
   (define steps (map (lambda (o) (quotient (obj-w o) 2)) ordered))
   (define indices (let loop ((i 0) (visited '()))
    (if (>= i (length tiles)) (reverse visited)
        (loop (+ i (list-ref steps i)) (cons i visited)))))
   (define chosen (map (lambda (i) (list-ref tiles i)) indices))
   (define width (apply max (map cols chosen)))
   (build-grid (* 2 (length chosen)) width (r c)
    (let* ((tile (list-ref chosen (quotient r 2)))
           (offset (quotient (- width (cols tile)) 2)))
     (if (and (>= c offset) (< c (+ offset (cols tile))))
         (at tile (modulo r 2) (- c offset)) 8))))))
