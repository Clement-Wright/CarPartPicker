from __future__ import annotations

from fastapi import HTTPException

from app.schemas import CurrentSetup, EliminatedOption, GraphEdge, GraphNode, GraphResponse
from app.services.graph_codec import decode_graph_payload
from app.services.recommendation_engine import collect_package_evaluations, evaluate_package
from app.services.seed_repository import SeedRepository, get_repository


def build_graph(graph_id: str, repository: SeedRepository | None = None) -> GraphResponse:
    repository = repository or get_repository()
    payload = decode_graph_payload(graph_id)

    try:
        trim = repository.get_trim(payload["trim_id"])
        package = repository.get_package(payload["package_id"])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown graph entity.") from exc

    selected_goals = payload.get("selected_goals", ["daily"])
    budget_max = payload.get("budget_max")
    current_setup = CurrentSetup.model_validate(payload.get("current_setup", {}))

    evaluation = evaluate_package(
        trim=trim,
        package=package,
        selected_goals=selected_goals,
        budget_max=budget_max,
        current_setup=current_setup,
        repository=repository,
    )

    trim_node_id = f"trim:{trim.trim_id}"
    package_node_id = f"package:{package.package_id}"
    nodes = [
        GraphNode(
            id=trim_node_id,
            label=f"{trim.year} {trim.make} {trim.model} {trim.trim}",
            kind="trim",
            status="info",
            description=f"Stock wheel: {trim.stock_wheel_diameter}-inch. {trim.utility_note}",
            position={"x": 0, "y": 140},
        ),
        GraphNode(
            id=package_node_id,
            label=package.title,
            kind="package",
            status="positive" if evaluation.valid else "conflict",
            description=package.subtitle,
            position={"x": 260, "y": 140},
        ),
        GraphNode(
            id=f"safety:{trim.trim_id}",
            label="Safety Snapshot",
            kind="safety",
            status="info",
            description=f"Safety index {trim.safety_index:.0%}. Demo NHTSA seed snapshot loaded.",
            position={"x": 0, "y": 0},
        ),
        GraphNode(
            id=f"recall:{trim.trim_id}",
            label="Recall Burden",
            kind="recall",
            status="warning" if trim.recall_burden >= 0.3 else "positive",
            description=trim.recall_summary,
            position={"x": 0, "y": 280},
        ),
    ]
    edges = [
        GraphEdge(
            id="trim-package",
            source=trim_node_id,
            target=package_node_id,
            label="compatible with" if evaluation.valid else "blocked by",
            status="positive" if evaluation.valid else "conflict",
        ),
        GraphEdge(
            id="trim-safety",
            source=trim_node_id,
            target=f"safety:{trim.trim_id}",
            label="anchored by",
            status="info",
        ),
        GraphEdge(
            id="trim-recall",
            source=trim_node_id,
            target=f"recall:{trim.trim_id}",
            label="risk context",
            status="warning" if trim.recall_burden >= 0.3 else "positive",
        ),
    ]

    for index, goal in enumerate(selected_goals):
        goal_node_id = f"goal:{goal}"
        nodes.append(
            GraphNode(
                id=goal_node_id,
                label=goal.replace("_", " ").title(),
                kind="goal",
                status="positive",
                description=f"Selected goal weight for {goal.replace('_', ' ')}.",
                position={"x": 260, "y": -40 + (index * 76)},
            )
        )
        edges.append(
            GraphEdge(
                id=f"goal-edge:{goal}",
                source=goal_node_id,
                target=package_node_id,
                label="optimizes for",
                status="positive",
            )
        )

    for index, part in enumerate(evaluation.parts):
        part_node_id = f"part:{part.part_id}"
        nodes.append(
            GraphNode(
                id=part_node_id,
                label=part.name,
                kind=part.category,
                status="positive",
                description=part.notes,
                position={"x": 540, "y": (index * 92)},
            )
        )
        edges.append(
            GraphEdge(
                id=f"package-part:{part.part_id}",
                source=package_node_id,
                target=part_node_id,
                label="contains",
                status="positive",
            )
        )
        if part.requires_min_wheel_diameter:
            rule_id = f"rule:{part.part_id}:min-wheel"
            wheel_id = "setup:effective-wheel"
            nodes.extend(
                [
                    GraphNode(
                        id=rule_id,
                        label=f"Min Wheel {part.requires_min_wheel_diameter}\"",
                        kind="rule",
                        status="warning",
                        description=f"{part.name} needs at least {part.requires_min_wheel_diameter}-inch clearance.",
                        position={"x": 780, "y": (index * 92)},
                    ),
                    GraphNode(
                        id=wheel_id,
                        label=f"Effective Wheel {evaluation.effective_wheel_diameter}\"",
                        kind="setup",
                        status="positive"
                        if evaluation.effective_wheel_diameter >= part.requires_min_wheel_diameter
                        else "conflict",
                        description="Current setup or included wheel after package rules are applied.",
                        position={"x": 780, "y": 340},
                    ),
                ]
            )
            edges.extend(
                [
                    GraphEdge(
                        id=f"part-rule:{part.part_id}",
                        source=part_node_id,
                        target=rule_id,
                        label="requires",
                        status="warning",
                    ),
                    GraphEdge(
                        id=f"wheel-rule:{part.part_id}",
                        source=wheel_id,
                        target=rule_id,
                        label="satisfies"
                        if evaluation.effective_wheel_diameter >= part.requires_min_wheel_diameter
                        else "conflicts with",
                        status="positive"
                        if evaluation.effective_wheel_diameter >= part.requires_min_wheel_diameter
                        else "conflict",
                    ),
                ]
            )

    _, rejected = collect_package_evaluations(
        trim=trim,
        selected_goals=selected_goals,
        budget_max=budget_max,
        current_setup=current_setup,
        repository=repository,
    )

    eliminated = [
        EliminatedOption(
            package_id=item.package.package_id,
            title=item.package.title,
            reason=item.reasons[0],
        )
        for item in rejected[:3]
    ]

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        highlights=[package_node_id, trim_node_id],
        eliminated_options=eliminated,
    )

