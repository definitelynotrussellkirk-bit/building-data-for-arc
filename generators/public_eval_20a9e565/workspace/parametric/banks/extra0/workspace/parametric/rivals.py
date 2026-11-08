"""Bounded executable alternatives; each predicts all four queries privately."""


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"expected one rival anchor: {old}")
    return source.replace(old, new)


def programs(adapter, settings):
    source = adapter.program(settings)
    other = "new_shell" if settings["output_part"] == "whole" else "whole"
    result = {"other_output_part": adapter.program({"output_part": other})}
    for name, declaration, value in (
        ("immediate_successor", "target-mode 'marked", "target-mode 'immediate"),
        ("one_growth_step_at_target", "shape-mode 'complete", "shape-mode 'first_future"),
        ("copy_last_observed", "shape-mode 'complete", "shape-mode 'last_observed"),
        ("freeze_palette_phase", "color-mode 'cycling", "color-mode 'frozen"),
        ("one_foreground_color", "color-mode 'cycling", "color-mode 'monochrome"),
        ("exclude_marker_border", "crop-mode 'inclusive", "crop-mode 'interior"),
    ):
        result[name] = replace_once(source, f"(define {declaration})", f"(define {value})")
    result["freeze_shell_color_phase"] = replace_once(
        source,
        "(define value (list-ref (fifth track) (modulo index (sixth track))))",
        "(define value (first (fifth track)))")
    # A common ambiguity: count every recolored inherited cell as newly grown.
    # Palette normalization makes coordinate growth and color changes distinct.
    result["color_changes_are_new_cells"] = replace_once(
        source,
        "[else (if (equal? output-part 'whole) current final-shell)]",
        """[else (if (equal? output-part 'whole) current
          (make-hash (for/list ([p (hash-keys current)]
            #:when (or (hash-has-key? final-shell p)
                       (not (= (hash-ref current p)
                               (hash-ref permutation (hash-ref current p))))))
            (cons p (hash-ref current p)))))]""")
    return result
