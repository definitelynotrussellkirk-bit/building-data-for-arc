(rule!
 ;; Install each orange 777 bridge as 868, with magenta on the strip cells
 ;; immediately above and below its center. Cyan four-neighbor paths result.
 ;; Count each path's original green tokens and pack them inward from its lower
 ;; endpoint. Equal-height endpoints keep their original token locations.
 (lambda (g)
  (let ()
   (define (install base)
    (for*/fold ((out base)) ((r (range 1 (- h 1))) (c (range 1 (- w 1))))
     (if (and (= (at g r (- c 1)) 7) (= (at g r c) 7) (= (at g r (+ c 1)) 7))
      (set-cell (set-cell (set-cell (set-cell (set-cell out r (- c 1) 8) r c 6) r (+ c 1) 8) (- r 1) c 6) (+ r 1) c 6)
      out)))
   (define (adj p cells)
    (filter (lambda (q) (member q cells))
     (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) cardinal-deltas)))
   (define (pack network)
    (for/fold ((out network)) ((o (filter (lambda (o) (= (obj-color o) 8)) (objects network 0))))
     (let* ((cells (obj-cells o))
            (tokens (filter (lambda (p) (= (at g (first p) (second p)) 3)) cells))
            (ends (filter (lambda (p) (<= (length (adj p cells)) 1)) cells))
            (level (if (null? ends) 0 (apply max (map first ends))))
            (chosen (filter (lambda (p) (= (first p) level)) ends)))
      (if (or (null? tokens) (not (= (length chosen) 1)))
       (recolor-cells out tokens 3)
       (let walk ((a out) (p (first chosen)) (previous '()) (remaining (length tokens)))
        (if (= remaining 0) a
         (let* ((painted (set-cell a (first p) (second p) 3))
                (next (filter (lambda (q) (not (equal? q previous))) (adj p cells))))
          (if (null? next) painted (walk painted (first next) p (- remaining 1))))))))))
   (pack (install (recolor g 3 8))))))
