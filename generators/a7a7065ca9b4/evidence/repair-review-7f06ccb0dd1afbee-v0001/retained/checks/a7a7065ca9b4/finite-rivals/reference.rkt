(rule! (lambda (g)
  ;; The first all-zero column ends the source prefix.
  (let* ((h (rows g))
         (w (cols g))
         (pw
          (let loop ((c 0))
            (if (or (>= c w)
                    (for/and ((r (range 0 h)))
                      (zero? (at g r c))))
                c
                (loop (+ c 1))))))
    ;; Keep the prefix, copy it unchanged to the right edge, and fill every
    ;; intervening cell from that row's first color.
    (cellmap g (r c v)
      (cond
        ((< c pw) v)
        ((>= c (- w pw))
         (at g r (- c (- w pw))))
        (else (at g r 0)))))))