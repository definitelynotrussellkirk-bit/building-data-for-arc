(rule! (let ((dummy 0))
  (define seen (make-hash))
  (define out g)
  (for* ((r (in-range (rows g))) (c (in-range (cols g))))
    (when (and (not (= (at g r c) 8))
               (not (hash-has-key? seen (list r c))))
      (define region
        (connected-region g r c (lambda (rr cc v) (not (= v 8))) 4))
      (for ((p (in-list region))) (hash-set! seen p #t))
      (define seed-values
        (filter (lambda (v) (not (member? v (list 0 8))))
                (map (lambda (p) (at g (first p) (second p))) region)))
      (define seed-colors (remove-duplicates seed-values))
      (define counts
        (for/list ((color (in-list seed-colors)))
          (for/sum ((v (in-list seed-values))) (if (= v color) 1 0))))
      (define winner
        (if (empty? seed-colors)
            #f
            (list-ref seed-colors (index-of counts (apply max counts)))))
      (when winner
        (set! out
              (for/fold ((acc out)) ((p (in-list region)))
                (if (= (at g (first p) (second p)) 0)
                    (set-cell acc (first p) (second p) winner)
                    acc))))))
  out))
