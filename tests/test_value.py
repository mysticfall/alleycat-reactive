import gc
import unittest

import rx
from returns.functions import identity
from rx import operators as ops

from alleycat.reactive import functions as rv, RP, RV
from alleycat.reactive.value import DATA_KEY


class ReactiveValueTest(unittest.TestCase):

    def test_eager_init(self):
        class CrowsCounter:
            animal: RP[str] = rv.new_property()

            crows: RV[int] = animal.as_view().pipe(lambda _: (
                ops.map(str.lower),
                ops.filter(lambda v: v == "crow"),
                ops.map(lambda _: 1),
                ops.scan(lambda v1, v2: v1 + v2, 0)))

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
            shallow: RP[int] = rv.new_property(1)

            passed: RV[int] = rv.new_property(1).map(lambda _, v: v + 1).map(lambda _, v: v + 1).as_view()

            deep: RV[int] = rv.combine_latest(shallow, passed)(ops.map(identity)).map(lambda _: identity)

        self.assertEqual("shallow", Fixture.shallow.name)
        self.assertEqual("passed", Fixture.passed.name)
        self.assertEqual("deep", Fixture.deep.name)

    def test_emitting_order(self):
        class Fixture:
            value: RP[int] = rv.from_value(1)

            doubled: RV[int] = value.as_view().map(lambda _, v: v * 2)

        values = []

        fixture = Fixture()

        rv.observe(fixture.value).subscribe(values.append)
        rv.observe(fixture.doubled).subscribe(values.append)

        self.assertEqual([1, 2], values)

        fixture.value = 3

        self.assertEqual([1, 2, 6, 3], values)

    def test_extending_attributes(self):
        class GrandParent:
            inherited: RP[str] = rv.from_value("A")

            extended: RP[int] = rv.from_value(1)

            from_init: RP[int] = rv.from_value(1)

        class Parent(GrandParent):
            extended: RP[int] = GrandParent.extended.map(lambda _, v: v * 2)

        class Child(Parent):
            extended: RP[int] = Parent.extended.map(lambda _, v: v * 3)

        fixture = Child()

        self.assertEqual("A", fixture.inherited)
        self.assertEqual(6, fixture.extended)

        fixture.extended = 2

        self.assertEqual(12, fixture.extended)

    def test_init_hook(self):
        class Bangles:
            song: RP[str] = rv.new_property()

            hits: RV[str] = song.as_view().pipe(lambda _: (ops.map(lambda _: 1), ops.scan(lambda v1, v2: v1 + v2, 0)))

            def __init__(self, hit, *years_active, **members):
                self.hit = hit
                self.years_active = years_active
                self.members = members

        the_bangles = {
            "vocal": "Susanna Hoffs",
            "drums": "Debbi Peterson",
            "bass": "Michael Steele",
            "guitar": "Vicki Peterson"
        }

        bangles = Bangles("Walk Like an Egyptian", "1981–1989", "1998–present", **the_bangles)

        bangles.song = "If She Knew What She Wants"
        bangles.song = "Manic Monday"

        self.assertEqual("Walk Like an Egyptian", bangles.hit)
        self.assertEqual(("1981–1989", "1998–present"), bangles.years_active)
        self.assertIsNotNone(bangles.members)
        self.assertEqual("Susanna Hoffs", bangles.members["vocal"])

        # Eager initialization should still work with an explict constructor:
        self.assertEqual(2, bangles.hits)

    def test_del_hook(self):
        calls = []

        class Fixture:
            tick: RV[int] = rv.from_observable(rx.of(1)).map(lambda _, v: "tick!")

            def __init__(self, invokes):
                self.invokes = invokes

                rv.observe(self, "tick").subscribe(print)

            def __del__(self):
                data = getattr(self, DATA_KEY)
                self.invokes.append(data["tick"].disposed)

        # noinspection PyUnusedLocal
        fixture = Fixture(calls)

        del fixture

        gc.collect()

        self.assertEqual([True], calls)


if __name__ == '__main__':
    unittest.main()
