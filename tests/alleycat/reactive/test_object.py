import unittest

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


class Fixture(ReactiveObject):
    value: int = from_value(0)

    def __init__(self, init_value=0):
        self.value = init_value


if __name__ == '__main__':
    unittest.main()
