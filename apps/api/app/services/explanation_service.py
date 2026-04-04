from __future__ import annotations

from app.schemas import VehicleTrim


def recommendation_explanation(
    *,
    trim: VehicleTrim,
    package_title: str,
    matched_goals: list[str],
    why_it_matched: list[str],
    conflicts: list[str],
    required_changes: list[str],
) -> str:
    goal_text = ", ".join(matched_goals[:2]) if matched_goals else "your stated goals"
    strengths = "; ".join(why_it_matched[:2]) if why_it_matched else "it matched the package filters cleanly"
    sentence = (
        f"{package_title} lands well on the {trim.year} {trim.make} {trim.model} {trim.trim} "
        f"because it aligns with {goal_text} and {strengths.lower()}."
    )
    if required_changes:
        sentence += f" It does ask you to handle {required_changes[0].lower()}."
    if conflicts:
        sentence += f" The main tradeoff is {conflicts[0].lower()}."
    return sentence


def compare_explanation(
    primary_title: str,
    primary_axis: str,
    challenger_title: str,
    challenger_axis: str,
) -> str:
    return (
        f"{primary_title} wins when you care most about {primary_axis}, while "
        f"{challenger_title} makes more sense if {challenger_axis} matters more."
    )

