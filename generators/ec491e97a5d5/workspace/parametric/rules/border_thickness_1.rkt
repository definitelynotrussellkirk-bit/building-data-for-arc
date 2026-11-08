#lang racket
(require json racket/list)

(define BORDER-THICKNESS 1)

(define grid (read-json))
(define height (length grid))
(define width (length (first grid)))
(define colours
  (remove-duplicates
   (filter positive? (apply append grid))))
(define output
  (for/vector ([r (in-range height)])
    (make-vector width 0)))

(define (cell r c)
  (list-ref (list-ref grid r) c))

(for ([colour (in-list colours)])
  (define coords
    (for*/list ([r (in-range height)]
                [c (in-range width)]
                #:when (= (cell r c) colour))
      (cons r c)))
  (define rows (map car coords))
  (define cols (map cdr coords))
  (define top (apply min rows))
  (define bottom (apply max rows))
  (define left (apply min cols))
  (define right (apply max cols))
  (for* ([r (in-range top (+ bottom 1))]
         [c (in-range left (+ right 1))]
         #:when (< (min (- r top)
                        (- bottom r)
                        (- c left)
                        (- right c))
                   BORDER-THICKNESS))
    (vector-set! (vector-ref output r) c colour)))

(write-json
 (for/list ([row (in-vector output)])
   (vector->list row)))
(newline)
