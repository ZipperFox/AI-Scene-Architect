"""Bound an AI's visual-revision loop using explicitly recorded review evidence."""

import argparse
import json
import sys
from pathlib import Path


class InvalidHistory(ValueError):
    pass


def severity_total(review):
    return sum(issue["severity"] for issue in review["issues"])


def issue_fingerprint(review):
    return tuple(sorted((issue["id"], issue["severity"]) for issue in review["issues"]))


def validate(history):
    if not isinstance(history, list) or not history:
        raise InvalidHistory("History must be a nonempty JSON array")
    for expected, review in enumerate(history):
        if not isinstance(review, dict) or review.get("iteration") != expected:
            raise InvalidHistory("Iterations must be consecutive, beginning at 0")
        if review.get("visual_reviewed") is not True:
            raise InvalidHistory("Every iteration must confirm actual image inspection")
        if not isinstance(review.get("elapsed_seconds"), (int, float)) or review["elapsed_seconds"] < 0:
            raise InvalidHistory("elapsed_seconds must be a nonnegative number")
        if expected and review["elapsed_seconds"] < history[expected - 1]["elapsed_seconds"]:
            raise InvalidHistory("elapsed_seconds must be cumulative and nondecreasing")
        if not isinstance(review.get("change_signature"), str) or not review["change_signature"].strip():
            raise InvalidHistory("Every iteration needs a nonempty change_signature")
        renders = review.get("renders")
        if not isinstance(renders, dict) or not renders:
            raise InvalidHistory("Every review requires rendered-image hash evidence")
        if any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64 or any(c not in "0123456789abcdef" for c in v.lower()) for k, v in renders.items()):
            raise InvalidHistory("renders must map camera names to SHA-256 hex digests")
        issues = review.get("issues")
        if not isinstance(issues, list):
            raise InvalidHistory("issues must be a list")
        seen = set()
        for issue in issues:
            if not isinstance(issue, dict) or not isinstance(issue.get("id"), str) or not issue["id"].strip():
                raise InvalidHistory("Every issue needs a stable id")
            if type(issue.get("severity")) is not int or issue["severity"] not in (1, 2, 3):
                raise InvalidHistory("Every issue severity must be 1, 2, or 3")
            if not isinstance(issue.get("evidence"), str) or not issue["evidence"].strip():
                raise InvalidHistory("Every issue needs image-based evidence")
            if issue["id"] in seen:
                raise InvalidHistory("Duplicate issue id within the same review")
            seen.add(issue["id"])


def decide(history, max_revisions=2, max_seconds=600):
    try:
        validate(history)
    except InvalidHistory as exc:
        return {"decision": "stop", "reason": "invalid_history", "detail": str(exc)}

    current = history[-1]
    revision = current["iteration"]
    unresolved = len(current["issues"])
    output = {"iteration": revision, "remaining_issues": unresolved,
              "severity_total": severity_total(current)}

    def stop(reason):
        return {**output, "decision": "stop", "reason": reason}

    if current.get("constraints_violated") is True:
        return stop("approved_constraints_violated")
    if unresolved == 0:
        return stop("no_remaining_issues")
    if revision >= max_revisions:
        return stop("revision_budget_reached")
    if current["elapsed_seconds"] >= max_seconds:
        return stop("elapsed_time_budget_reached")

    if len(history) >= 2:
        previous = history[-2]
        if current["renders"] == previous["renders"]:
            return stop("identical_render_hashes")
        if (current["change_signature"] == previous["change_signature"]
                and issue_fingerprint(current) == issue_fingerprint(previous)):
            return stop("repeated_ineffective_change")

    if len(history) >= 3:
        a, b, c = history[-3:]
        if severity_total(c) >= severity_total(b) >= severity_total(a):
            return stop("two_revisions_without_progress")

    return {**output, "decision": "continue", "reason": "targeted_revision_allowed",
            "revisions_remaining": max_revisions - revision}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--max-revisions", type=int, default=2)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args()
    if not 0 <= args.max_revisions <= 5 or not 1 <= args.max_seconds <= 3600:
        parser.error("revision limit must be 0–5 and elapsed seconds 1–3600")
    try:
        history = json.loads(args.history.read_text(encoding="utf-8"))
        result = decide(history, args.max_revisions, args.max_seconds)
    except (OSError, json.JSONDecodeError) as exc:
        result = {"decision": "stop", "reason": "unreadable_history", "detail": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # A stop is normal, not an error: agents must inspect the JSON decision.
    return 0


if __name__ == "__main__":
    sys.exit(main())
