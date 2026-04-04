from app.services.graph_codec import encode_graph_payload
from app.services.graph_service import build_graph


def test_graph_returns_eliminated_options() -> None:
    graph_id = encode_graph_payload(
        {
            "trim_id": "gr86_2022_base",
            "package_id": "daily_brake_refresh",
            "selected_goals": ["daily", "braking"],
            "budget_max": 2600,
            "current_setup": {"wheel_diameter": 17, "keep_current_wheels": False, "notes": []},
        }
    )

    graph = build_graph(graph_id)

    assert graph.nodes
    assert graph.edges
    assert any(option.package_id == "bbk_core_18_only" for option in graph.eliminated_options)

