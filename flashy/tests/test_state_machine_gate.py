"""Tests: state-machine transitions, quality gate, terminal state."""

import unittest

from flashy.quality_gate import QualityGate, GateError, GATE_ITEMS
from flashy.state_machine import (
    ExecutionStateMachine, TransitionError,
    LOCKED, PLANNING, EXECUTING, VERIFYING, DONE, BLOCKED,
)


class StateMachineTests(unittest.TestCase):
    def test_happy_path(self):
        m = ExecutionStateMachine("Ship the thing")
        self.assertEqual(m.state, LOCKED)
        m.transition(PLANNING)
        m.transition(EXECUTING)
        m.transition(VERIFYING)
        gate = QualityGate()
        gate.check_all()
        m.transition(DONE, quality_gate=gate)
        self.assertTrue(m.is_terminal)

    def test_needs_objective(self):
        with self.assertRaises(TransitionError):
            ExecutionStateMachine("   ")

    def test_cannot_skip_states(self):
        m = ExecutionStateMachine("Ship the thing")
        with self.assertRaises(TransitionError):
            m.transition(EXECUTING)  # LOCKED -> EXECUTING skips PLANNING

    def test_verifying_to_done_requires_gate(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        m.transition(EXECUTING)
        m.transition(VERIFYING)
        gate = QualityGate()
        gate.check(GATE_ITEMS[0])  # only one box
        with self.assertRaises(TransitionError):
            m.transition(DONE, quality_gate=gate)
        self.assertEqual(m.state, VERIFYING)  # still verifying, not done

    def test_verifying_to_done_without_gate_object(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        m.transition(EXECUTING)
        m.transition(VERIFYING)
        with self.assertRaises(TransitionError):
            m.transition(DONE)

    def test_no_silent_planning_reentry(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        m.transition(EXECUTING)
        with self.assertRaises(TransitionError):
            m.transition(PLANNING)  # no scope_change flag
        m.transition(PLANNING, scope_change=True)  # explicit: allowed
        self.assertEqual(m.state, PLANNING)

    def test_blocked_requires_checkpoint_before_resume(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        m.transition(EXECUTING)
        m.block("waiting on API key")
        self.assertEqual(m.state, BLOCKED)
        with self.assertRaises(TransitionError):
            m.transition(EXECUTING)  # no checkpoint emitted yet
        m.emit_checkpoint()
        m.transition(EXECUTING)
        self.assertEqual(m.state, EXECUTING)

    def test_block_requires_reason(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        m.transition(EXECUTING)
        with self.assertRaises(TransitionError):
            m.block("   ")
        m.block("waiting on API key")
        self.assertEqual(m.block_reason, "waiting on API key")

    def test_blocked_from_verifying(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        m.transition(EXECUTING)
        m.transition(VERIFYING)
        m.block("test environment down")
        self.assertEqual(m.state, BLOCKED)

    def test_done_is_terminal(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        m.transition(EXECUTING)
        m.transition(VERIFYING)
        gate = QualityGate()
        gate.check_all()
        m.transition(DONE, quality_gate=gate)
        with self.assertRaises(TransitionError):
            m.transition(EXECUTING)

    def test_unknown_state_rejected(self):
        m = ExecutionStateMachine("Ship the thing")
        with self.assertRaises(TransitionError):
            m.transition("NAPPING")

    def test_history_recorded(self):
        m = ExecutionStateMachine("Ship the thing")
        m.transition(PLANNING)
        self.assertEqual([s for s, _ in m.history], [LOCKED, PLANNING])


class QualityGateTests(unittest.TestCase):
    def test_seven_boxes(self):
        self.assertEqual(len(GATE_ITEMS), 7)

    def test_starts_unchecked(self):
        gate = QualityGate()
        self.assertFalse(gate.all_checked())
        self.assertEqual(gate.status(), "IN PROGRESS")
        self.assertEqual(len(gate.missing()), 7)

    def test_check_all(self):
        gate = QualityGate()
        gate.check_all()
        self.assertTrue(gate.all_checked())
        self.assertEqual(gate.status(), "DONE")
        self.assertEqual(gate.missing(), [])

    def test_unknown_item_rejected(self):
        gate = QualityGate()
        with self.assertRaises(GateError):
            gate.check("Looks fine to me")

    def test_uncheck_reopens(self):
        gate = QualityGate()
        gate.check_all()
        gate.uncheck(GATE_ITEMS[0])
        self.assertFalse(gate.all_checked())
        self.assertIn(GATE_ITEMS[0], gate.missing())


if __name__ == "__main__":
    unittest.main()
