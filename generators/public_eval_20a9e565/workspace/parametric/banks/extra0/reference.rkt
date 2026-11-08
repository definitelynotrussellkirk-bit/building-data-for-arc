(rule!
 ;; Infer a spatial sequence of additive shapes.  Align the leading edges,
 ;; normalize the input-derived palette permutation, and learn the separate
 ;; shape/translation and color periods of each newly added component track.
 ;; Continue the sequence to the gray-corner window and return its inclusive
 ;; crop.  No object template, supplied grid, answer, or public case ID occurs
 ;; in this rule.  The nearby setting returns only the target step's new cells.
 (lambda (g)
  (let ()
    (define output-part 'whole)
    (define target-mode 'marked)
    (define color-mode 'cycling)
    (define shape-mode 'complete)
    (define crop-mode 'inclusive)
    (define h (rows g))
    (define w (cols g))
    (define (point< a b)
      (or (< (first a) (first b))
          (and (= (first a) (first b)) (< (second a) (second b)))))
    (define (ordered points) (sort points point<))
    (define (coordinate p axis) (if (= axis 0) (first p) (second p)))
    (define foreground
      (for*/list ([r (in-range h)] [c (in-range w)]
                  #:when (not (member (at g r c) '(0 5)))) (list r c)))
    (define gray
      (for*/list ([r (in-range h)] [c (in-range w)] #:when (= (at g r c) 5)) (list r c)))
    (when (or (empty? gray) (empty? foreground))
      (error 'growth "both sequence and gray crop markers are required"))
    (define top (apply min (map first gray)))
    (define bottom (apply max (map first gray)))
    (define left (apply min (map second gray)))
    (define right (apply max (map second gray)))
    (define corner-a
      (list (list top left) (list top (+ left 1)) (list (+ top 1) left)
            (list bottom right) (list bottom (- right 1)) (list (- bottom 1) right)))
    (define corner-b
      (list (list top right) (list top (- right 1)) (list (+ top 1) right)
            (list bottom left) (list bottom (+ left 1)) (list (- bottom 1) left)))
    (unless (and (< top bottom) (< left right)
                 (or (equal? (ordered gray) (ordered (remove-duplicates corner-a)))
                     (equal? (ordered gray) (ordered (remove-duplicates corner-b)))))
      (error 'growth "two opposite gray L corners must bound the inclusive crop"))
    (define (runs values)
      (reverse
        (for/fold ([parts '()]) ([value (sort (remove-duplicates values) <)])
          (if (and (not (empty? parts)) (= value (+ (second (first parts)) 1)))
              (cons (list (first (first parts)) value) (rest parts))
              (cons (list value value) parts)))))
    (define (mass interval axis)
      (length (filter (lambda (p) (<= (first interval) (coordinate p axis) (second interval))) foreground)))
    (define candidates
      (filter identity
        (for/list ([axis '(0 1)])
          (define intervals (runs (map (lambda (p) (coordinate p axis)) foreground)))
          (define masses (map (lambda (interval) (mass interval axis)) intervals))
          (and (>= (length intervals) 3)
            (cond [(andmap < (drop-right masses 1) (rest masses)) (list axis 1)]
                  [(andmap > (drop-right masses 1) (rest masses)) (list axis -1)]
                  [else #f])))))
    (unless (= (length candidates) 1)
      (error 'growth "one projection must identify at least three increasingly large objects"))
    (define axis (first (first candidates)))
    (define direction (second (first candidates)))
    ;; Oriented coordinate s increases along the inferred sequence; t stays in
    ;; the canvas's perpendicular coordinate system.  This also handles D4.
    (define (s p) (* direction (coordinate p axis)))
    (define (t p) (coordinate p (- 1 axis)))
    (define intervals (runs (map s foreground)))
    (define gaps
      (map (lambda (old new) (- (first new) (second old) 1))
           (drop-right intervals 1) (rest intervals)))
    (unless (and (= (length (remove-duplicates gaps)) 1) (> (first gaps) 0))
      (error 'growth "observed objects must have a constant positive gap"))
    (define gap (first gaps))
    (define objects
      (for/list ([interval intervals])
        (make-hash
          (for/list ([p foreground] #:when (<= (first interval) (s p) (second interval)))
            (cons (list (- (s p) (first interval)) (t p)) (at g (first p) (second p)))))))
    ;; A single global permutation is constrained by every retained coordinate
    ;; in every consecutive pair, including older inner layers.
    (define permutation (make-hash))
    (for ([old (drop-right objects 1)] [new (rest objects)])
      (for ([p (hash-keys old)])
        (unless (hash-has-key? new p) (error 'growth "leading-edge support must be additive"))
        (define a (hash-ref old p))
        (define b (hash-ref new p))
        (when (and (hash-has-key? permutation a) (not (= (hash-ref permutation a) b)))
          (error 'growth "overlap colors do not determine one permutation"))
        (hash-set! permutation a b)))
    (define palette (sort (remove-duplicates (map (lambda (p) (at g (first p) (second p))) foreground)) <))
    (unless (and (equal? (sort (hash-keys permutation) <) palette)
                 (equal? (sort (hash-values permutation) <) palette))
      (error 'growth "overlap must determine the whole observed palette bijection"))
    (define inverse (make-hash (map (lambda (c) (cons (hash-ref permutation c) c)) palette)))
    (define (iterate-color color mapping count)
      (for/fold ([value color]) ([i (in-range count)]) (hash-ref mapping value)))
    (define normalized
      (for/list ([object objects] [i (in-naturals)])
        (make-hash (map (lambda (p) (cons p (iterate-color (hash-ref object p) inverse i))) (hash-keys object)))))
    (define additions
      (for/list ([old (drop-right normalized 1)] [new (rest normalized)])
        (for ([p (hash-keys old)])
          (unless (= (hash-ref old p) (hash-ref new p))
            (error 'growth "normalization did not preserve an inherited cell")))
        (make-hash (for/list ([p (hash-keys new)] #:unless (hash-has-key? old p))
          (cons p (hash-ref new p))))))
    ;; Component records: absolute aligned location, sorted relative support,
    ;; and colors in that same deterministic order.  Connectivity is cardinal.
    (define (components cells)
      (define unseen (make-hash (map (lambda (p) (cons p #t)) (hash-keys cells))))
      (define answer '())
      (let next-component ()
        (unless (= (hash-count unseen) 0)
          (define start (first (ordered (hash-keys unseen))))
          (hash-remove! unseen start)
          (define members
            (let flood ([todo (list start)] [found '()])
              (if (empty? todo) found
                  (let* ([p (first todo)]
                         [neighbors (for/list ([delta '((-1 0) (1 0) (0 -1) (0 1))])
                                      (list (+ (first p) (first delta)) (+ (second p) (second delta))))]
                         [fresh (filter (lambda (q) (hash-has-key? unseen q)) neighbors)])
                    (for ([q fresh]) (hash-remove! unseen q))
                    (flood (append fresh (rest todo)) (cons p found))))))
          (define a (apply min (map first members)))
          (define b (apply min (map second members)))
          (define shape (ordered (map (lambda (p) (list (- (first p) a) (- (second p) b))) members)))
          (define colors (map (lambda (p) (hash-ref cells (list (+ a (first p)) (+ b (second p))))) shape))
          (set! answer (cons (list (list a b) shape colors) answer))
          (next-component)))
      (sort answer (lambda (a b) (point< (first a) (first b)))))
    (define shells (map components additions))
    (unless (and (not (empty? (first shells)))
                 (andmap (lambda (parts) (= (length parts) (length (first shells)))) shells))
      (error 'growth "the number of added component tracks must stay fixed"))
    (define (least-color-period values)
      (or (for/first ([p (in-range 1 (+ (length values) 1))]
                      #:when (for/and ([value values] [i (in-naturals)])
                               (equal? value (list-ref values (modulo i p))))) p)
          (error 'growth "no color period")))
    (define (learn-track parts)
      (define n (length parts))
      (define repeat
        (for/first ([p (in-range 1 n)]
                    #:when (and
                      (for/and ([part parts] [i (in-naturals)])
                        (equal? (second part) (second (list-ref parts (modulo i p)))))
                      (= 1 (length (remove-duplicates
                        (for/list ([i (in-range p n)])
                          (map - (first (list-ref parts i)) (first (list-ref parts (- i p))))))))))
          p))
      (unless repeat (error 'growth "a shell geometry period must repeat with a constant displacement"))
      (define displacement (map - (first (list-ref parts repeat)) (first (first parts))))
      (define mono? (andmap (lambda (part) (= 1 (length (remove-duplicates (third part))))) parts))
      (unless (or mono? (andmap (lambda (part) (equal? (second part) (second (first parts)))) parts))
        (error 'growth "varying multicolor component geometry is outside this grammar"))
      (define color-values (map (lambda (part) (if mono? (first (third part)) (third part))) parts))
      (list parts repeat displacement mono? color-values (least-color-period color-values)))
    (define tracks
      (for/list ([j (in-range (length (first shells)))])
        (learn-track (map (lambda (parts) (list-ref parts j)) shells))))
    (define (predict-track track index)
      (define parts (first track))
      (define period (second track))
      (define displacement (third track))
      (define base (list-ref parts (modulo index period)))
      (define origin (map + (first base) (map (lambda (d) (* (quotient index period) d)) displacement)))
      (define value (list-ref (fifth track) (modulo index (sixth track))))
      (define colors (if (fourth track) (make-list (length (second base)) value) value))
      (map (lambda (p color) (cons (map + p origin) color)) (second base) colors))
    (define crop-s (sort (list (* direction (if (= axis 0) top left))
                               (* direction (if (= axis 0) bottom right))) <))
    (when (<= (first crop-s) (second (last intervals)))
      (error 'growth "the crop must be beyond the complete observed sequence"))
    ;; A: infer the future index from reconstructed object spans and the actual
    ;; spatial window, which may skip generations or reveal only a partial crop.
    (define initial (last normalized))
    (define current (hash-copy initial))
    (define previous-end (second (last intervals)))
    (define target-index (length objects))
    (define target-origin 0)
    (define final-shell (make-hash))
    (define first-future #f)
    (define first-shell #f)
    (define located? #f)
    (for ([attempt (in-range (+ 1 (max h w)))] #:break located?)
      (define shell (make-hash))
      (for ([track tracks])
        (for ([entry (predict-track track (- target-index 1))])
          (when (or (hash-has-key? shell (car entry)) (hash-has-key? current (car entry)))
            (error 'growth "extrapolated components must add disjoint new support"))
          (hash-set! shell (car entry) (cdr entry))))
      (for ([p (hash-keys shell)]) (hash-set! current p (hash-ref shell p)))
      (unless first-future (set! first-future (hash-copy current)) (set! first-shell (hash-copy shell)))
      (define low (+ previous-end gap 1))
      (define aligned-low (apply min (map first (hash-keys current))))
      (define aligned-high (apply max (map first (hash-keys current))))
      (define origin (- low aligned-low))
      (define high (+ origin aligned-high))
      (if (or (equal? target-mode 'immediate)
              (and (<= low (second crop-s)) (>= high (first crop-s))))
          (begin
            (unless (or (equal? target-mode 'immediate)
                        (<= low (first crop-s) (second crop-s) high))
              (error 'growth "the crop cannot span multiple future objects"))
            (set! target-origin origin)
            (set! final-shell shell)
            (set! located? #t))
          (begin (set! previous-end high) (set! target-index (+ target-index 1)))))
    (unless located? (error 'growth "no bounded future object contains the crop"))
    ;; B consumes the inferred target index and its new support.  New-shell
    ;; means new coordinates, not all cells whose displayed palette changes.
    (define selected
      (cond [(equal? shape-mode 'last_observed) initial]
            [(equal? shape-mode 'first_future) (if (equal? output-part 'whole) first-future first-shell)]
            [else (if (equal? output-part 'whole) current final-shell)]))
    (define rendered (make-hash))
    (for ([p (hash-keys selected)])
      (define absolute-s (* direction (+ (first p) target-origin)))
      (define absolute (if (= axis 0) (list absolute-s (second p)) (list (second p) absolute-s)))
      (define color (hash-ref selected p))
      (define displayed
        (cond [(equal? color-mode 'frozen) color]
              [(equal? color-mode 'monochrome) (iterate-color (first palette) permutation target-index)]
              [else (iterate-color color permutation target-index)]))
      (hash-set! rendered absolute displayed))
    (define inset (if (equal? crop-mode 'interior) 1 0))
    (define oh (max 1 (- (+ 1 (- bottom top)) (* 2 inset))))
    (define ow (max 1 (- (+ 1 (- right left)) (* 2 inset))))
    (grid-from-fn oh ow (lambda (r c) (hash-ref rendered (list (+ top inset r) (+ left inset c)) 0))))))
