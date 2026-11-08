(rule!
 ;; The cue row selects colors to erase. Recover horizontal beams before posts,
 ;; preserving a post's one-cell endpoint hidden by a beam or by the floor.
 ;; Settle surviving pieces bottom-up. A beam has bilateral side support, or
 ;; lands on the first direct obstruction; posts land on beams or other posts.
 ;; Paint beams over endpoint joints, and clip floor-hidden endpoints.
 (lambda (g)
  (let ()
    (define either-post #f)
    (define use-raw-supports #f)
    (define h (rows g)) (define w (cols g))
    ;; Record: kind (0=post/1=beam), color, top, left, length, hidden?, source-top.
    (define (kind o) (first o)) (define (color o) (second o))
    (define (top o) (third o)) (define (left o) (fourth o))
    (define (size o) (fifth o)) (define (hidden? o) (sixth o))
    (define (source-top o) (seventh o))
    (define (bottom o) (+ (top o) (if (= (kind o) 0) (- (size o) 1) 0)))
    (define (right o) (+ (left o) (if (= (kind o) 1) (- (size o) 1) 0)))
    (define (move o r) (list (kind o) (color o) r (left o) (size o) (hidden? o) (source-top o)))
    (define removed (remove-duplicates (filter (lambda (v) (not (= v 0))) (first g))))
    (define beams
      (for*/list ([r (in-range 2 (- h 1))] [c (in-range w)]
        #:when (and (not (= (at g r c) 0)) (or (= c 0) (= (at g r (- c 1)) 0)))
        #:do [(define end (let loop ([j (+ c 1)])
                            (if (and (< j w) (not (= (at g r j) 0))) (loop (+ j 1)) j)))]
        #:when (and (>= (- end c) 3)
                    (= (at g (+ r 1) c) (at g r c))
                    (= (at g (+ r 1) (- end 1)) (at g r (- end 1)))
                    (for/and ([j (in-range (+ c 1) (- end 1))]) (= (at g r j) (at g r (+ c 1))))))
        (list 1 (at g r (+ c 1)) r (+ c 1) (- end c 2) #f r)))
    (define (beam-owned? r c)
      (for/or ([b beams]) (and (= r (top b)) (<= (left b) c) (<= c (right b)))))
    (define posts
      (apply append
        (for/list ([c (in-range w)])
          (let loop ([r 2] [acc '()])
            (cond [(>= r h) (reverse acc)]
                  [(or (= (at g r c) 0) (beam-owned? r c)) (loop (+ r 1) acc)]
                  [else
                    (define end (let scan ([j (+ r 1)])
                      (if (and (< j h) (not (beam-owned? j c)) (= (at g j c) (at g r c)))
                          (scan (+ j 1)) j)))
                    (define hidden (or (= end h) (beam-owned? end c)))
                    (loop end (cons (list 0 (at g r c) r c (+ (- end r) (if hidden 1 0)) hidden r) acc))])))))
    (define survivors
      (sort (filter (lambda (o) (not (member (color o) removed))) (append posts beams))
        (lambda (a b)
          (cond [(not (= (bottom a) (bottom b))) (> (bottom a) (bottom b))]
                [(not (= (kind a) (kind b))) (> (kind a) (kind b))]
                [else (< (left a) (left b))]))))
    (define placed
      (for/fold ([done '()]) ([o survivors])
        (define newtop
          (if (= (kind o) 0)
            (let ([end (for/fold ([e (if (hidden? o) h (- h 1))]) ([lower done])
                         (cond [(and (= (kind lower) 1) (<= (left lower) (left o)) (<= (left o) (right lower)))
                                (min e (top lower))]
                               [(and (= (kind lower) 0) (= (left lower) (left o))) (min e (- (top lower) 1))]
                               [else e]))])
              (+ (- end (size o)) 1))
            (let* ([direct (for/fold ([r (- h 1)]) ([lower done])
                             (if (or (< (right lower) (left o)) (> (left lower) (right o)))
                                 r (min r (- (top lower) 1))))]
                   [side (lambda (c)
                     (for/list ([p done] #:when (and (= (kind p) 0) (= (left p) c)))
                       (if use-raw-supports (move p (source-top p)) p)))]
                   [lp (side (- (left o) 1))] [rp (side (+ (right o) 1))])
              (if either-post
                  (for/fold ([r direct]) ([p (append lp rp)])
                    (define landing (max (top o) (top p)))
                    (if (<= landing (bottom p)) (min r landing) r))
                  (for*/fold ([r direct]) ([a lp] [b rp])
                    (define landing (max (top o) (top a) (top b)))
                    (if (<= landing (min (bottom a) (bottom b))) (min r landing) r))))))
        (when (< newtop (top o)) (error 'support "upward motion outside admitted support grammar"))
        (append done (list (move o newtop)))))
    (grid-from-fn h w
      (lambda (r c)
        (if (= r 0) (at g r c)
          (let ([hits (filter (lambda (o)
                                (and (<= (top o) r) (<= r (bottom o))
                                     (<= (left o) c) (<= c (right o)))) placed)])
            (if (null? hits) 0
                (color (first (sort hits (lambda (a b) (> (kind a) (kind b))))))))))))))
