import unittest
from typing import Optional

import rx
from rx import operators as ops
from rx.subject import BehaviorSubject

from alleycat.reactive import ReactiveObject, functions as rv


# noinspection DuplicatedCode
class FunctionsTest(unittest.TestCase):
    def test_from_value(self):
        class Fixture(ReactiveObject):
            mary = rv.from_value(100, read_only=True)

            poppins = rv.from_value("Supercalifragilisticexpialidocious")

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
            mary = rv.from_observable(rx.of(100), read_only=True)

            poppins = rv.new_view()

            def __init__(self):
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
            song = rv.from_value("Supercalifragilisticexpialidocious")

            info = rv.new_view()

            def __init__(self):
                # TODO: This is not really a good usage example. We should look into more practical
                #  use cases and establish best practices once we are done implementing the core features.
                self.info = rv.observe(self.song).pipe(
                    ops.scan(lambda total, _: total + 1, 0),
                    ops.map(lambda count: f"Mary has sung {count} song(s)."),
                    ops.publish(),
                    ops.ref_count())

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

    def test_map_combinators(self):
        class Fixture:
            value = rv.from_value(1)

            doubled = value.as_view().map(lambda v: v * 2)

            numbers = rv.combine(value, doubled)(lambda o: rx.combine_latest(*o))

            combined = rv.combine_latest(value, doubled)(ops.map(lambda v: f"value = {v[0]}, doubled = {v[1]}"))

            zipped = rv.zip(value, doubled)(ops.map(lambda v: f"{v[0]} * 2 = {v[1]}"))

        combined = []
        zipped = []

        fixture = Fixture()

        rv.observe(fixture.zipped).subscribe(zipped.append)
        rv.observe(fixture.combined).subscribe(combined.append)

        self.assertEqual(1, fixture.value)
        self.assertEqual(2, fixture.doubled)
        self.assertEqual((1, 2), fixture.numbers)
        self.assertEqual("value = 1, doubled = 2", fixture.combined)
        self.assertEqual("1 * 2 = 2", fixture.zipped)
        self.assertEqual(["value = 1, doubled = 2"], combined)
        self.assertEqual(["1 * 2 = 2"], zipped)

        fixture.value = 3

        self.assertEqual(3, fixture.value)
        self.assertEqual(6, fixture.doubled)
        self.assertEqual((3, 6), fixture.numbers)
        self.assertEqual("value = 3, doubled = 6", fixture.combined)
        self.assertEqual("3 * 2 = 6", fixture.zipped)
        self.assertEqual(["value = 1, doubled = 2", "value = 3, doubled = 2", "value = 3, doubled = 6"], combined)
        self.assertEqual(["1 * 2 = 2", "3 * 2 = 6"], zipped)


if __name__ == '__main__':
    unittest.main()
