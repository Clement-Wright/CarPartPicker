from __future__ import annotations

from fastapi import HTTPException

from app.schemas import BuildDiffResponse, SlotDiff
from app.services.build_helpers import stock_config_ids, stock_part_ids
from app.services.build_state_service import get_build


def build_diff(build_id: str, against: str) -> BuildDiffResponse:
    build = get_build(build_id)
    current = {
        item.subsystem: {
            "part": item.selected_part_id,
            "config": item.selected_config_id,
        }
        for item in build.selections
    }

    if against == "stock":
        baseline_parts = stock_part_ids(build)
        baseline_configs = stock_config_ids(build)
    else:
        other = get_build(against)
        if other.vehicle.trim_id != build.vehicle.trim_id:
            raise HTTPException(status_code=422, detail="Diff baseline must use the same trim for this MVP.")
        baseline_parts = {item.subsystem: item.selected_part_id for item in other.selections}
        baseline_configs = {item.subsystem: item.selected_config_id for item in other.selections}

    slots = [
        SlotDiff(
            subsystem=subsystem,
            stock_part_id=stock_part_ids(build).get(subsystem),
            stock_config_id=stock_config_ids(build).get(subsystem),
            baseline_part_id=baseline_parts.get(subsystem),
            baseline_config_id=baseline_configs.get(subsystem),
            current_part_id=current[subsystem]["part"],
            current_config_id=current[subsystem]["config"],
            changed=current[subsystem]["part"] != baseline_parts.get(subsystem)
            or current[subsystem]["config"] != baseline_configs.get(subsystem),
        )
        for subsystem in current
    ]
    return BuildDiffResponse(build_id=build_id, against=against, slots=slots)
