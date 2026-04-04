from __future__ import annotations

import re

from app.schemas import CurrentSetup, ParsedBuildQuery, VehicleContext


GOAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "daily": ("daily", "commute", "street"),
    "winter": ("winter", "snow", "cold", "ski"),
    "budget_grip": ("budget grip", "budget performance", "cheap grip", "grip build"),
    "street_performance": ("street performance", "track", "coilover", "performance"),
    "braking": ("brake", "bbk", "pad", "stopping"),
}

BUDGET_PATTERN = re.compile(
    r"(?:under|below|around|budget(?: of)?)\s*\$?\s*([0-9][0-9,]{2,})",
    re.IGNORECASE,
)
INLINE_BUDGET_PATTERN = re.compile(r"\$([0-9][0-9,]{2,})")
WHEEL_PATTERN = re.compile(r"\b(17|18)[ -]?(?:inch|in)\b", re.IGNORECASE)


def parse_build_query(
    text: str,
    vehicle_context: VehicleContext | None = None,
    current_setup: CurrentSetup | None = None,
) -> ParsedBuildQuery:
    normalized = text.lower()
    goals: list[str] = []
    extracted_terms: list[str] = []

    for goal, keywords in GOAL_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            goals.append(goal)
            extracted_terms.extend(keyword for keyword in keywords if keyword in normalized)

    if "wheel" in normalized and "daily" in normalized and "daily" not in goals:
        goals.append("daily")
    if "wheel" in normalized and "braking" not in goals and "brake" in normalized:
        goals.append("braking")
    if "budget" in normalized and "budget_grip" not in goals:
        goals.append("budget_grip")
    if not goals:
        goals.append("daily")

    budget_max = None
    budget_match = BUDGET_PATTERN.search(text) or INLINE_BUDGET_PATTERN.search(text)
    if budget_match:
        budget_max = int(budget_match.group(1).replace(",", ""))

    hard_constraints: list[str] = []
    if "keep current wheel" in normalized or "keep stock wheel" in normalized:
        hard_constraints.append("keep_current_wheels")
    if "stock ride height" in normalized:
        hard_constraints.append("keep_stock_ride_height")

    setup = current_setup.model_copy(deep=True) if current_setup else CurrentSetup()
    if "keep_current_wheels" in hard_constraints:
        setup.keep_current_wheels = True

    wheel_match = WHEEL_PATTERN.search(normalized)
    if wheel_match:
        setup.wheel_diameter = int(wheel_match.group(1))
        extracted_terms.append(f"{setup.wheel_diameter}-inch")
    elif vehicle_context and vehicle_context.trim_id:
        extracted_terms.append(vehicle_context.trim_id)

    confidence = min(
        0.98,
        0.42 + (0.09 * len(goals)) + (0.12 if budget_max else 0.0) + (0.06 if wheel_match else 0.0),
    )

    return ParsedBuildQuery(
        goals=goals,
        budget_max=budget_max,
        hard_constraints=hard_constraints,
        current_setup=setup,
        confidence=round(confidence, 2),
        extracted_terms=sorted(set(extracted_terms)),
    )

