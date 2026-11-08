#lang racket
(require json racket/list)

(define MARKER-ORDER 'near_to_far)
(define input-grid (read-json))
(define H (length input-grid))
(define W (length (first input-grid)))
(define (cell r c) (list-ref (list-ref input-grid r) c))
(define (edge-distance r c)
  (min r c (- H 1 r) (- W 1 c)))

(define counts (make-hash))
(for* ([r (in-range H)] [c (in-range W)])
  (define value (cell r c))
  (unless (= value 0)
    (hash-update! counts value add1 0)))
(define entries (hash->list counts))
(when (null? entries)
  (error 'marker-order "at least one nonzero color is required"))
(define best-entry
  (for/fold ([best (first entries)]) ([entry (rest entries)])
    (if (> (cdr entry) (cdr best)) entry best)))
(define background (car best-entry))

(define markers
  (for*/list ([r (in-range H)] [c (in-range W)]
              #:when (not (= (cell r c) background)))
    (list (edge-distance r c) r c (cell r c))))
(define (distance-before? left right)
  (if (eq? MARKER-ORDER 'near_to_far)
      (< (first left) (first right))
      (> (first left) (first right))))
(define ordered (sort markers distance-before?))
(define colors (map fourth ordered))
(define N (length colors))
(define output
  (for/list ([r (in-range H)])
    (for/list ([c (in-range W)])
      (define distance (edge-distance r c))
      (if (< distance N) (list-ref colors distance) background))))
(write-json output)
(newline)
