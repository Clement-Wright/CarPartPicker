from app.schemas import VehicleContext
from app.services.query_parser import parse_build_query


def test_parser_extracts_budget_goals_and_wheel() -> None:
    parsed = parse_build_query(
        "Best daily brake + wheel upgrade under $2,500 with 17-inch wheels",
        vehicle_context=VehicleContext(trim_id="gr86_2022_base"),
    )

    assert parsed.budget_max == 2500
    assert "daily" in parsed.goals
    assert "braking" in parsed.goals
    assert parsed.current_setup is not None
    assert parsed.current_setup.wheel_diameter == 17

