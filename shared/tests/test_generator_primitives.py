import unittest

from src.core.generator_primitives import (
    background_color,
    background_regions,
    bbox_of_mask,
    best_candidate,
    complete_by_symmetry,
    components4,
    crop_bbox,
    detect_period,
    enclosed_regions,
    fill_periodic_holes,
    mask_color,
    move_content_to_edge,
    nonzero_colors,
    overlay,
    raycast,
    select_color_by_rank,
    select_object,
    slide_layer,
    split_by_separators,
    take_panel,
    translate_layer,
    unique_or_reject,
    zip_panels,
)


class GeneratorPrimitivesTest(unittest.TestCase):
    def test_color_and_mask_helpers(self):
        grid = [
            [0, 2, 2],
            [3, 0, 2],
            [3, 3, 0],
        ]

        self.assertEqual(background_color(grid), 0)
        self.assertEqual(background_color(grid, policy="mode", tie="lowest"), 0)
        self.assertEqual(nonzero_colors(grid), {2, 3})
        self.assertEqual(mask_color(grid, 2), {(0, 1), (0, 2), (1, 2)})
        self.assertEqual(bbox_of_mask(mask_color(grid, 3)), (1, 0, 2, 1))
        self.assertEqual(select_color_by_rank(grid, rank=0, largest=True), 2)

    def test_components_and_object_selection(self):
        grid = [
            [1, 1, 0, 2],
            [0, 1, 0, 2],
            [3, 0, 2, 2],
        ]

        objects = components4(grid)
        largest = select_object(objects, key="size", largest=True)
        smallest = select_object(objects, key="size", largest=False)

        self.assertEqual(len(objects), 3)
        self.assertIsNotNone(largest)
        self.assertEqual(largest.color, 2)
        self.assertEqual(largest.size, 4)
        self.assertIsNotNone(smallest)
        self.assertEqual(smallest.color, 3)
        self.assertEqual(select_object(objects, key=lambda obj: obj.bbox, largest=False).color, 1)

    def test_crop_overlay_and_translation(self):
        grid = [
            [0, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]
        self.assertEqual(crop_bbox(grid, (0, 1, 1, 1)), [[1], [1]])
        self.assertEqual(
            translate_layer(grid, (0, 1)),
            [
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 0],
            ],
        )
        self.assertEqual(
            overlay([[1, 1], [1, 1]], [[0, 2], [None, 3]]),
            [[1, 2], [1, 3]],
        )

    def test_slide_layer_policies(self):
        grid = [
            [0, 1, 0],
            [0, 0, 2],
            [0, 0, 0],
        ]

        self.assertEqual(
            slide_layer(grid, 1, (1, 0), vacated="background", collision="overwrite"),
            [
                [0, 0, 0],
                [0, 1, 2],
                [0, 0, 0],
            ],
        )
        self.assertEqual(
            slide_layer(grid, 1, (1, 1), vacated="unknown", collision="overwrite"),
            [
                [0, None, 0],
                [0, 0, 1],
                [0, 0, 0],
            ],
        )
        with self.assertRaises(ValueError):
            slide_layer(grid, 1, (1, 1), collision="error")

    def test_move_content_to_edge_and_panels(self):
        grid = [
            [0, 0, 0, 0, 0],
            [0, 1, 0, 9, 0],
            [0, 0, 0, 0, 0],
            [2, 2, 2, 2, 2],
            [0, 3, 0, 9, 0],
        ]

        self.assertEqual(
            move_content_to_edge([[0, 0, 0], [0, 4, 0], [0, 0, 0]], vertical="top", horizontal="left"),
            [[4, 0, 0], [0, 0, 0], [0, 0, 0]],
        )
        self.assertEqual(len(split_by_separators(grid, "rows", separator_color=2)), 2)
        self.assertEqual(take_panel(grid, 1, 1, row_separators=[3], col_separators=[2]), [[9, 0]])
        self.assertEqual(
            zip_panels([[1, 0], [2, 2]], [[0, 3], [2, 0]], op="xor"),
            [[1, 3], [0, 2]],
        )

    def test_raycast_regions_period_and_symmetry(self):
        grid = [
            [5, 5, 5, 5],
            [5, 0, 0, 5],
            [5, 0, 5, 5],
            [5, 5, 5, 0],
        ]

        ray = raycast(grid, (1, 0), (0, 1), blockers={5})
        self.assertEqual([step.position for step in ray], [(1, 1), (1, 2), (1, 3)])
        self.assertEqual(len(background_regions(grid)), 2)
        self.assertEqual(len(enclosed_regions(grid)), 1)

        periodic = [
            [1, 2, 1, 2],
            [3, 4, 3, 4],
            [1, 2, 1, 2],
        ]
        self.assertEqual(detect_period(periodic), (2, 2))
        self.assertIsNone(detect_period(periodic, max_period=1))
        self.assertEqual(
            fill_periodic_holes([[1, 0, 1], [2, 0, 2]], 1, 2),
            [[1, 0, 1], [2, 0, 2]],
        )
        self.assertEqual(
            complete_by_symmetry([[1, 0, 0], [2, 0, 2]], symmetry="lr"),
            [[1, 0, 1], [2, 0, 2]],
        )

    def test_candidate_helpers(self):
        self.assertEqual(best_candidate(["aa", "b", "ccc"], score=len), "b")
        self.assertEqual(best_candidate(["aa", "b", "ccc"], score=len, largest=True), "ccc")
        with self.assertRaises(ValueError):
            best_candidate(["a", "b"], score=len)

        self.assertEqual(unique_or_reject([[1], [1]], key=tuple), [1])
        with self.assertRaises(ValueError):
            unique_or_reject([1, 2])


if __name__ == "__main__":
    unittest.main()
