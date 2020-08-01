import unittest
from typing import Any, Callable

from rx import operators as ops

from alleycat.reactive import ReactiveObject, observe, from_value, from_observable


class ReactiveObjectTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()

    def tearDown(self) -> None:
        if not self.fixture.disposed:
            self.fixture.dispose()

    def test_observe(self):
        values = []
        doubles = []

        def value_changed(value):
            values.append(value)

        def doubled_value_changed(value):
            doubles.append(value)

        # Both of the styles should work in the same way:
        self.fixture.observe("value").subscribe(value_changed)
        observe(self.fixture.double).subscribe(doubled_value_changed)

        for i in range(1, 5):
            self.fixture.value = i

        self.assertEqual([0, 1, 2, 3, 4], values)
        self.assertEqual([0, 2, 4, 6, 8], doubles)

    def test_dispose(self):
        self.assertEqual(False, self.fixture.disposed)

        self.fixture.dispose()

        self.assertEqual(True, self.fixture.disposed)

    def test_dispose_event(self):
        disposed = False

        def value_changed(value):
            nonlocal disposed
            disposed = value

        observe(self.fixture.disposed).subscribe(value_changed)

        self.fixture.dispose()

        self.assertEqual(True, disposed)

    def test_complete_before_dispose(self):
        completed = {"value": False, "double": False}

        def on_complete(key: str):
            self.assertEqual(False, self.fixture.disposed)

            completed[key] = True

        observe(self.fixture.value).subscribe(on_completed=on_complete("value"))
        observe(self.fixture, "double").subscribe(on_completed=on_complete("double"))

        self.fixture.dispose()

        self.assertEqual(True, completed["value"])
        self.assertEqual(True, completed["double"])

    def test_access_after_dispose(self):
        def assert_error(fun: Callable[[], Any], expected: str):
            with self.assertRaises(Exception) as cm:
                fun()

            self.assertEqual(expected, cm.exception.args[0])

        self.fixture.dispose()

        def modify_value():
            self.fixture.value = 10

        assert_error(modify_value, "Property 'value' has been disposed.")

        for key in ["value", "double"]:
            assert_error(lambda: self.fixture.observe(key), "Cannot observe a disposed object.")

        assert_error(lambda: self.fixture.dispose(), "The object has already been disposed.")

        self.assertEqual(0, self.fixture.value)
        self.assertEqual(0, self.fixture.double)


class Fixture(ReactiveObject):
    value = from_value(0)

    double = from_observable()

    def __init__(self):
        self.double = observe(self.value).pipe(ops.map(lambda v: v * 2))


if __name__ == '__main__':
    unittest.main()
