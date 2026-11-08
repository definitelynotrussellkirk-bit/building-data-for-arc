(rule!
 (lambda (g)
  (define reversed? #t)
  (define h (rows g))
  (define w (cols g))
  (define right? (= (at g 0 (- w 1)) 0))
  (define edge (if right? (- w 1) 0))
  (define horizontal? (= (at g 0 (if right? 0 1)) 1))
  (define mask
   (for/list ([r (in-range h)])
    (for/list ([c (in-range w)])
     (if (and (> r 0) (not (= c edge)) (not (= (at g r c) 8))) 1 0))))
  (define bars
   (for/list ([obj (objects mask 0)])
    (let* ([box (obj-bbox obj)] [r0 (first box)] [c0 (second box)] [r1 (third box)] [c1 (fourth box)]
           [x (if right? (- (- w 1) c1) c0)]
           [tile (if horizontal?
                  (for/list ([r (in-range r0 (+ r1 1))]) (for/list ([c (in-range c0 (+ c1 1))]) (at g r c)))
                  (for/list ([c (in-range c1 (- c0 1) -1)]) (for/list ([r (in-range r0 (+ r1 1))]) (at g r c))))])
     (list (if horizontal? r0 x) (if horizontal? x r0) tile))))
  (define scan-order
   (sort bars (lambda (a b) (or (< (first a) (first b))
                               (and (= (first a) (first b)) (< (second a) (second b)))))))
  (define ordered (if reversed? (reverse scan-order) scan-order))
  (define layout-order ordered)
  (define packing-width (apply max (map (lambda (b) (length (first (third b)))) ordered)))
  (apply append
   (for/list ([bar layout-order])
    (let* ([tile (third bar)] [pad (quotient (- packing-width (length (first tile))) 2)])
     (for/list ([row tile]) (append (make-list pad 8) row (make-list pad 8))))))))
