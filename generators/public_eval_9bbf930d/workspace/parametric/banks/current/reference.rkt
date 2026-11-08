(rule!
 ;; Magenta markers occupy the left border; orange is empty background.
 ;; Launch a marker when its first encountered upper/lower rail pair has one
 ;; common color. Travel through orange, refreshing the active guide color
 ;; whenever equal-colored walls flank the current heading. A same-guide wall
 ;; ahead turns the marker through the unique open perpendicular direction;
 ;; another color, a blocked/ambiguous turn, or the edge stops it. Move only
 ;; the source marker and its endpoint. Black is a wall color, not background.
 (lambda (g)
  (let ()
   (define update-guide? #t)
   (define (wall? v) (and (>= v 0) (not (= v 6)) (not (= v 7))))
   (define (entry-color r)
    (let scan ((c 1))
     (cond ((>= c w) -1)
           ((not (= (at g r c) 7)) -1)
           (else
            (let ((a (safe-at g (- r 1) c -1)) (b (safe-at g (+ r 1) c -1)))
             (cond ((and (= a 7) (= b 7)) (scan (+ c 1)))
                   ((and (= a b) (wall? a)) a)
                   (else -1)))))))
   (define (route r c dr dc color seen fuel)
    (let* ((a (safe-at g (- r dc) (+ c dr) -1))
           (b (safe-at g (+ r dc) (- c dr) -1))
           (guide (if (and update-guide? (= a b) (wall? a)) a color))
           (state (list r c dr dc guide))
           (front (safe-at g (+ r dr) (+ c dc) -1)))
     (cond ((or (<= fuel 0) (member state seen)) (list r c))
           ((= front 7) (route (+ r dr) (+ c dc) dr dc guide (cons state seen) (- fuel 1)))
           ((= front guide)
            (let ((turns
                   (filter (lambda (d) (= (safe-at g (+ r (first d)) (+ c (second d)) -1) 7))
                           (list (list (- dc) dr) (list dc (- dr))))))
             (if (= (length turns) 1)
              (route r c (first (first turns)) (second (first turns)) guide (cons state seen) (- fuel 1))
              (list r c))))
           (else (list r c)))))
   (define starts
    (for/list ((r (range 1 (- h 1))) #:when (and (= (at g r 0) 6) (wall? (entry-color r))))
     (list r (entry-color r))))
   (define ends
    (map (lambda (s) (route (first s) 0 0 1 (second s) '() (* 32 h w))) starts))
   (define cleared
    (for/fold ((out g)) ((s starts)) (set-cell out (first s) 0 7)))
   (for/fold ((out cleared)) ((p ends)) (set-cell out (first p) (second p) 6)))))
