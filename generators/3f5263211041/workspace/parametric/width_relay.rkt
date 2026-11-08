(rule!
 ;; A LIBRARY of maroon(9)-framed patterns, each keyed by the color dot in
 ;; the row ABOVE its frame. The second-to-last grid row lists the keys to
 ;; SELECT, in order; the last row lists a transform per pick (5 = keep,
 ;; 6 = rotate-cw, 7 = flip-lr). The picked, transformed patterns line up
 ;; horizontally (vertically centered, 1-col gaps).
 (lambda (g)
   (let ()
     (define (crop-nonzero grid)
       (let ((cells (filter (lambda (p) (!= (at grid (first p) (second p)) 0))
                            (grid-positions grid))))
         (if (empty? cells)
             (list (list 0))
             (let ((bb (bbox-of-cells cells)))
               (subgrid grid (first bb) (second bb) (third bb) (fourth bb))))))
     (define (rect-frame? obj)
       ;; exactly the border of a >=3x3 bbox: every cell on the border AND
       ;; the cell count equals the perimeter
       (let* ((bb (obj-bbox obj))
              (hh (+ 1 (- (third bb) (first bb))))
              (ww (+ 1 (- (fourth bb) (second bb)))))
         (and (>= hh 3) (>= ww 3)
              (= (obj-size obj) (- (* 2 (+ hh ww)) 4))
              (all? (lambda (p) (or (= (first p) (first bb))
                                    (= (first p) (third bb))
                                    (= (second p) (second bb))
                                    (= (second p) (fourth bb))))
                    (obj-cells obj)))))
     (define frames
       ;; library frames only — anything reaching the two control rows at
       ;; the bottom is not a library entry
       (sort (filter (lambda (o) (and (= (obj-color o) 9)
                                      (rect-frame? o)
                                      (< (third (obj-bbox o)) (- (rows g) 3))))
                     (objects g 0))
             (lambda (a b)
               (let ((ba (obj-bbox a)) (bb (obj-bbox b)))
                 (or (< (first ba) (first bb))
                     (and (= (first ba) (first bb))
                          (< (second ba) (second bb))))))))
     (define (key-above fr)
       (let ((bb (obj-bbox fr)))
         (first (filter (lambda (v) (not (member? v (list 0 9))))
                        (map (lambda (c) (at g (- (first bb) 1) c))
                             (range (second bb) (+ (fourth bb) 1)))))))
     (define (pattern-of fr)
       (let ((bb (obj-bbox fr)))
         (crop-nonzero (subgrid g (+ (first bb) 1) (+ (second bb) 1)
                               (- (third bb) 1) (- (fourth bb) 1)))))
     (define library (map (lambda (fr) (list (key-above fr) (pattern-of fr)))
                          frames))
     (define (lookup k)
       (second (first (filter (lambda (kv) (= (first kv) k)) library))))
     (define selectors
       (filter (lambda (v)
                 (not (empty? (filter (lambda (kv) (= (first kv) v))
                                      library))))
               (row g (- (rows g) 2))))
     (define transforms (filter (lambda (v) (member? v (list 5 6 7)))
                                (last g)))
     (define parts
       (let loop ((ks selectors) (ts transforms) (acc (list)))
         (if (or (empty? ks) (empty? ts))
             (reverse acc)
             (loop (rest ks) (rest ts)
                   (cons (cond ((= (first ts) 6) (rotate-cw (lookup (first ks))))
                               ((= (first ts) 7) (flip-lr (lookup (first ks))))
                               (else (lookup (first ks))))
                         acc)))))
     (define (hstack-center pieces)
       (if (empty? pieces)
           (list (list))
           (let* ((hh (apply max (map rows pieces)))
                  (ww (+ (apply + (map cols pieces)) (- (length pieces) 1))))
             (let loop ((xs pieces) (left 0) (out (empty-grid hh ww 0)))
               (if (empty? xs)
                   out
                   (let ((piece (first xs)))
                     (loop (rest xs) (+ left (cols piece) 1)
                           (paste out piece
                                  (quotient (- hh (rows piece)) 2)
                                  left))))))))
     ;; The first transformed piece is A.  Its width (2 or 3) selects
     ;; the second or third payload instruction; the first payload is a distractor.
     (define control (first parts))
     (define payloads (rest parts))
     (define relay-width (cols control))
     (define chosen (list-ref payloads (- relay-width 1)))
     (hstack-center (list control chosen)))))