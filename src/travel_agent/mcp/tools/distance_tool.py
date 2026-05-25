def get_distance_between_places(
    origin_place_id: str,
    destination_place_id: str,
    travel_mode: str = "DRIVE",
):

    from travel_agent.tools.google_places import (
        get_distance_between_places as _get_distance,
    )

    return _get_distance(
        origin_place_id=origin_place_id,
        destination_place_id=destination_place_id,
        travel_mode=travel_mode,
    )