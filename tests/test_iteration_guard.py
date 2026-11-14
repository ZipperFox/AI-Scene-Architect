"""Deterministic tests for bounded AI visual revision."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "ai-scene-architect"
          / "scripts" / "iteration_guard.py")
spec = importlib.util.spec_from_file_location("iteration_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def review(iteration, severity, digest_char, signature="edit"):
    return {
        "iteration": iteration,
        "visual_reviewed": True,
        "change_signature": signature,
        "renders": {"hero": digest_char * 64},
        "issues": ([{"id": "flat-lighting", "severity": severity,
                     "evidence": "Observed flat lighting in hero render", "fix": "Change key/fill ratio"}]
                   if severity else []),
    }


class TestGuard(unittest.TestCase):
    def test_baseline_allows_one_targeted_revision(self):
        self.assertEqual(guard.decide([review(0, 3, "a")])["decision"], "continue")

    def test_good_result_stops(self):
        history = [review(0, 3, "a"), review(1, 0, "b")]
        self.assertEqual(guard.decide(history)["reason"], "no_remaining_issues")

    def test_two_revisions_max(self):
        history = [review(0, 3, "a"), review(1, 2, "b"), review(2, 1, "c")]
        self.assertEqual(guard.decide(history)["reason"], "revision_budget_reached")

    def test_same_render_warns_but_count_controls(self):
        history = [review(0, 3, "a"), review(1, 3, "a")]
        self.assertEqual(guard.decide(history)["decision"], "continue")
        self.assertIn("identical_render_hashes", guard.decide(history)["warnings"])

    def test_same_ineffective_edit_warns(self):
        history = [review(0, 3, "a", "light-move"), review(1, 3, "b", "light-move")]
        self.assertEqual(guard.decide(history)["decision"], "continue")
        self.assertIn("repeated_ineffective_change", guard.decide(history)["warnings"])

    def test_two_non_improvements_warns_even_with_larger_budget(self):
        history = [review(0, 2, "a", "initial"), review(1, 2, "b", "light"),
                   review(2, 3, "c", "material")]
        self.assertEqual(guard.decide(history, max_revisions=5)["decision"], "continue")
        self.assertIn("two_revisions_without_progress",
                      guard.decide(history, max_revisions=5)["warnings"])

    def test_no_time_budget(self):
        history = [review(0, 2, "a")]
        history[0]["elapsed_seconds"] = 86400
        self.assertEqual(guard.decide(history)["decision"], "continue")

    def test_no_visual_inspection_is_invalid(self):
        item = review(0, 3, "a")
        item["visual_reviewed"] = False
        self.assertEqual(guard.decide([item])["reason"], "invalid_history")

    def test_nonconsecutive_review_invalid(self):
        self.assertEqual(guard.decide([review(1, 3, "a")])["reason"], "invalid_history")

    def test_constraint_violation_stops(self):
        item = review(0, 2, "a")
        item["constraints_violated"] = True
        self.assertEqual(guard.decide([item])["reason"], "approved_constraints_violated")


if __name__ == "__main__":
    unittest.main()
