(rule!
 (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (positions
          (flatmap (lambda (r) (map (lambda (c) (cons r c)) (range 0 w)))
                   (range 0 h))))
   (define (block-color? v) (and (!= v 0) (!= v 8)))
   (define cells
    (filter (lambda (p) (block-color? (at g (fst p) (snd p)))) positions))
   (define colors (unique (map (lambda (p) (at g (fst p) (snd p))) cells)))
   (define (center color)
    (let* ((pts (filter (lambda (p) (= (at g (fst p) (snd p)) color)) cells))
           (n (length pts)))
     (list color
           (/ (for/sum ((p pts)) (fst p)) n)
           (/ (for/sum ((p pts)) (snd p)) n))))
   (define blocks (map center colors))
   (define rows* (sort-by (map second blocks) (lambda (x) x)))
   (define cols* (sort-by (map third blocks) (lambda (x) x)))
   (define mid-r (/ (+ (first rows*) (last rows*)) 2))
   (define mid-c (/ (+ (first cols*) (last cols*)) 2))
   (define (quadrant v mid) (if (<= v mid) 0 1))
   (define summary
    (reduce
     (lambda (out block)
      (set-cell out
                (quadrant (second block) mid-r)
                (quadrant (third block) mid-c)
                (first block)))
     (list (list 0 0) (list 0 0))
     blocks))
   (define bb (bbox-of-cells (find-color g 8)))
   (define hole-count
    (for/sum ((c (in-range (+ (second bb) 1) (+ (second bb) 5))))
     (if (= (at g (first bb) c) 0) 1 0)))
   (define selector (- hole-count 1))
   (define selected
    (at summary (quotient selector 2) (modulo selector 2)))
   (define turns (modulo selected 4))
   (cond ((= turns 0) summary)
         ((= turns 1) (rotate-cw summary))
         ((= turns 2) (rotate-180 summary))
         (else (rotate-ccw summary))))))
