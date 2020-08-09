import unittest
from typing import TypeVar, Callable, Any

from returns.maybe import Some
from rx import operators as ops

from alleycat.reactive import ReactiveProperty, functions as rv, ReactiveView

T = TypeVar("T")


# noinspection DuplicatedCode
class ReactivePropertyTest(unittest.TestCase):

    def test_initialization(self):
        self.assertEqual(Some(3), ReactiveProperty(Some(3)).init_value)
        self.assertEqual(Some("test"), ReactiveProperty(Some("test")).init_value)
        self.assertEqual(False, ReactiveProperty().read_only)
        self.assertEqual(True, ReactiveProperty(read_only=True).read_only)
        self.assertEqual(False, ReactiveProperty(read_only=False).read_only)

    def test_name_inference(self):
        class Fixture:
            value = ReactiveProperty(Some("test"))

        self.assertEqual(Fixture.value.name, "value")

    def test_read_value(self):
        class Fixture:
            value = ReactiveProperty(Some("test"))

        self.assertEqual("test", Fixture().value)

    def test_write_value(self):
        class Fixture:
            value = ReactiveProperty(Some("ABC"))

        fixture = Fixture()
        fixture.value = "123"

        self.assertEqual("123", fixture.value)

    def test_read_only(self):
        class Fixture:
            value = ReactiveProperty(Some("Waltzing"), read_only=True)

        with self.assertRaises(AttributeError) as cm:
            Fixture().value = "Matilda"

        self.assertEqual("Cannot modify a read-only property.", cm.exception.args[0])

    def test_lazy_read_only(self):
        class Fixture:
            value = ReactiveProperty(read_only=True)

            def __init__(self):
                self.value = "Lazy"

        fixture = Fixture()

        self.assertEqual(fixture.value, "Lazy")

        with self.assertRaises(AttributeError) as cm:
            fixture.value = "Fox"

        self.assertEqual("Cannot modify a read-only property.", cm.exception.args[0])

    def test_lazy_init(self):
        class Fixture:
            value = ReactiveProperty()

        fixture = Fixture()

        with self.assertRaises(AttributeError) as cm:
            # noinspection PyStatementEffect
            fixture.value

        self.assertEqual("Property 'value' is not initialized yet.", cm.exception.args[0])

        fixture.value = "simple"

        self.assertEqual("simple", fixture.value)

    def test_observe(self):
        class Fixture:
            value = ReactiveProperty(Some("Do, Re, Mi"))

        fixture = Fixture()

        obs = Fixture.value.observable(fixture)

        self.assertIsNotNone(obs)

        last_changed = []

        obs.subscribe(last_changed.append)

        # By now, you should be able to hum the rest of the song, if you are cultured :P
        fixture.value = "ABC"

        self.assertEqual(["Do, Re, Mi", "ABC"], last_changed)

    def test_lazy_observe(self):
        class Fixture:
            value = ReactiveProperty()

        fixture = Fixture()

        obs = Fixture.value.observable(fixture)

        self.assertIsNotNone(obs)

        last_changed = []

        obs.subscribe(last_changed.append)

        fixture.value = "ABC"

        self.assertEqual(["ABC"], last_changed)

    def test_multiple_properties(self):
        class Fixture:
            name = ReactiveProperty(Some("Slim Shady"))
            age = ReactiveProperty(Some(26))

        fixture = Fixture()

        self.assertEqual("Slim Shady", fixture.name)
        self.assertEqual(26, fixture.age)

        fixture.name = "The real Slim Shady"
        fixture.age = 47  # Yeah, time flies fast.

        self.assertEqual("The real Slim Shady", fixture.name)
        self.assertEqual(47, fixture.age)

    def test_access_after_dispose(self):
        class Fixture:
            value = ReactiveProperty(Some(1))

        fixture = Fixture()

        data = Fixture.value._get_data(fixture)

        self.assertIs(False, data.disposed)

        data.dispose()

        self.assertIs(True, data.disposed)

        self.assertEqual(1, fixture.value)

        expected = "Property 'value' has been disposed."

        def assert_attr_error(fun: Callable[[], Any]):
            with self.assertRaises(AttributeError) as cm:
                fun()

            self.assertEqual(expected, cm.exception.args[0])

        assert_attr_error(lambda: setattr(fixture, "value", 1))
        assert_attr_error(lambda: Fixture.value.observable(fixture))
        assert_attr_error(lambda: data.dispose())

    def test_class_attribute(self):
        class Fixture:
            value = rv.from_value(True)

        prop = Fixture.value

        self.assertEqual(ReactiveProperty, type(prop))
        self.assertEqual("value", prop.name)

    def test_map(self):
        class Fixture:
            name = ReactiveProperty(Some("wolf"))

            song = name.map(lambda n: f"Who's afraid of a big bad {n}?")

        fixture = Fixture()

        self.assertEqual("Who's afraid of a big bad wolf?", fixture.song)

        fixture.song = "cat"

        self.assertEqual("Who's afraid of a big bad cat?", fixture.song)

        fixture.name = "dog"

        self.assertEqual("Who's afraid of a big bad cat?", fixture.song)

    def test_pipe(self):
        class Fixture:
            name = ReactiveProperty(Some("wolf"))

            song = name.pipe(ops.map(lambda n: f"Who's afraid of a big bad {n}?"), ops.map(str.upper))

        fixture = Fixture()

        self.assertEqual("WHO'S AFRAID OF A BIG BAD WOLF?", fixture.song)

        fixture.song = "cat"

        self.assertEqual("WHO'S AFRAID OF A BIG BAD CAT?", fixture.song)

        fixture.name = "dog"

        self.assertEqual("WHO'S AFRAID OF A BIG BAD CAT?", fixture.song)

    def test_premap(self):
        def validate(number: int) -> int:
            if number < 1:
                raise AttributeError("Value must be a positive integer.")

            return number

        class Fixture:
            value = ReactiveProperty(Some(1)).premap(lambda v: v * 2)

            positive_only = value.premap(validate)

        fixture = Fixture()

        self.assertEqual(2, fixture.value)
        self.assertEqual(2, fixture.positive_only)

        fixture.value = -2

        self.assertEqual(-4, fixture.value)

        with self.assertRaises(AttributeError) as cm:
            fixture.positive_only = -2

        self.assertEqual("Value must be a positive integer.", cm.exception.args[0])

        fixture.positive_only = 3

        self.assertEqual(6, fixture.positive_only)

    def test_as_view(self):
        class Fixture:
            name = ReactiveProperty(Some("Virginia O'Brien"))

            star = name.as_view()

        self.assertEqual(ReactiveView, type(Fixture.star))

        fixture = Fixture()

        stars = []

        rv.observe(fixture.star).subscribe(stars.append)

        self.assertEqual("Virginia O'Brien", fixture.star)
        self.assertEqual(["Virginia O'Brien"], stars)

        fixture.name = "Judy Garland"

        self.assertEqual("Judy Garland", fixture.star)
        self.assertEqual(["Virginia O'Brien", "Judy Garland"], stars)


if __name__ == '__main__':
    unittest.main()
