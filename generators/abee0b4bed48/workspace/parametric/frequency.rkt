(rule!
 (lambda (g)
  (define n (/ (cols g) 3))
  (define (gray-count z)
   (for*/sum ([r (in-range 3)] [c (in-range (* z 3) (+ (* z 3) 3))])
    (if (= (at g r c) 5) 1 0)))
  (define (row-full? z r)
   (all? (lambda (c) (= (at g r c) 5)) (range (* z 3) (+ (* z 3) 3))))
  (define (decode-zone z)
   (let ([cnt (gray-count z)])
    (cond [(= cnt 1) 4] [(= cnt 8) 3]
          [(= cnt 3) (cond [(row-full? z 0) 6] [(row-full? z 2) 1] [else 9])]
          [else 0])))
  (define labels (map decode-zone (range n)))
  (define ranking-labels labels)
  (define (frequency value)
   (for/sum ([x ranking-labels]) (if (= x value) 1 0)))
  (define permutation
   (sort (range n)
    (lambda (a b)
     (let* ([la (list-ref ranking-labels a)] [lb (list-ref ranking-labels b)]
            [fa (frequency la)] [fb (frequency lb)])
      (or (> fa fb)
          (and (= fa fb) (< la lb))
          (and (= fa fb) (= la lb) (< a b)))))))
  (for/list ([r (in-range 3)])
   (for/list ([c (in-range (cols g))])
    (list-ref labels (list-ref permutation (/ c 3)))))))
