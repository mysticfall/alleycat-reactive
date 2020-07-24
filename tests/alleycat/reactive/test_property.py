import unittest
from collections import deque
from typing import TypeVar, List, Callable, Any

from returns.maybe import Maybe, Some
from rx import operators as ops

from alleycat.reactive import ReactiveProperty

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

        self.assertEqual(cm.exception.args[0], "Name is a required argument.")

        self.assertEqual(ReactiveProperty("value").name, "value")
        self.assertEqual(ReactiveProperty("value", Maybe.from_value(3)).init_value, Some(3))
        self.assertEqual(ReactiveProperty("value", Maybe.from_value("test")).init_value, Some("test"))
        self.assertEqual(ReactiveProperty("value", read_only=True).read_only, True)
        self.assertEqual(ReactiveProperty("value", read_only=False).read_only, False)

        pre_modifiers = deque([lambda obj, v: v + obj.increment])
        post_modifiers = deque([lambda obj, obs: obs.pipe(ops.map(lambda v: v * obj.multiplier))])

        self.assertEqual(ReactiveProperty("value", pre_modifiers=pre_modifiers).pre_modifiers, pre_modifiers)
        self.assertEqual(ReactiveProperty("value", post_modifiers=post_modifiers).post_modifiers, post_modifiers)

    def test_read_value(self):
        prop = ReactiveProperty("name", Some("test"))

        self.assertEqual(prop.__get__({}), "test")

    def test_write_value(self):
        prop = ReactiveProperty("name", Some("ABC"))

        prop.__set__(self.fixture, "123")

        self.assertEqual(prop.__get__(self.fixture), "123")

    def test_lazy_init(self):
        prop = ReactiveProperty("name")

        with self.assertRaises(AttributeError) as cm:
            ReactiveProperty("name").__get__({})

        self.assertEqual(cm.exception.args[0], "Property 'name' is not initialized yet.")

        prop.__set__(self.fixture, "simple")

        self.assertEqual(prop.__get__(self.fixture), "simple")

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

        self.assertEqual(last_changed, ["Do, Re, Mi", "ABC"])

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

        self.assertEqual(last_changed, ["ABC"])

    def test_multiple_properties(self):
        name = ReactiveProperty("name", Some("Slim Shady"))
        age = ReactiveProperty("age", Some(26))

        self.assertEqual(name.__get__(self.fixture), "Slim Shady")
        self.assertEqual(age.__get__(self.fixture), 26)

        name.__set__(self.fixture, "The real Slim Shady")
        age.__set__(self.fixture, 47)  # Yeah, time flies fast.

        self.assertEqual(name.__get__(self.fixture), "The real Slim Shady")
        self.assertEqual(age.__get__(self.fixture), 47)

    def test_access_after_dispose(self):
        value = ReactiveProperty("value")
        value.__set__(self.fixture, 1)

        data = value._get_data(self.fixture)

        self.assertIs(data.disposed, False)

        data.dispose()

        self.assertIs(data.disposed, True)

        self.assertEqual(value.__get__(self.fixture), 1)

        expected = "Property 'value' has been disposed."

        def assert_attr_error(fun: Callable[[], Any]):
            with self.assertRaises(AttributeError) as cm:
                fun()

            self.assertEqual(cm.exception.args[0], expected)

        assert_attr_error(lambda: value.__set__(self.fixture, 1))
        assert_attr_error(lambda: value.observable(self.fixture))
        assert_attr_error(lambda: data.dispose())


if __name__ == '__main__':
    unittest.main()
