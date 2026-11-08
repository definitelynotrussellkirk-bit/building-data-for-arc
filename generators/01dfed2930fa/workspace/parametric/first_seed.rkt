(rule! (let ((dummy 0))
  (define seen (make-hash))
  (define out g)
  (for* ((r (in-range (rows g))) (c (in-range (cols g))))
    (when (and (not (= (at g r c) 8))
               (not (hash-has-key? seen (list r c))))
      (define region
        (connected-region g r c (lambda (rr cc v) (not (= v 8))) 4))
      (for ((p (in-list region))) (hash-set! seen p #t))
      (define winner
        (for*/first ((rr (in-range (rows g)))
                     (cc (in-range (cols g)))
                     #:when
                     (and (member (list rr cc) region)
                          (not (member? (at g rr cc) (list 0 8)))))
          (at g rr cc)))
      (when winner
        (set! out
              (for/fold ((acc out)) ((p (in-list region)))
                (if (= (at g (first p) (second p)) 0)
                    (set-cell acc (first p) (second p) winner)
                    acc))))))
  out))
