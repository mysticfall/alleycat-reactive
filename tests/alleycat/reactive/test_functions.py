import unittest
from typing import Optional

from rx import operators as ops

from alleycat.reactive import ReactiveObject, from_value, observe, from_property


class FunctionsTest(unittest.TestCase):
    def test_from_value(self):
        self.assertEqual(from_value(True, "Detective").name, "Detective")

        class Fixture(ReactiveObject):
            mary = from_value(100, read_only=True)

            poppins = from_value("Supercalifragilisticexpialidocious", "named_value")

        fixture = Fixture()

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Supercalifragilisticexpialidocious", fixture.poppins)

        with self.assertRaises(AttributeError) as cm:
            fixture.mary = 10

        self.assertEqual(cm.exception.args[0], "Cannot modify a read-only property.")

        fixture.poppins = "Feed the Birds"

        self.assertEqual(100, fixture.mary)
        self.assertEqual("Feed the Birds", fixture.poppins)

    def test_observe(self):
        class Fixture(ReactiveObject):
            mary = from_value(100, read_only=True)

            poppins = from_value("Supercalifragilisticexpialidocious", "named_value")

        fixture = Fixture()

        songs = []

        def value_changed(value):
            songs.append(value)

        cancel = observe(fixture.poppins).subscribe(value_changed)

        fixture.poppins = "Feed the Birds"

        self.assertEqual(["Supercalifragilisticexpialidocious", "Feed the Birds"], songs)

        cancel.dispose()

        fixture.poppins = "A Spoonful of Sugar"

        self.assertEqual(["Supercalifragilisticexpialidocious", "Feed the Birds"], songs)

        # This time, subscribe using the name.
        observe(fixture, "poppins").subscribe(value_changed)

        fixture.poppins = "Chim Chim Cheree"

        self.assertEqual([
            "Supercalifragilisticexpialidocious",
            "Feed the Birds",
            "A Spoonful of Sugar",
            "Chim Chim Cheree"], songs)

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
