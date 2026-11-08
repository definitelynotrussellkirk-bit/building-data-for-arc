(rule!
 ;; Decode the top template bank and bottom palette bank by source color.  The
 ;; middle bank is a sparse n-by-n macro canvas: a nonzero token selects its
 ;; same-colored template and palette entry.  Expand each occupied macro cell
 ;; to an n-by-n recolored template.  The alternate episode setting binds each
 ;; occupied position to the next row-major token before rendering.
 (lambda (g)
  (let ()
   (define binding-mode 'self)
   (define h (rows g))
   (define w (cols g))
   (define separator-rows
    (filter (lambda (r) (= (at g r 0) 5)) (range 2 (min h 8))))
   (define n (first separator-rows))
   (define bottom (+ (* 2 n) 2))
   (define candidate-starts (range 0 (+ 1 (- w n)) (+ n 1)))
   (define (block-values r0 r1 c0)
    (remove-duplicates
     (filter (lambda (v) (and (not (= v 0)) (not (= v 5))))
      (for*/list ((r (range r0 r1)) (c (range c0 (+ c0 n)))) (at g r c)))))
   (define starts
    (filter (lambda (c0) (= (length (block-values 0 n c0)) 1)) candidate-starts))
   (define source-order (map (lambda (c0) (first (block-values 0 n c0))) starts))
   (define records (map list source-order starts))
   (define (record-for source)
    (first (filter (lambda (record) (= (first record) source)) records)))
   (define (token-at r c)
    (define found
     (for/list ((c0 starts) (owner (range (length starts)))
                #:when (let ((v (at g (+ n 1 r) (+ c0 c))))
                         (and (not (= v 0)) (not (= v 5)))))
      (list (at g (+ n 1 r) (+ c0 c)) owner)))
    (if (null? found) (list 0 -1) (first found)))
   (define occupied
    (for*/list ((r (range n)) (c (range n))
                #:when (not (= (first (token-at r c)) 0)))
     (list r c (first (token-at r c)) (second (token-at r c)))))
   (define count (length occupied))
   (define (bound-source index record)
    (if (equal? binding-mode 'self)
        (third record)
        (third (list-ref occupied (modulo (+ index 1) count)))))
   (define (target-for source)
    (define c0 (second (record-for source)))
    (first (block-values bottom h c0)))
   (for*/fold ((out (empty-grid (* n n) (* n n) 0)))
    ((index (range count))
     (rr (range n))
     (cc (range n)))
    (define record (list-ref occupied index))
    (define source (bound-source index record))
    (define c0 (second (record-for source)))
    (if (= (at g rr (+ c0 cc)) source)
        (set-cell out (+ (* (first record) n) rr)
                      (+ (* (second record) n) cc)
                      (target-for source))
        out)))))
