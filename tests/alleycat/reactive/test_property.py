import unittest
from collections import deque
from typing import TypeVar, List, Callable, Any

from returns.maybe import Maybe, Some
from rx import operators as ops

from alleycat.reactive import ReactiveProperty, from_value

T = TypeVar("T")


# noinspection DuplicatedCode
class ReactivePropertyTest(unittest.TestCase):
    class Fixture:
        pass

    fixture: Fixture

    def setUp(self) -> None:
        super().setUp()

        self.fixture = self.Fixture()

    def test_initialization(self):
        with self.assertRaises(ValueError) as cm:
            # noinspection PyTypeChecker
            ReactiveProperty(None)

        self.assertEqual("Name is a required argument.", cm.exception.args[0])

        self.assertEqual("value", ReactiveProperty("value").name)
        self.assertEqual(Some(3), ReactiveProperty("value", Maybe.from_value(3)).init_value)
        self.assertEqual(Some("test"), ReactiveProperty("value", Maybe.from_value("test")).init_value)
        self.assertEqual(True, ReactiveProperty("value", read_only=True).read_only)
        self.assertEqual(False, ReactiveProperty("value", read_only=False).read_only)

        pre_modifiers = deque([lambda obj, v: v + obj.increment])
        post_modifiers = deque([lambda obj, obs: obs.pipe(ops.map(lambda v: v * obj.multiplier))])

        self.assertEqual(pre_modifiers, ReactiveProperty("value", pre_modifiers=pre_modifiers).pre_modifiers)
        self.assertEqual(post_modifiers, ReactiveProperty("value", post_modifiers=post_modifiers).post_modifiers)

    def test_read_value(self):
        prop = ReactiveProperty("name", Some("test"))

        self.assertEqual("test", prop.__get__({}))

    def test_write_value(self):
        prop = ReactiveProperty("name", Some("ABC"))

        prop.__set__(self.fixture, "123")

        self.assertEqual("123", prop.__get__(self.fixture))

    def test_read_only(self):
        prop = ReactiveProperty("waltzing", Some("matilda"), read_only=True)

        with self.assertRaises(AttributeError) as cm:
            prop.__set__(self.fixture, "ants")

        self.assertEqual("Cannot modify a read-only property.", cm.exception.args[0])

    def test_lazy_init(self):
        prop = ReactiveProperty("name")

        with self.assertRaises(AttributeError) as cm:
            ReactiveProperty("name").__get__({})

        self.assertEqual("Property 'name' is not initialized yet.", cm.exception.args[0])

        prop.__set__(self.fixture, "simple")

        self.assertEqual("simple", prop.__get__(self.fixture))

    def test_observe(self):
        prop = ReactiveProperty("name", Some("Do, Re, Mi"))

        obs = prop.observable(self.fixture)

        self.assertIsNotNone(obs)

        last_changed: List[str] = []

        def value_changed(value):
            nonlocal last_changed
            last_changed.append(value)

        obs.subscribe(value_changed)

        # By now, you should be able to hum the rest of the song, if you are cultured :P
        prop.__set__(self.fixture, "ABC")

        self.assertEqual(["Do, Re, Mi", "ABC"], last_changed)

    def test_lazy_observe(self):
        prop = ReactiveProperty("name")

        obs = prop.observable(self.fixture)

        self.assertIsNotNone(obs)

        last_changed: List[str] = []

        def value_changed(value):
            nonlocal last_changed
            last_changed.append(value)

        obs.subscribe(value_changed)

        prop.__set__(self.fixture, "ABC")

        self.assertEqual(["ABC"], last_changed)

    def test_multiple_properties(self):
        name = ReactiveProperty("name", Some("Slim Shady"))
        age = ReactiveProperty("age", Some(26))

        self.assertEqual("Slim Shady", name.__get__(self.fixture))
        self.assertEqual(26, age.__get__(self.fixture))

        name.__set__(self.fixture, "The real Slim Shady")
        age.__set__(self.fixture, 47)  # Yeah, time flies fast.

        self.assertEqual("The real Slim Shady", name.__get__(self.fixture))
        self.assertEqual(47, age.__get__(self.fixture))

    def test_access_after_dispose(self):
        value = ReactiveProperty("value")
        value.__set__(self.fixture, 1)

        data = value._get_data(self.fixture)

        self.assertIs(False, data.disposed)

        data.dispose()

        self.assertIs(True, data.disposed)

        self.assertEqual(1, value.__get__(self.fixture))

        expected = "Property 'value' has been disposed."

        def assert_attr_error(fun: Callable[[], Any]):
            with self.assertRaises(AttributeError) as cm:
                fun()

            self.assertEqual(expected, cm.exception.args[0])

        assert_attr_error(lambda: value.__set__(self.fixture, 1))
        assert_attr_error(lambda: value.observable(self.fixture))
        assert_attr_error(lambda: data.dispose())

    def test_class_attribute(self):
        class Fixture:
            value = from_value(True)

        prop = Fixture.value

        self.assertEqual(ReactiveProperty, type(prop))
        self.assertEqual("value", prop.name)


if __name__ == '__main__':
    unittest.main()
