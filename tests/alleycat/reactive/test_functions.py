import unittest
from typing import Optional

import rx
from rx import operators as ops
from rx.subject import BehaviorSubject

from alleycat.reactive import ReactiveObject, from_value, observe, from_property, from_view


# noinspection DuplicatedCode
class FunctionsTest(unittest.TestCase):
    def test_from_value(self):
        class Fixture(ReactiveObject):
            mary = from_value(100, read_only=True)

            poppins = from_value("Supercalifragilisticexpialidocious")

        fixture = Fixture()

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Supercalifragilisticexpialidocious", fixture.poppins)

        with self.assertRaises(AttributeError) as cm:
            fixture.mary = 10

        self.assertEqual(cm.exception.args[0], "Cannot modify a read-only property.")

        fixture.poppins = "Feed the Birds"

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Feed the Birds", fixture.poppins)

    def test_from_view(self):
        songs = BehaviorSubject("Supercalifragilisticexpialidocious")

        class Fixture(ReactiveObject):
            mary = from_view(rx.of(100), read_only=True)

            poppins = from_view()

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
            song = from_value("Supercalifragilisticexpialidocious")

            info = from_view()

            def __init__(self):
                # TODO: This is not really a good usage example. We should look into more practical
                #  use cases and establish best practices once we are done implementing the core features.
                self.info = observe(self.song).pipe(
                    ops.scan(lambda total, _: total + 1, 0),
                    ops.map(lambda count: f"Mary has sung {count} song(s)."),
                    ops.publish(),
                    ops.ref_count())

        poppins = MaryPoppins()

        songs = []
        info: Optional[str] = None

        def song_changed(value):
            songs.append(value)

        def info_changed(value):
            nonlocal info
            info = value

        song_subs = observe(poppins.song).subscribe(song_changed)
        info_subs = observe(poppins.info).subscribe(info_changed)

        poppins.song = "Feed the Birds"

        self.assertEqual(["Supercalifragilisticexpialidocious", "Feed the Birds"], songs)
        self.assertEqual("Mary has sung 2 song(s).", info)

        song_subs.dispose()
        info_subs.dispose()

        poppins.song = "A Spoonful of Sugar"

        self.assertEqual(["Supercalifragilisticexpialidocious", "Feed the Birds"], songs)
        self.assertEqual("Mary has sung 2 song(s).", info)

        # This time, subscribe using the name.
        observe(poppins, "song").subscribe(song_changed)
        observe(poppins, "info").subscribe(info_changed)

        poppins.song = "Chim Chim Cheree"

        self.assertEqual([
            "Supercalifragilisticexpialidocious",
            "Feed the Birds",
            "A Spoonful of Sugar",
            "Chim Chim Cheree"], songs)

        self.assertEqual("Mary has sung 4 song(s).", info)

    def test_from_property(self):
        class Wolf(ReactiveObject):
            name = from_value("wolf")

        class SuperWolf(Wolf):
            name = from_property(
                Wolf.name,
                lambda obj, v: f"a big bad {v}",
                lambda obj, v: v.pipe(ops.map(lambda n: f"Who's afraid of {n}?")))

        text: Optional[str] = None

        def value_changed(value):
            nonlocal text
            text = value

        with SuperWolf() as wolf:
            observe(wolf.name).subscribe(value_changed)

            self.assertEqual("Who's afraid of a big bad wolf?", text)

            wolf.name = "cat"

            self.assertEqual("Who's afraid of a big bad cat?", text)


if __name__ == '__main__':
    unittest.main()
