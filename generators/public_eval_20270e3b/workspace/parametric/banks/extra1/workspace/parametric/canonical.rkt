(rule!
 ;; The two 8-connected yellow/orange pieces dock without rotation.
 ;; Translate the second so the complete orange patterns sit one cardinal cell
 ;; apart, each orange port covered by the other piece's yellow material.
 ;; Yellow cells must not overlap; the crop must fit within 30x30.
 ;; Erase orange ports and crop the assembly.
 (lambda (g)
  (let ()
   (define parts (objects-multicolor g 1))
   (define ca (obj-cells (first parts)))
   (define cb (obj-cells (second parts)))
   (define (colored cells color)
    (sort (filter (lambda (p) (= (at g (first p) (second p)) color)) cells) cell<))
   (define sa (colored ca 4))
   (define sb (colored cb 4))
   (define ma (colored ca 7))
   (define mb (colored cb 7))
   (define (shift cells delta)
    (map (lambda (p) (list (+ (first p) (first delta)) (+ (second p) (second delta)))) cells))
   (define anchor (first ma))
   (define other (first mb))
   (define candidates
    (for/list ((normal cardinal-deltas)
      #:when
      (let* ((delta (list (+ (- (first anchor) (first other)) (first normal))
                         (+ (- (second anchor) (second other)) (second normal))))
             (moved (shift sb delta))
             (moved-marks (shift mb delta))
             (candidate-box (bbox-of-cells (append sa moved))))
       (and (<= (+ 1 (- (third candidate-box) (first candidate-box))) 30)
            (<= (+ 1 (- (fourth candidate-box) (second candidate-box))) 30)
            (equal? (sort moved-marks cell<) (sort (shift ma normal) cell<))
            (all? (lambda (p) (member p moved)) ma)
            (all? (lambda (p) (member p sa)) moved-marks)
            (not (any? (lambda (p) (member p sa)) moved)))))
     (list (+ (- (first anchor) (first other)) (first normal))
           (+ (- (second anchor) (second other)) (second normal)))))
   (define delta (first candidates))
   (define combined (append sa (shift sb delta)))
   (define box (bbox-of-cells combined))
   (define canvas
    (build-grid (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box))) (r c)
     (if (member (list (+ r (first box)) (+ c (second box))) combined) 4 1)))
   
   canvas)))
