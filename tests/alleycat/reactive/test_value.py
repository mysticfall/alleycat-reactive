import unittest

from rx import operators as ops

from alleycat.reactive import functions as rv


class ReactiveValueTest(unittest.TestCase):

    def test_eager_init(self):
        class CrowsCounter:
            animal = rv.new_property()

            crows = animal.as_view().pipe(
                ops.map(str.lower),
                ops.filter(lambda v: v == "crow"),
                ops.map(lambda _: 1),
                ops.scan(lambda v1, v2: v1 + v2, 0))

        counting = CrowsCounter()

        counting.animal = "Crow"
        counting.animal = "cat"

        counts = []

        # Even though this is the first reference of 'crows', it correctly reports the aggregated data,
        # because it was eagerly initialized after the instantiation.
        rv.observe(counting.crows).subscribe(counts.append)

        self.assertEqual(1, counting.crows)
        self.assertEqual([1], counts)

        counting.animal = "CROW"
        counting.animal = "dog"

        self.assertEqual(2, counting.crows)
        self.assertEqual([1, 2], counts)


if __name__ == '__main__':
    unittest.main()
