(rule!
 ;; Reconstruct solid or alternating rectangular outlines behind the largest
 ;; green WINDOW; smaller green frames are decoys. Crop the window interior.
 ;; Compatibility convention: start each hidden patterned outline with its
 ;; lower palette color in row-major order. The supplied third example has
 ;; eight cells incompatible with simple visible-border phase continuation.
 (lambda (g)
  (let ()
   (define restart-hidden? #t)
   (define (within? p bb)
    (and (<= (first bb) (first p) (third bb)) (<= (second bb) (second p) (fourth bb))))
   (define (border bb)
    (filter (lambda (p) (or (= (first p) (first bb)) (= (first p) (third bb))
                            (= (second p) (second bb)) (= (second p) (fourth bb))))
            (apply positions-in-rect bb)))
   (define background (mode-list (map (lambda (p) (at g (first p) (second p))) (border (list 0 0 (- h 1) (- w 1))))))
   (define green-mask (cellmap g (r c v) (if (= v 3) 3 -1)))
   (define frames
    (filter (lambda (bb) (and (>= (- (third bb) (first bb)) 2) (>= (- (fourth bb) (second bb)) 2)
                              (andmap (lambda (p) (= (at g (first p) (second p)) 3)) (border bb))))
            (map obj-bbox (objects green-mask -1))))
   (define frame (pick-max frames (lambda (bb) (* (+ 1 (- (third bb) (first bb))) (+ 1 (- (fourth bb) (second bb)))))))
   (define window (list (+ 1 (first frame)) (+ 1 (second frame)) (- (third frame) 1) (- (fourth frame) 1)))
   (define exposed (cellmap g (r c v) (if (ormap (lambda (bb) (within? (list r c) bb)) frames) background v)))
   (define fragments (objects-multicolor exposed background))
   (define palettes (map (lambda (o) (unique (map (lambda (p) (at g (first p) (second p))) (obj-cells o)))) fragments))
   (define (closure colors)
    (for/fold ((current colors)) ((iteration (in-range 10)))
     (unique (append current (apply append (filter (lambda (p) (ormap (lambda (v) (member v current)) p)) palettes))))))
   (define groups (remove-duplicates (map (lambda (v) (closure (list v))) (grid-colors exposed background))))
   (define records
    (for/list ((palette (in-list groups)))
     (define cells (filter (lambda (p) (member (at exposed (first p) (second p)) palette)) (grid-positions exposed)))
     (define bb (bbox-of-cells cells))
     (define hidden (filter (lambda (p) (within? p window)) (border bb)))
     (list palette cells hidden)))
   (define base (apply subgrid g window))
   (for/fold ((out base)) ((record (in-list records)) #:unless (null? (third record)))
    (define palette (first record))
    (define visible (second record))
    (define hidden (third record))
    (define origin (+ (first (first hidden)) (second (first hidden))))
    (for/fold ((acc out)) ((p (in-list hidden)))
     (define parity (modulo (+ (first p) (second p)) 2))
     (define witnesses (filter (lambda (q) (= (modulo (+ (first q) (second q)) 2) parity)) visible))
     (define color
      (if restart-hidden?
       (list-ref palette (modulo (- (+ (first p) (second p)) origin) (length palette)))
       (mode-list (map (lambda (q) (at g (first q) (second q))) (if (null? witnesses) visible witnesses)))))
     (set-cell acc (- (first p) (first window)) (- (second p) (second window)) color))))))
