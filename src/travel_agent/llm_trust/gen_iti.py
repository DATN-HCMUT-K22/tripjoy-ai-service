from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from travel_agent.graphs.itinerary_graph import generate_itinerary
from travel_agent.models.models import Coordinate, TravelRequest


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _load_requests(path: Path) -> list[TravelRequest]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("request.json must contain a JSON array")

    requests: list[TravelRequest] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"request[{idx}] must be an object")

        coord = item.get("coordinate") or {}
        requests.append(
            TravelRequest(
                destination_name=item["destination_name"],
                coordinate=Coordinate(
                    latitude=float(coord["latitude"]),
                    longitude=float(coord["longitude"]),
                ),
                travel_type=list(item.get("travel_type") or []),
                budget=int(item["budget"]),
                start_date=_parse_date(item["start_date"]),
                end_date=_parse_date(item["end_date"]),
                people_quantity=int(item["people_quantity"]),
                suggest_locations=item.get("suggest_locations") or [],
            )
        )

    return requests


def serialize(obj):
    from datetime import date, datetime

    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def main() -> None:
    # Load requests from adjacent request.json
    request_path = Path(__file__).with_name("request.json")
    travel_requests = _load_requests(request_path)
    filtered_requests = travel_requests[0:25]

    log_path = Path(r"C:\Users\Admin\OneDrive\Desktop\eval_log2.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    for i, req in enumerate(filtered_requests, start=1):
        print(f"\n[{i}/{len(filtered_requests)}] Generating itinerary for: {req.destination_name}")

        itinerary = generate_itinerary(req)
        if not itinerary:
            raise ValueError(
                f"generate_itinerary returned None for {req.destination_name}"
            )

        payload = asdict(itinerary)
        pretty = json.dumps(payload, ensure_ascii=False, indent=2, default=serialize)

        # Append with a blank line between records for readability
        with log_path.open("a", encoding="utf-8") as f:
            f.write(pretty)
            f.write("\n\n")

        print(pretty)

    print(f"\n✅ Logged {len(travel_requests)} itineraries to: {log_path}")


if __name__ == "__main__":
    main()
