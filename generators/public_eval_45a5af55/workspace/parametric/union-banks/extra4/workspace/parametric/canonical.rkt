(rule!
 (lambda (g)
  (let ()
   ;; Uniform input rows encode successive ring colors. The repeated final row
   ;; is center evidence, not an additional ring. Input width is irrelevant.
   (define reverse-layers #f)
   (define layer-count (- h 1))
   (define observed
    (for/list ([r (in-range layer-count)]) (at g r 0)))
   (define layers (if reverse-layers (reverse observed) observed))
   (define side (* 2 layer-count))
   (build-grid side side (r c)
    (list-ref layers (min r c (- side 1 r) (- side 1 c)))))))
