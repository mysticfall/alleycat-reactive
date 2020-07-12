import unittest

from rx import operators as ops

from alleycat.reactive import ReactiveObject, ReactiveProperty, observe, extend


class ReactivePropertyTestCase(unittest.TestCase):
    def test_initialization(self):
        with Fixture(init_value=10) as obj1, Fixture(init_value=20) as obj2:
            self.assertEqual(obj1.value, 10)
            self.assertEqual(obj2.value, 20)

    def test_modification(self):
        with Fixture() as obj1, Fixture() as obj2:
            obj1.value = 10
            obj2.value = 20

            self.assertEqual(obj1.value, 10)
            self.assertEqual(obj2.value, 20)

            obj1.value = 30

            self.assertEqual(obj1.value, 30)
            self.assertEqual(obj2.value, 20)

    def test_observe(self):
        with Fixture(init_value=10) as obj:
            observable = observe(obj.value)

            self.assertIsNotNone(observable)

            last_changed = obj.value

            def value_changed(value):
                nonlocal last_changed
                last_changed = value

            observable.subscribe(value_changed)

            obj.value = 30

            self.assertEqual(last_changed, 30)

    def test_extend(self):
        with ExtendedFixture(increment=5, multiplier=2) as obj:
            observable = observe(obj.value)

            self.assertIsNotNone(observable)

            observed_change = obj.value

            def value_changed(value):
                nonlocal observed_change
                observed_change = value

            observable.subscribe(value_changed)

            obj.value = 30

            self.assertEqual(observed_change, 70)
            self.assertEqual(obj.value, 70)


class Fixture(ReactiveObject):
    value: int = ReactiveProperty()

    def __init__(self, init_value=0):
        self.value = init_value


class ExtendedFixture(Fixture):
    value: int = extend(Fixture.value,
                        pre_modifier=lambda obj, v: v + obj.increment,
                        post_modifier=lambda obj, obs: obs.pipe(ops.map(lambda v: v * obj.multiplier)))

    def __init__(self, init_value=0, increment=0, multiplier=1):
        self.increment = increment
        self.multiplier = multiplier

        super().__init__(init_value)


if __name__ == '__main__':
    unittest.main()
