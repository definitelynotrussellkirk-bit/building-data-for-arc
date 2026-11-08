#lang racket
(require json racket/list racket/set)
(provide main solve-grid)

(define (jref h key default)
  (cond
    [(and (hash? h) (hash-has-key? h key)) (hash-ref h key)]
    [(and (hash? h) (hash-has-key? h (symbol->string key)))
     (hash-ref h (symbol->string key))]
    [else default]))

(define (clockwise dr dc) (list dc (- dr)))
(define (counterclockwise dr dc) (list (- dc) dr))

(define (seed-launches g launch-mode)
  (define h (vector-length g))
  (define w (vector-length (vector-ref g 0)))
  (define seeds
    (for*/list ([r (in-range h)]
                [c (in-range w)]
                #:when (= 3 (vector-ref (vector-ref g r) c)))
      (list r c)))
  (unless (= (length seeds) 2)
    (error 'seed-launches "expected exactly two green seed cells"))
  (define sorted
    (sort seeds
          (lambda (a b)
            (or (< (first a) (first b))
                (and (= (first a) (first b))
                     (< (second a) (second b)))))))
  (define a (first sorted))
  (define b (second sorted))
  (define r1 (first a))
  (define c1 (second a))
  (define r2 (first b))
  (define c2 (second b))
  (define outward
    (cond
      [(and (= r1 r2) (= (abs (- c1 c2)) 1))
       (let ([lo (min c1 c2)] [hi (max c1 c2)])
         (list (list r1 (sub1 lo) 0 -1)
               (list r1 (add1 hi) 0 1)))]
      [(and (= c1 c2) (= (abs (- r1 r2)) 1))
       (let ([lo (min r1 r2)] [hi (max r1 r2)])
         (list (list (sub1 lo) c1 -1 0)
               (list (add1 hi) c1 1 0)))]
      [else (error 'seed-launches "seed cells must be adjacent")]))
  (if (equal? launch-mode "four")
      (append
       outward
       (if (= r1 r2)
           (list (list r1 (add1 (min c1 c2)) 0 1)
                 (list r1 (sub1 (max c1 c2)) 0 -1))
           (list (list (add1 (min r1 r2)) c1 1 0)
                 (list (sub1 (max r1 r2)) c1 -1 0))))
      outward))

(define (solve-grid raw-grid mode config)
  (define original (list->vector (map list->vector raw-grid)))
  (define out
    (list->vector
     (map (lambda (row) (list->vector (vector->list row)))
          (vector->list original))))
  (define h (vector-length original))
  (define w (if (= h 0) 0 (vector-length (vector-ref original 0))))
  (define (inside? r c)
    (and (<= 0 r) (< r h) (<= 0 c) (< c w)))
  (define (at r c)
    (vector-ref (vector-ref original r) c))
  (define (aligned-wall? r c dr dc)
    (and
     (jref config 'cyan_along_pass #f)
     (or
      (and
       (not (= dr 0))
       (or (and (inside? (- r dr) c) (= 8 (at (- r dr) c)))
           (and (inside? (+ r dr) c) (= 8 (at (+ r dr) c)))))
      (and
       (not (= dc 0))
       (or (and (inside? r (- c dc)) (= 8 (at r (- c dc))))
           (and (inside? r (+ c dc)) (= 8 (at r (+ c dc)))))))))
  (define initial
    (if (= h 0)
        '()
        (seed-launches original (jref config 'launch_mode "outward"))))
  (let loop ([queue initial] [seen (set)])
    (if (null? queue)
        (map vector->list (vector->list out))
        (let* ([state (car queue)]
               [restq (cdr queue)]
               [r (first state)]
               [c (second state)]
               [dr (third state)]
               [dc (fourth state)])
          (cond
            [(or (not (inside? r c)) (set-member? seen state))
             (loop restq seen)]
            [else
             (let* ([seen2 (set-add seen state)]
                    [cell (at r c)]
                    [next-straight (list (+ r dr) (+ c dc) dr dc)])
               (cond
                 [(= cell 8)
                  (if (aligned-wall? r c dr dc)
                      (loop (append restq (list next-straight)) seen2)
                      (let* ([dirs
                              (append
                               (if (or (equal? mode "split_both")
                                       (equal? mode "clockwise_only"))
                                   (list (clockwise dr dc))
                                   '())
                               (if (or (equal? mode "split_both")
                                       (equal? mode "counterclockwise_only"))
                                   (list (counterclockwise dr dc))
                                   '())
                               (if (jref config 'straight_at_wall #f)
                                   (list (list dr dc))
                                   '()))]
                             [branches
                              (for/list ([d dirs])
                                (list (+ r (first d))
                                      (+ c (second d))
                                      (first d)
                                      (second d)))])
                        (loop (append restq branches) seen2)))]
                 [(= cell 7)
                  (vector-set! (vector-ref out r) c 3)
                  (if (jref config 'orange_stops #f)
                      (loop restq seen2)
                      (loop (append restq (list next-straight)) seen2))]
                 [(or (= cell 0) (= cell 3))
                  (loop (append restq (list next-straight)) seen2)]
                 [(jref config 'other_stops #t)
                  (loop restq seen2)]
                 [else
                  (loop (append restq (list next-straight)) seen2)]))])))))

(define (main mode)
  (define payload (read-json (current-input-port)))
  (define grid (jref payload 'grid '()))
  (define config (jref payload 'config (hash)))
  (write-json (solve-grid grid mode config))
  (newline))
