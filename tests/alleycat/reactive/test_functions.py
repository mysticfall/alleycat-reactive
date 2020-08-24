import unittest
from typing import Optional

import rx
from returns.functions import identity
from rx import operators as ops
from rx.subject import BehaviorSubject

from alleycat.reactive import ReactiveObject, functions as rv, RP, RV


# noinspection DuplicatedCode
class FunctionsTest(unittest.TestCase):
    def test_from_value(self):
        class Fixture(ReactiveObject):
            mary: RP[int] = rv.from_value(100, read_only=True)

            poppins: RP[str] = rv.from_value("Supercalifragilisticexpialidocious")

        fixture = Fixture()

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Supercalifragilisticexpialidocious", fixture.poppins)

        with self.assertRaises(AttributeError) as cm:
            fixture.mary = 10

        self.assertEqual(cm.exception.args[0], "Cannot modify a read-only property.")

        fixture.poppins = "Feed the Birds"

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Feed the Birds", fixture.poppins)

    def test_from_observable(self):
        songs = BehaviorSubject("Supercalifragilisticexpialidocious")

        class Fixture(ReactiveObject):
            mary: RV[int] = rv.from_observable(rx.of(100), read_only=True)

            poppins: RV[str] = rv.new_view()

            def __init__(self):
                # noinspection PyTypeChecker
                self.poppins = songs

        fixture = Fixture()

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Supercalifragilisticexpialidocious", fixture.poppins)

        with self.assertRaises(AttributeError) as cm:
            fixture.mary = 10

        self.assertEqual(cm.exception.args[0], "Cannot modify a read-only property.")

        songs.on_next("Feed the Birds")

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Feed the Birds", fixture.poppins)

    def test_observe(self):
        class MaryPoppins(ReactiveObject):
            song: RP[str] = rv.from_value("Supercalifragilisticexpialidocious")

            info = song.as_view().pipe(
                ops.scan(lambda total, _: total + 1, 0),
                ops.map(lambda count: f"Mary has sung {count} song(s)."))

        poppins = MaryPoppins()

        songs = []
        info: Optional[str] = None

        def info_changed(value):
            nonlocal info
            info = value

        song_subs = rv.observe(poppins.song).subscribe(songs.append)
        info_subs = rv.observe(poppins.info).subscribe(info_changed)

        poppins.song = "Feed the Birds"

        self.assertEqual(["Supercalifragilisticexpialidocious", "Feed the Birds"], songs)
        self.assertEqual("Mary has sung 2 song(s).", info)

        song_subs.dispose()
        info_subs.dispose()

        poppins.song = "A Spoonful of Sugar"

        self.assertEqual(["Supercalifragilisticexpialidocious", "Feed the Birds"], songs)
        self.assertEqual("Mary has sung 2 song(s).", info)

        # This time, subscribe using the name.
        rv.observe(poppins, "song").subscribe(songs.append)
        rv.observe(poppins, "info").subscribe(info_changed)

        poppins.song = "Chim Chim Cheree"

        self.assertEqual([
            "Supercalifragilisticexpialidocious",
            "Feed the Birds",
            "A Spoonful of Sugar",
            "Chim Chim Cheree"], songs)

        self.assertEqual("Mary has sung 4 song(s).", info)

    def test_observe_uninitialized(self):
        class Fixture:
            value: RP[int] = rv.new_property()

        values = []

        fixture = Fixture()

        rv.observe(fixture.value).subscribe(values.append)

        fixture.value = 1
        fixture.value = 2

        self.assertEqual([1, 2], values)

    def test_combine(self):
        class Fixture:
            value: RP[int] = rv.from_value(1)

            doubled: RV[int] = value.as_view().map(lambda v: v * 2)

            combined: RV[int] = rv.combine(value, doubled)(rx.combine_latest)

        combined = []

        fixture = Fixture()

        rv.observe(fixture.combined).subscribe(combined.append)

        self.assertEqual([(1, 2)], combined)

        fixture.value = 3

        self.assertEqual([(1, 2), (1, 6), (3, 6)], combined)

    def test_combine_latest(self):
        class Fixture:
            value: RP[int] = rv.from_value(1)

            doubled: RV[int] = value.as_view().map(lambda v: v * 2)

            combined: RV[int] = rv.combine_latest(value, doubled)(identity)

        combined = []

        fixture = Fixture()

        rv.observe(fixture.combined).subscribe(combined.append)

        self.assertEqual([(1, 2)], combined)

        fixture.value = 3

        self.assertEqual([(1, 2), (1, 6), (3, 6)], combined)

    def test_merge(self):
        class Fixture:
            cats: RP[str] = rv.new_property()

            dogs: RP[str] = rv.new_property()

            pets: RP[str] = rv.merge(cats, dogs)

        pets = []

        fixture = Fixture()

        rv.observe(fixture, "pets").subscribe(pets.append)

        fixture.cats = "Garfield"
        fixture.cats = "Grumpy"
        fixture.cats = "Cat who argues with a woman over a salad bowl"  # What was his name?

        fixture.dogs = "Pompidou"  # Sorry, I'm a cat person so I don't know too many canine celebrities.

        self.assertEqual(["Garfield", "Grumpy", "Cat who argues with a woman over a salad bowl", "Pompidou"], pets)

    def test_zip(self):
        class Fixture:
            value: RP[int] = rv.from_value(1)

            doubled: RV[int] = value.as_view().map(lambda v: v * 2)

            zipped: RV[int] = rv.zip(value, doubled)(ops.map(lambda v: f"{v[0]} * 2 = {v[1]}"))

        zipped = []

        fixture = Fixture()

        rv.observe(fixture.zipped).subscribe(zipped.append)

        self.assertEqual("1 * 2 = 2", fixture.zipped)
        self.assertEqual(["1 * 2 = 2"], zipped)

        fixture.value = 3

        self.assertEqual("3 * 2 = 6", fixture.zipped)
        self.assertEqual(["1 * 2 = 2", "3 * 2 = 6"], zipped)


if __name__ == '__main__':
    unittest.main()
