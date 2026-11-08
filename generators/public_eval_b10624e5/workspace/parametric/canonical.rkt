(rule!
 ;; A full blue cross divides yellow panels. Each has a red square; the one
 ;; with additional colored pixels is the source. Scale its decoration by
 ;; each destination/source red-side ratio. Reflect across changed panel axes.
 ;; Preserve red anchors, the source, and dividers; clip to the target panel.
 ;; Inverse lookup uses mathematical floor for negative anchor offsets.
 (lambda (g)
  (let ()
   (define divider-row
    (for/first ((r (in-range h)) #:when (for/and ((c (in-range w))) (= (at g r c) 1))) r))
   (define divider-col
    (for/first ((c (in-range w)) #:when (for/and ((r (in-range h))) (= (at g r c) 1))) c))
   (define bounds
    (list (list 0 0 (- divider-row 1) (- divider-col 1))
          (list 0 (+ divider-col 1) (- divider-row 1) (- w 1))
          (list (+ divider-row 1) 0 (- h 1) (- divider-col 1))
          (list (+ divider-row 1) (+ divider-col 1) (- h 1) (- w 1))))
   (define records
    (for/list ((b bounds))
     (let ((cells (for*/list ((r (in-range (first b) (+ 1 (third b))))
                             (c (in-range (second b) (+ 1 (fourth b))))
                             #:when (= (at g r c) 2)) (list r c))))
      (list b (bbox-of-cells cells)))))
   (define source
    (for/first ((p records) #:when
     (let ((b (first p)))
      (for*/or ((r (in-range (first b) (+ 1 (third b))))
                (c (in-range (second b) (+ 1 (fourth b)))))
        (and (not (= (at g r c) 4)) (not (= (at g r c) 2)))))) p))
   (define sb (first source))
   (define anchor (second source))
   (define source-size (+ 1 (- (third anchor) (first anchor))))
   (define (floor-ratio a b)
    (if (>= a 0) (quotient a b) (- (quotient (+ (- a) (- b 1)) b))))
   (for/fold ((result g)) ((target records) #:when (not (equal? target source)))
    (let* ((b (first target)) (box (second target))
           (k (+ 1 (- (third box) (first box))))
           (flip-y (not (= (first b) (first sb))))
           (flip-x (not (= (second b) (second sb)))))
     (for*/fold ((out result))
       ((r (in-range (first b) (+ 1 (third b))))
        (c (in-range (second b) (+ 1 (fourth b)))))
      (let* ((dr (- r (first box))) (dc (- c (second box)))
             (rr (if flip-y (- k 1 dr) dr))
             (cc (if flip-x (- k 1 dc) dc))
             (sr (+ (first anchor) (floor-ratio (* rr source-size) k)))
             (sc (+ (second anchor) (floor-ratio (* cc source-size) k))))
       (if (and (= (at g r c) 4)
                (<= (first sb) sr (third sb)) (<= (second sb) sc (fourth sb))
                (not (= (at g sr sc) 4)) (not (= (at g sr sc) 2)))
        (set-cell out r c (at g sr sc)) out))))))))
