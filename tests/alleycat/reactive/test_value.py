import unittest

from returns.functions import identity
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

    def test_name_inference(self):
        class Fixture:
            shallow = rv.new_property(1)

            passed = rv.new_property(1).map(lambda v: v + 1).map(lambda v: v + 1).as_view()

            deep = rv.combine_latest(shallow, passed)(ops.map(identity)).map(identity)

        self.assertEqual("shallow", Fixture.shallow.name)
        self.assertEqual("passed", Fixture.passed.name)
        self.assertEqual("deep", Fixture.deep.name)

    def test_emitting_order(self):
        class Fixture:
            value = rv.from_value(1)

            doubled = value.as_view().map(lambda v: v * 2)

        values = []

        fixture = Fixture()

        rv.observe(fixture.value).subscribe(values.append)
        rv.observe(fixture.doubled).subscribe(values.append)

        self.assertEqual([1, 2], values)

        fixture.value = 3

        self.assertEqual([1, 2, 6, 3], values)


if __name__ == '__main__':
    unittest.main()
