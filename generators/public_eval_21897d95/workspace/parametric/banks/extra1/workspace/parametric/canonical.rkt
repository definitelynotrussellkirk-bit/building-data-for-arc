(rule!
 (lambda (g)
   (let ()
     (define payload-mode 1) ; 1 = colored center overrides host, 0 = host only
     (define h (rows g))
     (define w (cols g))
     (define d4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
     (define specs
       (list (list -1 0 0 -1 0 1)
             (list 1 0 0 -1 0 1)
             (list 0 -1 -1 0 1 0)
             (list 0 1 -1 0 1 0)))
     (define (in-bounds? r c)
       (and (<= 0 r) (< r h) (<= 0 c) (< c w)))
     (define (intersects? xs ys)
       (for/or ((x xs)) (member? x ys)))
     (define all-ones (find-color g 1))
     (define candidates
       (for*/list ((r (in-range h)) (c (in-range w)) (s specs)
                   #:when
                   (let* ((dr (first s)) (dc (second s))
                          (a1r (third s)) (a1c (fourth s))
                          (a2r (fifth s)) (a2c (sixth s))
                          (arms (list (list (+ r dr) (+ c dc))
                                      (list (+ r a1r) (+ c a1c))
                                      (list (+ r a2r) (+ c a2c)))))
                     (and (for/and ((p arms))
                            (and (in-bounds? (first p) (second p))
                                 (= (at g (first p) (second p)) 1))))))
         (let* ((dr (first s)) (dc (second s))
                (a1r (third s)) (a1c (fourth s))
                (a2r (fifth s)) (a2c (sixth s))
                (center (list r c))
                (cells (list center
                             (list (+ r dr) (+ c dc))
                             (list (+ r a1r) (+ c a1c))
                             (list (+ r a2r) (+ c a2c))))
                (ones (filter (lambda (p) (= (at g (first p) (second p)) 1)) cells)))
           (list center (list dr dc) cells ones))))
     (define (cover remaining occupied)
       (if (null? remaining)
           '()
           (let ((point (first remaining)))
             (for/or ((candidate candidates)
                      #:when (and (member? point (fourth candidate))
                                  (not (intersects? (third candidate) occupied))))
               (let* ((ones (fourth candidate))
                      (rest (cover (filter (lambda (p) (not (member? p ones))) remaining)
                                   (append occupied (third candidate)))))
                 (and rest (cons candidate rest)))))))
     (define t-markers (cover all-ones '()))
     (define (color-components grid color)
       (find-0-regions
        (grid-from-fn h w (lambda (r c) (if (= (at grid r c) color) 0 1)))
        0))
     (define l-marker
       (for*/first ((color (in-range 0 10)) #:unless (= color 1)
                    (component (color-components g color)) #:when (= (length component) 5)
                    (corner component)
                    (option (list (list 1 0 0 1 1)
                                  (list 1 0 0 -1 -1)))
                    #:when
                    (let* ((d1r (first option)) (d1c (second option))
                           (d2r (third option)) (d2c (fourth option))
                           (shape (list corner
                                        (list (+ (first corner) d1r) (+ (second corner) d1c))
                                        (list (+ (first corner) (* 2 d1r)) (+ (second corner) (* 2 d1c)))
                                        (list (+ (first corner) d2r) (+ (second corner) d2c))
                                        (list (+ (first corner) (* 2 d2r)) (+ (second corner) (* 2 d2c))))))
                      (for/and ((p shape)) (member? p component))))
         (list component corner (fifth option))))
     (define blocked
       (append
        (if (null? t-markers) '() (apply append (map third t-markers)))
        (if l-marker (first l-marker) '())))
     (define (host-color cells)
       (define neighbors
         (for*/list ((p cells) (d d4)
                     (rr (in-value (+ (first p) (first d))))
                     (cc (in-value (+ (second p) (second d))))
                     #:when (and (in-bounds? rr cc)
                                 (not (member? (list rr cc) blocked))))
           (at g rr cc)))
       (define counts
         (for/list ((color (in-range 0 10)))
           (list (length (filter (lambda (x) (= x color)) neighbors)) color)))
       (second
        (for/fold ((best (first counts))) ((entry (rest counts)))
          (if (> (first entry) (first best)) entry best))))
     (define hosted-t
       (map (lambda (marker) (append marker (list (host-color (third marker))))) t-markers))
     (define marker-fills
       (append
        (map (lambda (marker) (list (third marker) (fifth marker))) hosted-t)
        (if l-marker (list (list (first l-marker) (host-color (first l-marker)))) '())))
     (define filled
       (grid-from-fn h w
         (lambda (r c)
           (let* ((p (list r c))
                  (entry (for/first ((m marker-fills) #:when (member? p (first m))) m)))
             (if entry (second entry) (at g r c))))))
     (define rooms
       (apply append
         (for/list ((color (in-range 0 10)))
           (map (lambda (cells) (list color cells)) (color-components filled color)))))
     (define (room-of p)
       (first (filter (lambda (room) (member? p (second room))) rooms)))
     (define (trace-destination host r c dr dc)
       (if (not (in-bounds? r c))
           #f
           (let ((room (room-of (list r c))))
             (if (equal? room host)
                 (trace-destination host (+ r dr) (+ c dc) dr dc)
                 room))))
     (define incoming
       (for/list ((marker hosted-t))
         (let* ((center (first marker))
                (delta (second marker))
                (host (room-of center))
                (dr (first delta)) (dc (second delta))
                (destination (trace-destination host
                                                (+ (first center) dr)
                                                (+ (second center) dc)
                                                dr dc))
                (center-value (at g (first center) (second center)))
                (payload (if (and (= payload-mode 1) (not (= center-value 1)))
                             center-value
                             (first host))))
           (list destination payload))))
     (define recolored
       (grid-from-fn h w
         (lambda (r c)
           (let* ((room (room-of (list r c)))
                  (entry (for/first ((x incoming) #:when (equal? (first x) room)) x)))
             (if entry (second entry) (first room))))))
     (define (rotate-clockwise x)
       (grid-from-fn (cols x) (rows x)
         (lambda (r c) (at x (- (rows x) 1 c) r))))
     (define (rotate-counterclockwise x)
       (grid-from-fn (cols x) (rows x)
         (lambda (r c) (at x c (- (cols x) 1 r)))))
     (cond
       ((not l-marker) recolored)
       ((= (third l-marker) 1) (rotate-clockwise recolored))
       (else (rotate-counterclockwise recolored))))))
