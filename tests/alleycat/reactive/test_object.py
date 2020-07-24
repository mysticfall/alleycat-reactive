import unittest
from typing import Any, Callable

from alleycat.reactive import ReactiveObject, observe, from_value


class ReactiveObjectTest(unittest.TestCase):
    def test_dispose(self):
        with Fixture() as obj:
            self.assertEqual(obj.disposed, False)

            obj.dispose()

            self.assertEqual(obj.disposed, True)

    def test_dispose_event(self):
        with Fixture() as obj:
            disposed = False

            def value_changed(value):
                nonlocal disposed
                disposed = value

            observe(obj.disposed).subscribe(value_changed)

            obj.dispose()

            self.assertEqual(disposed, True)

    def test_complete_before_dispose(self):
        with Fixture() as obj:
            completed = False

            def on_complete():
                self.assertEqual(obj.disposed, False)

                nonlocal completed
                completed = True

            observe(obj.value).subscribe(on_completed=on_complete())

            obj.dispose()

            self.assertEqual(completed, True)

    def test_access_after_dispose(self):
        def assert_error(fun: Callable[[], Any], expected: str):
            with self.assertRaises(Exception) as cm:
                fun()

            self.assertEqual(cm.exception.args[0], expected)

        with Fixture() as obj:
            obj.dispose()

            self.assertEqual(obj.value, 0)

            def modify_value():
                obj.value = 10

            assert_error(modify_value, "Property 'value' has been disposed.")
            assert_error(lambda: obj.observe("value"), "Cannot observe a disposed object.")
            assert_error(lambda: obj.dispose(), "The object has already been disposed.")


class Fixture(ReactiveObject):
    value: int = from_value(0)

    def __init__(self, init_value=0):
        self.value = init_value


if __name__ == '__main__':
    unittest.main()
