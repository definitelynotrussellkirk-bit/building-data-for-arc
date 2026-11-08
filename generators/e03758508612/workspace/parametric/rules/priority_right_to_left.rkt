#lang racket
(require json racket/list)

(define REVERSE-PRIORITY? #t)
(define DIRS (list (cons -1 0) (cons 1 0) (cons 0 -1) (cons 0 1)))

(define (grid-rows grid) (length grid))
(define (grid-cols grid) (length (first grid)))
(define (cell grid row column) (list-ref (list-ref grid row) column))
(define (inside-room-domain? grid row column)
  (and (<= 1 row) (< row (grid-rows grid))
       (<= 0 column) (< column (grid-cols grid))))

(define (solve grid)
  (define base-priority
    (filter (lambda (value) (and (not (= value 0)) (not (= value 8))))
            (first grid)))
  (define priority (if REVERSE-PRIORITY? (reverse base-priority) base-priority))
  (define seen (make-hash))
  (define fills (make-hash))

  (define (room-from start)
    (hash-set! seen start #t)
    (let loop ([queue (list start)] [cells '()])
      (if (empty? queue)
          (reverse cells)
          (let* ([point (first queue)]
                 [row (car point)]
                 [column (cdr point)]
                 [new-neighbours
                  (for/list ([delta (in-list DIRS)]
                             #:do [(define next-row (+ row (car delta)))
                                   (define next-column (+ column (cdr delta)))
                                   (define next-point (cons next-row next-column))]
                             #:when (and (inside-room-domain? grid next-row next-column)
                                         (not (= (cell grid next-row next-column) 8))
                                         (not (hash-has-key? seen next-point))))
                    (hash-set! seen next-point #t)
                    next-point)])
            (loop (append (rest queue) new-neighbours) (cons point cells))))))

  (for* ([row (in-range 1 (grid-rows grid))]
         [column (in-range (grid-cols grid))])
    (define start (cons row column))
    (when (and (not (= (cell grid row column) 8))
               (not (hash-has-key? seen start)))
      (define room (room-from start))
      (define present
        (remove-duplicates
         (for/list ([point (in-list room)])
           (cell grid (car point) (cdr point)))))
      (define winner
        (for/first ([value (in-list priority)] #:when (member value present)) value))
      (when winner
        (for ([point (in-list room)])
          (hash-set! fills point winner)))))

  (for/list ([row (in-range (grid-rows grid))])
    (for/list ([column (in-range (grid-cols grid))])
      (define point (cons row column))
      (if (hash-has-key? fills point)
          (hash-ref fills point)
          (cell grid row column)))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)
