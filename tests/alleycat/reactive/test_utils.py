import unittest

from returns.maybe import Maybe

from alleycat.reactive import utils


class UtilsTest(unittest.TestCase):
    def test_get_current_frame(self):
        # noinspection PyUnusedLocal
        def inner(depth: int):
            chloe = "price"
            return utils.get_current_frame(depth)

        # noinspection PyUnusedLocal
        def outer(depth: int):
            maxine = "caulfield"
            return inner(depth)

        frame = outer(1).value_or(None)

        self.assertIsNotNone(frame)
        self.assertDictEqual({"chloe": "price", "depth": 1}, frame.f_locals)

        frame = outer(2).value_or(None)

        self.assertIsNotNone(frame)
        self.assertDictEqual({"maxine": "caulfield", "depth": 2, "inner": inner}, frame.f_locals)

    def test_get_assigned_name(self):
        def fun():
            frame = utils.get_current_frame(2)
            return frame.bind(utils.get_assigned_name).unwrap()

        class Blackwell:
            value = 1

            kate_marsh = fun()

            value2 = "1"

        self.assertEqual("kate_marsh", Blackwell().kate_marsh)

    def test_get_property_reference(self):
        def fun(_):
            frame = utils.get_current_frame(2)
            return frame.bind(utils.get_property_reference).unwrap()

        class Life:
            is_strange = Maybe.from_value(True)

        # I didn't put this line for philosophy, but to see if it would confuse the bytecode processing.
        # noinspection PyUnusedLocal
        life = "Lemon"

        # noinspection PyUnusedLocal
        life = Life()

        (obj, prop) = fun(life.is_strange)

        self.assertEqual(life, obj)
        self.assertEqual("is_strange", prop)

    def test_infer_or_require_name(self):
        def is_not_fun():
            return at_all()

        def at_all():
            return utils.infer_or_require_name(utils.get_assigned_name, 3)()

        def is_step_douche(_):
            return utils.infer_or_require_name(utils.get_property_reference, 2)()

        class David:
            madsen = is_not_fun()

        self.assertEqual("madsen", David.madsen)

        (obj, prop) = is_step_douche(David.madsen)

        self.assertEqual(David, obj)
        self.assertEqual("madsen", prop)

        with self.assertRaises(ValueError) as cm:
            utils.infer_or_require_name(utils.get_assigned_name)()

        self.assertEqual(
            "Argument 'name' is required when the platform does not provide bytecode instructions.",
            cm.exception.args[0])

    def test_get_instructions(self):
        def outer(depth: int):
            value = inner(depth)
            return value

        def inner(depth: int):
            return utils.get_current_frame(depth).map(utils.get_instructions).unwrap()

        self.assertEqual("RETURN_VALUE", next(outer(1)).opname)
        self.assertEqual("RETURN_VALUE", next(outer(2)).opname)
        self.assertEqual("CALL_FUNCTION", next(outer(3)).opname)


if __name__ == '__main__':
    unittest.main()
