import unittest
from typing import Callable, Any

import rx
from returns.context import RequiresContext
from rx import operators as ops
from rx.subject import BehaviorSubject

from alleycat.reactive import ReactiveView, functions as rv, RV


# noinspection DuplicatedCode
class ReactiveViewTest(unittest.TestCase):

    def test_initialization(self):
        init_value = RequiresContext.from_value(rx.empty())

        self.assertEqual(True, ReactiveView(init_value).read_only)
        self.assertEqual(True, ReactiveView(init_value, True).read_only)
        self.assertEqual(False, ReactiveView(init_value, False).read_only)

    def test_name_inference(self):
        class Fixture:
            value: RV[int] = ReactiveView(RequiresContext.from_value(rx.of(1, 2, 3)))

        self.assertEqual(Fixture.value.name, "value")

    def test_read_value(self):
        subject = BehaviorSubject(1)

        class Fixture:
            value: RV[int] = ReactiveView(RequiresContext.from_value(subject))

        self.assertEqual(1, Fixture().value)

        subject.on_next(2)

        self.assertEqual(2, Fixture().value)

        subject.on_next(3)

        self.assertEqual(3, Fixture().value)

    def test_write_value(self):
        class Fixture:
            value: RV[int] = ReactiveView(RequiresContext.from_value(rx.of(1)), read_only=False)

        fixture = Fixture()
        fixture.value = rx.of(2, 3)

        self.assertEqual(3, fixture.value)

    def test_read_only(self):
        class Fixture:
            value: RV[int] = ReactiveView(RequiresContext.from_value(rx.of(1)), read_only=True)

        with self.assertRaises(AttributeError) as cm:
            Fixture().value = rx.of(2, 3)

        self.assertEqual("Cannot modify a read-only property.", cm.exception.args[0])

    def test_observe(self):
        subject = BehaviorSubject("Do, Re, Mi")

        class Fixture:
            value: RV[str] = ReactiveView(RequiresContext.from_value(subject))

        fixture = Fixture()

        obs = Fixture.value.observable(fixture)

        self.assertIsNotNone(obs)

        last_changed = []

        obs.subscribe(last_changed.append)

        # By now, you should be able to hum the rest of the song, if you are cultured :P
        subject.on_next("ABC")

        self.assertEqual(["Do, Re, Mi", "ABC"], last_changed)

    def test_multiple_properties(self):
        name_subject = BehaviorSubject("Slim Shady")
        age_subject = BehaviorSubject(26)

        class Fixture:
            name: RV[str] = ReactiveView(RequiresContext.from_value(name_subject))
            age: RV[int] = ReactiveView(RequiresContext.from_value(rx.empty()))

            def __init__(self):
                # noinspection PyTypeChecker
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
            value: RV[int] = ReactiveView(RequiresContext.from_value(rx.of(1)), read_only=False)

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
            value: RV[int] = rv.from_observable(rx.empty())

        prop = Fixture.value

        self.assertEqual(ReactiveView, type(prop))
        self.assertEqual("value", prop.name)

    def test_map(self):
        source = BehaviorSubject("wolf")

        class Fixture:
            name: RV[str] = ReactiveView(RequiresContext.from_value(source), read_only=False)

            song: RV[str] = name.map(lambda n: f"Who's afraid of a big bad {n}?")

        fixture = Fixture()

        self.assertEqual(False, Fixture.song.read_only)
        self.assertEqual("Who's afraid of a big bad wolf?", fixture.song)

        source.on_next("cat")

        self.assertEqual("Who's afraid of a big bad cat?", fixture.song)

    def test_pipe(self):
        source = BehaviorSubject("wolf")

        class Fixture:
            name: RV[str] = ReactiveView(RequiresContext.from_value(source), read_only=False)

            song: RV[str] = name.pipe(ops.map(lambda n: f"Who's afraid of a big bad {n}?"))

        fixture = Fixture()

        self.assertEqual(False, Fixture.song.read_only)
        self.assertEqual("Who's afraid of a big bad wolf?", fixture.song)

        source.on_next("cat")

        self.assertEqual("Who's afraid of a big bad cat?", fixture.song)

    def test_extend(self):
        counter = BehaviorSubject(1)

        class Fixture:
            value: RV[int] = ReactiveView(RequiresContext.from_value(counter))

            doubled: RV[int] = ReactiveView(value.context.map(lambda c: c.pipe(ops.map(lambda v: v * 2))))

            result: RV[int] = ReactiveView(RequiresContext
                                           .from_iterable([v.context for v in [value, doubled]])
                                           .map(lambda v: rx.combine_latest(*v))
                                           .map(lambda o: o.pipe(ops.map(lambda v: f"{v[0]} * 2 = {v[1]}"))))

        fixture = Fixture()

        self.assertEqual(1, fixture.value)
        self.assertEqual(2, fixture.doubled)
        self.assertEqual("1 * 2 = 2", fixture.result)

        counter.on_next(3)

        self.assertEqual(3, fixture.value)
        self.assertEqual(6, fixture.doubled)
        self.assertEqual("3 * 2 = 6", fixture.result)


if __name__ == '__main__':
    unittest.main()
