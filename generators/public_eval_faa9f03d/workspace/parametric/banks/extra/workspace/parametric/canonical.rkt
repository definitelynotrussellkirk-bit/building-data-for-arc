(rule!
 (lambda (g)
   (define crossing-policy "fragmented")
   (define bg (mode g -1))
   (define h (rows g))
   (define w (cols g))
   (define dirs '((-1 0) (1 0) (0 -1) (0 1)))
   (define positions (grid-positions g))
   (define colors (remove-duplicates (filter (lambda (v) (!= v bg)) (map (lambda (p) (at g (first p) (second p))) positions))))
   (define (in? p) (and (<= 0 (first p)) (< (first p) h) (<= 0 (second p)) (< (second p) w)))
   (define (p+ p d) (list (+ (first p) (first d)) (+ (second p) (second d))))
   (define (cells-of color) (filter (lambda (p) (= (at g (first p) (second p)) color)) positions))
   (define (color-components color)
    (let loop ([remaining (cells-of color)] [out '()])
     (if (null? remaining) (reverse out)
      (let* ([p (first remaining)]
             [part (connected-region g (first p) (second p) (lambda (r c v) (= v color)) 4)]
             [left (filter (lambda (q) (not (member q part))) remaining)])
       (loop left (cons part out))))))
   (define marker-colors
    (filter (lambda (color) (andmap (lambda (part) (= (length part) 1)) (color-components color))) colors))
   (define line-colors (filter (lambda (color) (not (member color marker-colors))) colors))
   (define (get recs color) (second (findf (lambda (rec) (= (first rec) color)) recs)))
   (define (put recs color cells) (map (lambda (rec) (if (= (first rec) color) (list color cells) rec)) recs))
   (define originals (map (lambda (color) (list color (cells-of color))) line-colors))
   (define (axis-support? cells p horizontal?)
    (if horizontal?
        (or (member (list (first p) (- (second p) 1)) cells) (member (list (first p) (+ (second p) 1)) cells))
        (or (member (list (- (first p) 1) (second p)) cells) (member (list (+ (first p) 1) (second p)) cells))))
   (define marker-points (filter (lambda (p) (member (at g (first p) (second p)) marker-colors)) positions))
   (define (scan marker d)
    (let loop ([p (p+ marker d)] [dist 1])
     (cond [(not (in? p)) #f]
           [else
            (define v (at g (first p) (second p)))
            (cond [(member v line-colors)
                   (list dist (if (axis-support? (get originals v) p (= (first d) 0)) 0 1) v d)]
                  [(or (= v bg) (member v marker-colors)) (loop (p+ p d) (+ dist 1))]
                  [else #f])])))
   (define (cand<? a b)
    (cond [(< (first a) (first b)) #t] [(> (first a) (first b)) #f]
          [(< (second a) (second b)) #t] [(> (second a) (second b)) #f]
          [else (< (third a) (third b))]))
   (define assignments
    (for/list ([m (in-list marker-points)])
     (let* ([cs (filter identity (map (lambda (d) (scan m d)) dirs))]
            [best (first (sort cs cand<?))])
      (list m (third best) (fourth best)))))
   (define (assigned-color p) (second (findf (lambda (rec) (equal? (first rec) p)) assignments)))
   (define masks0
    (for/list ([color (in-list line-colors)])
     (list color (remove-duplicates (append (get originals color)
       (map first (filter (lambda (rec) (= (second rec) color)) assignments)))))))
   (define marker-masks
    (for/list ([color (in-list line-colors)])
     (list color (map first (filter (lambda (rec) (= (second rec) color)) assignments)))))
   (define (component-count cells)
    (let loop ([remaining cells] [n 0])
     (if (null? remaining) n
      (let* ([start (first remaining)]
             [part
              (let bfs ([front (list start)] [seen (list start)])
               (if (null? front) seen
                (let* ([p (first front)] [rest (rest front)]
                       [ns (filter (lambda (q) (and (member q cells) (not (member q seen)))) (map (lambda (d) (p+ p d)) dirs))])
                 (bfs (append rest ns) (append seen ns)))))]
             [left (filter (lambda (q) (not (member q part))) remaining)])
       (loop left (+ n 1))))))
   (define comp-counts (map (lambda (color) (list color (component-count (get masks0 color)))) line-colors))
   (define (cc color) (second (findf (lambda (rec) (= (first rec) color)) comp-counts)))
   (define (perp-support? cells p horizontal?) (axis-support? cells p (not horizontal?)))
   (define (marker? color p) (member p (get marker-masks color)))
   (define (should-fill? masks color a b horizontal?)
    (define cells (get masks color))
    (define gap (if horizontal? (- (second b) (second a) 1) (- (first b) (first a) 1)))
    (define aa (or (marker? color a) (axis-support? cells a horizontal?)))
    (define bb (or (marker? color b) (axis-support? cells b horizontal?)))
    (cond [(<= gap 0) #f]
          [(= gap 1) (if (or aa bb) #t (not (and (perp-support? cells a horizontal?) (perp-support? cells b horizontal?))))]
          [(and (marker? color a) (marker? color b)) #f]
          [else (and aa bb)]))
   (define (between a b horizontal?)
    (if horizontal?
        (for/list ([c (in-range (+ (second a) 1) (second b))]) (list (first a) c))
        (for/list ([r (in-range (+ (first a) 1) (first b))]) (list r (second a)))))
   (define (pair-adds masks color cells horizontal? round)
    (apply append
     (for/list ([k (in-range (if horizontal? h w))])
      (let* ([ps0 (filter (lambda (p) (= (if horizontal? (first p) (second p)) k)) cells)]
             [ps (sort ps0 < #:key (if horizontal? second first))])
       (if (< (length ps) 2) '()
        (apply append
         (for/list ([i (in-range (- (length ps) 1))])
          (let* ([a (list-ref ps i)] [b (list-ref ps (+ i 1))]
                 [gap (if horizontal? (- (second b) (second a) 1) (- (first b) (first a) 1))])
           (if (and (or (= round 0) (> gap 1)) (should-fill? masks color a b horizontal?))
               (between a b horizontal?) '())))))))))
   (define (round-fill masks round)
    (for/fold ([cur masks]) ([color (in-list line-colors)])
     (let* ([cells (get cur color)]
            [adds-h (pair-adds cur color cells #t round)]
            [adds-v (pair-adds cur color cells #f round)])
       (put cur color (remove-duplicates (append cells adds-h adds-v))))))
   (define masks-filled
    (let loop ([m masks0] [round 0])
     (if (>= round 12) m
      (let ([m2 (round-fill m round)]) (if (equal? m2 m) m (loop m2 (+ round 1)))))))
   (define (assignment-rec p) (findf (lambda (rec) (equal? (first rec) p)) assignments))
   (define yellow-points (if (member 4 marker-colors) (cells-of 4) '()))
   (define (reachable-without-pivot cells start pivot)
    (if (not (member start cells)) '()
     (let bfs ([front (list start)] [seen (list start)])
      (if (null? front) seen
       (let* ([p (first front)] [restq (rest front)]
              [ns (filter (lambda (q) (and (member q cells) (not (equal? q pivot)) (not (member q seen)))) (map (lambda (d) (p+ p d)) dirs))])
        (bfs (append restq ns) (append seen ns)))))))
   (define (ray start d)
    (let loop ([p start] [out '()]) (if (in? p) (loop (p+ p d) (cons p out)) (reverse out))))
   (define yellow-result
    (for/fold ([state (list masks-filled (map (lambda (c) (list c '())) line-colors))]) ([control (in-list yellow-points)])
     (let* ([masks (first state)] [rays (second state)] [rec (assignment-rec control)] [color (second rec)] [d (third rec)]
            [cells (get masks color)]
            [pivot (let loop ([p (p+ control d)]) (cond [(not (in? p)) #f] [(member p cells) p] [else (loop (p+ p d))]))]
            [old-start (and pivot (p+ pivot d))]
            [old-arm (if pivot (reachable-without-pivot cells old-start pivot) '())]
            [kept (filter (lambda (p) (not (member p old-arm))) cells)]
            [back (list (- (first d)) (- (second d)))]
            [newray (if pivot (ray pivot back) '())]
            [m2 (put masks color (remove-duplicates (append kept newray)))]
            [r2 (put rays color (remove-duplicates (append (get rays color) newray)))])
       (list m2 r2))))
   (define masks (first yellow-result))
   (define control-rays (second yellow-result))
   (define (claims p) (filter (lambda (color) (member p (get masks color))) line-colors))
   (define (marker-brackets? color p)
    (define ms (get marker-masks color))
    (define same-row (map second (filter (lambda (q) (= (first q) (first p))) ms)))
    (define same-col (map first (filter (lambda (q) (= (second q) (second p))) ms)))
    (or (and (ormap (lambda (x) (< x (second p))) same-row) (ormap (lambda (x) (> x (second p))) same-row))
        (and (ormap (lambda (x) (< x (first p))) same-col) (ormap (lambda (x) (> x (first p))) same-col))))
   (define (score color p) (+ (cc color) (if (member p (get control-rays color)) 1 0)))
   (define (fragmented-winner cs p)
    (first (sort cs (lambda (a b)
     (let ([sa (score a p)] [sb (score b p)])
      (if (= sa sb) (< a b) (if (equal? crossing-policy "complete") (< sa sb) (> sa sb))))))))
   (build-grid h w (r c)
    (let* ([p (list r c)] [cs (claims p)])
     (cond [(null? cs) bg]
           [(= (length cs) 1) (first cs)]
           [(member (at g r c) cs) (fragmented-winner cs p)]
           [else
            (define bracketed (filter (lambda (color) (marker-brackets? color p)) cs))
            (if (null? bracketed) (apply min cs) (fragmented-winner bracketed p))])))))
