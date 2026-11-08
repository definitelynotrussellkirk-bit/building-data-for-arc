(rule!
  (define bg (mode g -1))
  (define ignore-color #t)
  (define separators
    (filter (lambda (r) (and (not (= (at g r 0) bg))
                             (andmap (lambda (c) (= (at g r c) (at g r 0))) (range w)))) (range h)))
  (define top (first separators))
  (define bottom (second separators))
  (define (runs xs)
    (if (null? xs) (list)
      (let loop ([lo (first xs)] [hi (first xs)] [rest-xs (rest xs)] [acc (list)])
        (cond [(null? rest-xs) (reverse (cons (list lo hi) acc))]
              [(= (first rest-xs) (+ hi 1)) (loop lo (first rest-xs) (rest rest-xs) acc)]
              [else (loop (first rest-xs) (first rest-xs) (rest rest-xs) (cons (list lo hi) acc))]))))
  (define rb (runs (filter (lambda (r) (ormap (lambda (c) (not (= (at g r c) bg))) (range w))) (range (+ top 1) bottom))))
  (define cb (runs (filter (lambda (c) (ormap (lambda (r) (not (= (at g r c) bg))) (range (+ top 1) bottom))) (range w))))
  (define hc (runs (filter (lambda (c) (ormap (lambda (r) (not (= (at g r c) bg))) (range top))) (range w))))
  (define (signature r1 c1 r2 c2)
    (define cells (filter (lambda (p) (not (= (at g (first p) (second p)) bg))) (positions-in-rect r1 c1 r2 c2)))
    (define mr (apply min (map first cells)))
    (define mc (apply min (map second cells)))
    (map (lambda (p) (list (- (first p) mr) (- (second p) mc)
                           (if ignore-color 1 (at g (first p) (second p))))) cells))
  (define wanted (map (lambda (b) (signature 0 (first b) (- top 1) (second b))) hc))
  (define matched
    (for*/list ([r (range (length rb))] [c (range (length cb))]
                #:when (member (signature (first (list-ref rb r)) (first (list-ref cb c))
                                          (second (list-ref rb r)) (second (list-ref cb c))) wanted))
      (list r c)))
  (define success
    (or (ormap (lambda (r) (andmap (lambda (c) (member (list r c) matched)) (range (length cb)))) (range (length rb)))
        (ormap (lambda (c) (andmap (lambda (r) (member (list r c) matched)) (range (length rb)))) (range (length cb)))))
  (define highlighted
    (for/fold ([out g]) ([p matched])
      (define y (list-ref rb (first p)))
      (define x (list-ref cb (second p)))
      (for*/fold ([acc out]) ([r (range (- (first y) 1) (+ (second y) 2))]
                               [c (range (- (first x) 1) (+ (second x) 2))])
        (if (= (at g r c) bg) (set-cell acc r c 3) acc))))
  (build-grid h w (r c)
    (cond [(> r bottom) (if success 3 2)]
          [(and success (< r top) (= (at g r c) bg)) 3]
          [else (at highlighted r c)])))
