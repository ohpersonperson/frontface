"""Tests for the register set and cycle planning."""

import unittest

from meminqu.registers import (
    REGISTERS,
    Register,
    RegisterError,
    get_register,
    plan_cycle,
    validate_register_set,
)

EXPECTED_NAMES = (
    "direct",
    "reflective",
    "structural",
    "irreverent",
    "sparse",
    "temporal",
    "contrastive",
)


class TestRegisterSet(unittest.TestCase):
    def test_all_seven_registers_present(self):
        self.assertEqual(tuple(r.name for r in REGISTERS), EXPECTED_NAMES)

    def test_every_register_has_description_and_stems(self):
        for r in REGISTERS:
            self.assertTrue(r.label.strip(), r.name)
            self.assertTrue(r.description.strip(), r.name)
            self.assertGreaterEqual(len(r.example_stems), 2, r.name)
            for stem in r.example_stems:
                self.assertTrue(stem.strip(), r.name)

    def test_get_register_case_insensitive(self):
        self.assertEqual(get_register("Direct").name, "direct")
        self.assertEqual(get_register("CONTRASTIVE").name, "contrastive")

    def test_get_register_unknown_raises(self):
        with self.assertRaises(RegisterError):
            get_register("astrological")


class TestValidateRegisterSet(unittest.TestCase):
    def test_custom_set_accepted(self):
        custom = (
            Register("a", "A", "desc", ("stem one", "stem two")),
            Register("b", "B", "desc", ("stem one", "stem two")),
        )
        self.assertEqual(validate_register_set(custom), custom)

    def test_single_register_rejected(self):
        with self.assertRaises(RegisterError):
            validate_register_set((REGISTERS[0],))

    def test_duplicate_names_rejected(self):
        with self.assertRaises(RegisterError):
            validate_register_set((REGISTERS[0], REGISTERS[0]))

    def test_register_without_stems_rejected(self):
        bad = Register("x", "X", "desc", ())
        with self.assertRaises(RegisterError):
            validate_register_set((bad, REGISTERS[1]))


class TestPlanCycle(unittest.TestCase):
    DOMAINS = ("personal", "work", "projects", "reference", "misc")

    def test_per_domain_count(self):
        plan = plan_cycle(self.DOMAINS, per_domain=3)
        for domain, regs in plan.items():
            self.assertEqual(len(regs), 3, domain)

    def test_registers_distinct_within_domain(self):
        plan = plan_cycle(self.DOMAINS, per_domain=4)
        for domain, regs in plan.items():
            self.assertEqual(len(set(regs)), len(regs), domain)

    def test_consecutive_domains_differ(self):
        plan = plan_cycle(self.DOMAINS, per_domain=3)
        ordered = [plan[d] for d in self.DOMAINS]
        for first, second in zip(ordered, ordered[1:]):
            self.assertNotEqual(first, second)

    def test_full_cycle_covers_all_registers(self):
        plan = plan_cycle(self.DOMAINS, per_domain=3)
        used = {r for regs in plan.values() for r in regs}
        self.assertEqual(used, set(EXPECTED_NAMES))

    def test_deterministic(self):
        self.assertEqual(
            plan_cycle(self.DOMAINS), plan_cycle(self.DOMAINS)
        )

    def test_per_domain_exceeding_register_count_rejected(self):
        with self.assertRaises(RegisterError):
            plan_cycle(self.DOMAINS, per_domain=99)

    def test_empty_domains_rejected(self):
        with self.assertRaises(RegisterError):
            plan_cycle(())


if __name__ == "__main__":
    unittest.main()
