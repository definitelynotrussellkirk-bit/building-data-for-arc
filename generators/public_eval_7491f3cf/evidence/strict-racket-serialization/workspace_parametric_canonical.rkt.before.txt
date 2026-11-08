(rule!
 ;; Four equal panels sit inside a monochrome frame.  The first panel contains
 ;; an 8-connected divider plus a singleton marker.  Flood the marker side
 ;; without crossing the divider.  In the fourth panel, take the second panel
 ;; on that side and the third panel on the other side; both may contribute on
 ;; the divider, with the marked-side source winning overlaps.
 (lambda (g)
  (let ()
   (define h (rows g))
   (define w (cols g))
   (define frame (at g 0 0))
   (define (full-frame-row? r)
    (andmap (lambda (c) (= (at g r c) frame)) (range w)))
   (define (full-frame-col? c)
    (andmap (lambda (r) (= (at g r c) frame)) (range h)))
   (define active-rows (filter (lambda (r) (not (full-frame-row? r))) (range h)))
   (define r0 (apply min active-rows))
   (define r1 (apply max active-rows))
   (define starts
    (for/list ((c (range w))
               #:when (and (not (full-frame-col? c))
                           (or (= c 0) (full-frame-col? (- c 1))))) c))
   (define runs
    (for/list ((s starts))
     (list s (let loop ((c s))
               (if (or (= c w) (full-frame-col? c)) (- c 1) (loop (+ c 1)))))))
   (define panels
    (for/list ((run runs)) (subgrid g r0 (first run) r1 (second run))))
   (define bg (mode-list (apply append (map (lambda (p) (apply append p)) panels))))
   (define control (first panels))
   (define objects0 (objects-multicolor control bg))
   (define divider (obj-cells (argmax obj-size objects0)))
   (define marker-object (argmin obj-size objects0))
   (define marker (first (obj-cells marker-object)))
   (define marked
    (connected-region control (first marker) (second marker)
     (lambda (r c v) (not (member (list r c) divider))) 4))
   (define source-assignment 'second_in_marked)
   (define marked-source
    (if (equal? source-assignment 'second_in_marked) (second panels) (third panels)))
   (define other-source
    (if (equal? source-assignment 'second_in_marked) (third panels) (second panels)))
   (define ph (rows control))
   (define pw (cols control))
   (define completed
    (grid-from-fn ph pw
     (lambda (r c)
      (define p (list r c))
      (define on-divider (member p divider))
      (define on-marked (member p marked))
      (define a (at marked-source r c))
      (define b (at other-source r c))
      (cond ((and (or on-marked on-divider) (not (= a bg))) a)
            ((and (or (not on-marked) on-divider) (not (= b bg))) b)
            (else bg)))))
   (define target (fourth runs))
   (paste g completed r0 (first target))))))
