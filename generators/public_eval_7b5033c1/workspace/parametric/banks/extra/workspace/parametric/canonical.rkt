(rule!
 ;; The modal background surrounds one nonbranching four-neighbor colored path.
 ;; Start at the row-major smaller endpoint, follow the path through its bends,
 ;; and put each visited color in the next row of a one-column output. Repeated
 ;; colors remain in their original path positions, not pooled into a histogram.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define cells (for*/list ((r (range (rows g))) (c (range (cols g)))
                            #:when (not (= (at g r c) bg))) (list r c)))
   (define (adjacent? p q)
    (= (+ (abs (- (first p) (first q))) (abs (- (second p) (second q)))) 1))
   (define (neighbors p) (filter (lambda (q) (adjacent? p q)) cells))
   (define endpoints (filter (lambda (p) (= (length (neighbors p)) 1)) cells))
   (define route
    (let walk ((p (first endpoints)) (seen '()))
     (define next (filter (lambda (q) (not (member q seen))) (neighbors p)))
     (cons p (if (null? next) '() (walk (first next) (cons p seen))))))
   (define trace-mode 'path)
   (define ordered
    (cond ((equal? trace-mode 'row_major) cells)
          ((equal? trace-mode 'column_major)
           (sort cells (lambda (p q) (< (+ (* (second p) (rows g)) (first p))
                                       (+ (* (second q) (rows g)) (first q))))))
          ((equal? trace-mode 'reverse) (reverse route))
          (else route)))
   (define raw-sequence (map (lambda (p) (at g (first p) (second p))) ordered))
   (define sequence (if (equal? trace-mode 'histogram) (sort raw-sequence <) raw-sequence))
   (define runs
    (let group ((remaining sequence) (current '()) (done '()))
     (cond ((null? remaining) (reverse (if (null? current) done (cons current done))))
           ((or (null? current) (= (first remaining) (first current)))
            (group (rest remaining) (cons (first remaining) current) done))
           (else (group (rest remaining) (list (first remaining)) (cons current done))))))
   (define finish 'unroll)
   (define selector 'header)
   (define paint-mode 'run)
   (define address
    (cond ((number? selector) selector)
          ((equal? selector 'last) (- (length runs) 1))
          ((equal? selector 'largest)
           (if (> (length runs) 1)
             (first (sort (range 1 (length runs))
                      (lambda (i j) (> (length (nth runs i)) (length (nth runs j)))))) 0))
          (else (length (first runs)))))
   (define selected-color (if (< address (length runs)) (first (nth runs address)) -1))
   (if (equal? finish 'unroll)
       (map list sequence)
       (apply append
        (for/list ((run runs) (i (range (length runs))))
         (for/list ((color run))
          (list (if (or (= i address)
                        (and (equal? paint-mode 'all_matching) (= color selected-color))) 9 color)))))))))
