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
                super().__init__()

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

            info = song.as_view().pipe(lambda _: (
                ops.scan(lambda total, _: total + 1, 0),
                ops.map(lambda count: f"Mary has sung {count} song(s).")))

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

        self.assertEqual([], songs[2:])
        self.assertEqual("Mary has sung 2 song(s).", info)

        # This time, subscribe using the name.
        rv.observe(poppins, "song").subscribe(songs.append)
        rv.observe(poppins, "info").subscribe(info_changed)

        poppins.song = "Chim Chim Cheree"

        self.assertEqual(["A Spoonful of Sugar", "Chim Chim Cheree"], songs[2:])

        self.assertEqual("Mary has sung 4 song(s).", info)

    def test_observe_uninitialized(self):
        class Fixture:
            value: RP[int] = rv.new_property()

            view: RP[int] = value.as_view()

        values1 = []
        values2 = []

        fixture = Fixture()

        rv.observe(fixture.value).subscribe(values1.append)
        rv.observe(fixture.view).subscribe(values2.append)

        fixture.value = 1
        fixture.value = 2

        self.assertEqual([1, 2], values1)
        self.assertEqual([1, 2], values2)

    def test_combine(self):
        class Fixture:
            value: RP[int] = rv.from_value(1)

            doubled: RV[int] = value.as_view().map(lambda _, v: v * 2)

            combined: RV[int] = rv.combine(value, doubled)(rx.combine_latest)

        combined = []

        fixture = Fixture()

        rv.observe(fixture.combined).subscribe(combined.append)

        self.assertEqual([(1, 2)], combined)

        fixture.value = 3

        self.assertEqual([(1, 6), (3, 6)], combined[1:])

    def test_combine_latest(self):
        class Fixture:
            value: RP[int] = rv.from_value(1)

            doubled: RV[int] = value.as_view().map(lambda _, v: v * 2)

            combined: RV[int] = rv.combine_latest(value, doubled)(identity)

        combined = []

        fixture = Fixture()

        rv.observe(fixture.combined).subscribe(combined.append)

        self.assertEqual([(1, 2)], combined)

        fixture.value = 3

        self.assertEqual([(1, 6), (3, 6)], combined[1:])

    def test_merge(self):
        class Fixture:
            cats: RP[str] = rv.new_property()

            dogs: RP[str] = rv.new_property()

            pets: RP[str] = rv.merge(cats, dogs)

        pets = []

        fixture = Fixture()

        rv.observe(fixture, "pets").subscribe(pets.append)

        fixture.cats = "Garfield"
        self.assertEqual(["Garfield"], pets)

        fixture.cats = "Grumpy"
        self.assertEqual(["Grumpy"], pets[1:])

        fixture.cats = "Cat who argues with a woman over a salad bowl"  # What was his name?
        self.assertEqual(["Cat who argues with a woman over a salad bowl"], pets[2:])

        fixture.dogs = "Pompidou"  # Sorry, I'm a cat person so I don't know too many canine celebrities.
        self.assertEqual(["Pompidou"], pets[3:])

    def test_zip(self):
        class Fixture:
            value: RP[int] = rv.from_value(1)

            doubled: RV[int] = value.as_view().map(lambda _, v: v * 2)

            zipped: RV[int] = rv.zip(value, doubled)(ops.map(lambda v: f"{v[0]} * 2 = {v[1]}"))

        zipped = []

        fixture = Fixture()

        rv.observe(fixture.zipped).subscribe(zipped.append)

        self.assertEqual("1 * 2 = 2", fixture.zipped)
        self.assertEqual(["1 * 2 = 2"], zipped)

        fixture.value = 3

        self.assertEqual("3 * 2 = 6", fixture.zipped)
        self.assertEqual(["3 * 2 = 6"], zipped[1:])


if __name__ == '__main__':
    unittest.main()
