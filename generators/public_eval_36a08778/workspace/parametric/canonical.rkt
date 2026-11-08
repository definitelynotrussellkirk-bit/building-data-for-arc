(rule!
 ;; Magenta rays begin at the top edge and fall downward through orange space.
 ;; A ray that reaches a horizontal red segment first identifies that complete
 ;; segment.  It then paints the row immediately above the segment from one
 ;; cell beyond the left end through one cell beyond the right end, and the two
 ;; free endpoint columns become the rays for the following rows.  Endpoints
 ;; outside the grid are discarded.  Rays not meeting red continue straight.
 (lambda (g)
  (let ()
   (define routing-mode 'split)
   (define h (rows g))
   (define w (cols g))
   (define (unique-columns xs) (sort (remove-duplicates xs) <))
   (define (segment-bounds r c)
    (define left
     (let loop ([x c])
      (if (and (> x 0) (= (at g r (- x 1)) 2)) (loop (- x 1)) x)))
    (define right
     (let loop ([x c])
      (if (and (< (+ x 1) w) (= (at g r (+ x 1)) 2)) (loop (+ x 1)) x)))
    (list left right))
   (define (paint-range out r a b)
    (if (or (< r 0) (> a b)) out
     (for/fold ([result out]) ([c (range a (+ b 1))])
      (if (and (in-bounds? r c h w) (not (= (at g r c) 2))) (set-cell result r c 6) result))))
   (define sources
    (for/list ([c (range w)] #:when (= (at g 0 c) 6)) c))
   (define-values (answer final-active)
    (for/fold ([out g] [active sources]) ([r (range 1 h)])
     (define-values (next updated seen)
      (for/fold ([next '()] [current out] [seen '()]) ([c active])
       (cond
        [(not (in-bounds? r c h w)) (values next current seen)]
        [(not (= (at g r c) 2))
         (values (cons c next) (set-cell current r c 6) seen)]
        [else
         (define bounds (segment-bounds r c))
         (define left (first bounds))
         (define right (second bounds))
         (cond
          [(equal? routing-mode 'split)
           (if (member bounds seen)
            (values next current seen)
            (let* ([left-exit (- left 1)]
                   [right-exit (+ right 1)]
                   [cap (paint-range current (- r 1)
                                     (max 0 left-exit) (min (- w 1) right-exit))]
                   [with-left (if (>= left-exit 0) (set-cell cap r left-exit 6) cap)]
                   [with-both (if (< right-exit w) (set-cell with-left r right-exit 6) with-left)]
                   [new-next (append (if (>= left-exit 0) (list left-exit) '())
                                     (if (< right-exit w) (list right-exit) '()) next)])
             (values new-next with-both (cons bounds seen))))]
          [else
           (define left-exit (- left 1))
           (define right-exit (+ right 1))
           (define choose-left
            (or (>= right-exit w)
                (and (>= left-exit 0)
                     (<= (- c left-exit) (- right-exit c)))))
           (define exit (if choose-left left-exit right-exit))
           (define cap (paint-range current (- r 1) (min c exit) (max c exit)))
           (values (if (in-bounds? r exit h w) (cons exit next) next)
                   (if (in-bounds? r exit h w) (set-cell cap r exit 6) cap)
                   seen)])])))
     (values updated (unique-columns next))))
   answer)))
