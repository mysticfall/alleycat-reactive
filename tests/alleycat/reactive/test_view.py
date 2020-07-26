import unittest
from typing import List, Callable, Any

import rx
from returns.maybe import Some
from rx.subject import BehaviorSubject

from alleycat.reactive import ReactiveView, from_view


# noinspection DuplicatedCode
class ReactiveViewTest(unittest.TestCase):

    def test_initialization(self):
        init_obs = rx.empty()

        self.assertEqual(Some(init_obs), ReactiveView(Some(init_obs)).init_observable)
        self.assertEqual(True, ReactiveView(read_only=True).read_only)
        self.assertEqual(False, ReactiveView(read_only=False).read_only)

    def test_name_inference(self):
        class Fixture:
            value = ReactiveView(Some(rx.of(1, 2, 3)))

        self.assertEqual(Fixture.value.name, "value")

    def test_read_value(self):
        subject = BehaviorSubject(1)

        class Fixture:
            value = ReactiveView(Some(subject))

        self.assertEqual(1, Fixture().value)

        subject.on_next(2)

        self.assertEqual(2, Fixture().value)

        subject.on_next(3)

        self.assertEqual(3, Fixture().value)

    def test_write_value(self):
        class Fixture:
            value = ReactiveView(Some(rx.of(1)))

        fixture = Fixture()
        fixture.value = rx.of(2, 3)

        self.assertEqual(3, fixture.value)

    def test_read_only(self):
        class Fixture:
            value = ReactiveView(Some(rx.of(1)), read_only=True)

        with self.assertRaises(AttributeError) as cm:
            Fixture().value = rx.of(2, 3)

        self.assertEqual("Cannot modify a read-only property.", cm.exception.args[0])

    def test_lazy_read_only(self):
        class Fixture:
            value = ReactiveView(read_only=True)

            def __init__(self):
                self.value = rx.of("Lazy")

        fixture = Fixture()

        self.assertEqual(fixture.value, "Lazy")

        with self.assertRaises(AttributeError) as cm:
            fixture.value = "Fox"

        self.assertEqual("Cannot modify a read-only property.", cm.exception.args[0])

    def test_lazy_init(self):
        class Fixture:
            value = ReactiveView()

        fixture = Fixture()

        with self.assertRaises(AttributeError) as cm:
            # noinspection PyStatementEffect
            fixture.value

        self.assertEqual("Property 'value' is not initialized yet.", cm.exception.args[0])

        fixture.value = rx.of("simple")

        self.assertEqual("simple", fixture.value)

    def test_observe(self):
        subject = BehaviorSubject("Do, Re, Mi")

        class Fixture:
            value = ReactiveView(Some(subject))

        fixture = Fixture()

        obs = Fixture.value.observable(fixture)

        self.assertIsNotNone(obs)

        last_changed: List[str] = []

        def value_changed(value):
            nonlocal last_changed
            last_changed.append(value)

        obs.subscribe(value_changed)

        # By now, you should be able to hum the rest of the song, if you are cultured :P
        subject.on_next("ABC")

        self.assertEqual(["Do, Re, Mi", "ABC"], last_changed)

    def test_lazy_observe(self):
        class Fixture:
            value = ReactiveView()

        fixture = Fixture()

        obs = Fixture.value.observable(fixture)

        self.assertIsNotNone(obs)

        last_changed: List[str] = []

        def value_changed(value):
            nonlocal last_changed
            last_changed.append(value)

        obs.subscribe(value_changed)

        fixture.value = rx.of("ABC")

        self.assertEqual(["ABC"], last_changed)

    def test_multiple_properties(self):
        name_subject = BehaviorSubject("Slim Shady")
        age_subject = BehaviorSubject(26)

        class Fixture:
            name = ReactiveView(Some(name_subject))
            age = ReactiveView()

            def __init__(self):
                self.age = age_subject

        fixture = Fixture()

        self.assertEqual("Slim Shady", fixture.name)
        self.assertEqual(26, fixture.age)

        name_subject.on_next("The real Slim Shady")
        age_subject.on_next(47)  # Yeah, time flies fast.

        self.assertEqual("The real Slim Shady", fixture.name)
        self.assertEqual(47, fixture.age)

    def test_access_after_dispose(self):
        class Fixture:
            value = ReactiveView(Some(rx.of(1)))

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

        assert_attr_error(lambda: setattr(fixture, "value", rx.of(2)))
        assert_attr_error(lambda: Fixture.value.observable(fixture))
        assert_attr_error(lambda: data.dispose())

    def test_class_attribute(self):
        class Fixture:
            value = from_view(rx.empty())

        prop = Fixture.value

        self.assertEqual(ReactiveView, type(prop))
        self.assertEqual("value", prop.name)


if __name__ == '__main__':
    unittest.main()
