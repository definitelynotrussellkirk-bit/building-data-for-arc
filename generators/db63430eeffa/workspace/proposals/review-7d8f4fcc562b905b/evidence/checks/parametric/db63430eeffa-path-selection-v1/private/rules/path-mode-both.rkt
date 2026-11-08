(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((eights (find-color g 8))
                  (p1 (first eights))
                  (p2 (second eights))
                  (r1 (first p1))
                  (c1 (second p1))
                  (r2 (first p2))
                  (c2 (second p2))
                  (dr (- r2 r1))
                  (dc (- c2 c1))
                  (adr (abs dr))
                  (adc (abs dc))
                  (sr (cond ((> dr 0) 1) ((< dr 0) -1) (else 0)))
                  (sc (cond ((> dc 0) 1) ((< dc 0) -1) (else 0)))
                  (d-steps (min adr adc))
                  (s-steps (abs (- adr adc)))
                  (major-is-r (> adr adc))
                  (path (make-hash)))
             (let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step d-steps) (hash-set! path (list rr cc) #t)
                      (loop1 (+ rr sr) (+ cc sc) (+ step 1)))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step s-steps) (hash-set! path (list rr cc) #t)
                                   (cond
                                     (major-is-r (loop2 (+ rr sr) cc (+ step 1)))
                                     (else (loop2 rr (+ cc sc) (+ step 1)))))
                                 (else (hash-set! path (list rr cc) #t)))))))
             (let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step s-steps) (hash-set! path (list rr cc) #t)
                      (cond
                        (major-is-r (loop1 (+ rr sr) cc (+ step 1)))
                        (else (loop1 rr (+ cc sc) (+ step 1)))))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step d-steps) (hash-set! path (list rr cc) #t)
                                   (loop2 (+ rr sr) (+ cc sc) (+ step 1)))
                                 (else (hash-set! path (list rr cc) #t)))))))
             (cellmap g
                      (r c v)
                      (cond
                        ((and (= r r1) (= c c1)) 8)
                        ((and (= r r2) (= c c2)) 8)
                        ((hash-has-key? path (list r c)) 3)
                        (else 0)))))))
