from app.services.target_spec_service import parse_target_spec, solve_target_spec
from app.schemas import TargetSpecRequest


def test_target_spec_parser_extracts_metrics_and_constraints() -> None:
    parsed = parse_target_spec("I want 430 hp, manual, RWD, naturally aspirated, under $80,000 and 8000 rpm")

    assert parsed.target_metrics.hp_min == 430
    assert parsed.hard_constraints["transmission"] == ["manual"]
    assert parsed.hard_constraints["drivetrain"] == ["RWD"]
    assert parsed.hard_constraints["aspiration"] == ["na"]
    assert parsed.target_metrics.redline_min_rpm == 8000


def test_target_spec_solver_returns_candidates() -> None:
    response = solve_target_spec(
        TargetSpecRequest(text="Like a GT3 RS but more practical, 430 hp, manual, RWD, under $80,000")
    )

    assert response.candidates
    assert response.candidates[0].score > 0
