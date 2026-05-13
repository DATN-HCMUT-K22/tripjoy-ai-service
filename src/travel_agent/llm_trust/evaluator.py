from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import get_settings
from ..graphs.itinerary_graph import generate_itinerary
from ..llm_trust.openrouter_client import OpenRouterClient, OpenRouterConfig
from ..models.models import TravelRequest, TrustScore


# CRITERIA: list[str] = [
#     "spatial_coherence", # khoảng cách & thứ tự địa điểm
#     "temporal_feasibility", # thời gian ghé thăm
#     "poi_relevance_travel_type", # phù hợp loại hình du lịch
#     "poi_relevance_budget" # phù hợp ngân sách
# ]


def travel_request_to_dict(req: TravelRequest) -> dict:
    budget_value = req.budget
    if isinstance(budget_value, str):
        try:
            budget_value = int("".join(ch for ch in budget_value if ch.isdigit()))
        except Exception:
            budget_value = 0

    return {
        "destination_name": req.destination_name,
        "location": {
            "latitude": req.coordinate.latitude,
            "longitude": req.coordinate.longitude,
        },
        "travel_type": req.travel_type,
        "budget": int(budget_value),
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "people_quantity": req.people_quantity,
        "suggest_locations": req.suggest_locations or [],
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate_output(
    *,
    output_text: str,
    travel_request: TravelRequest,
    log_path: str | Path | None = None,
) -> TrustScore:
    """Score an LLM output using an OpenRouter judge model and optionally append JSONL logs."""

    settings = get_settings()

    api_key = (
        getattr(settings, "openrouter_api_key", None)
        or getattr(settings, "openrouter_key", None)
        or None
    )
    if not api_key:
        raise ValueError(
            "Missing OpenRouter API key. Set OPENROUTER_API_KEY (recommended) in .env/environment."
        )

    judge_model = getattr(settings, "openrouter_model", None) or "openai/gpt-4o-mini"

    client = OpenRouterClient(OpenRouterConfig(api_key=api_key, model=judge_model))

    system = (
        "Bạn là một hệ thống đánh giá (judge) nghiêm ngặt và khách quan.\n"
        "Nhiệm vụ của bạn là chấm điểm lịch trình dựa CHỈ trên các tiêu chí được cung cấp.\n\n"
        "QUY TẮC CHẤM ĐIỂM:\n"
        "- Mỗi tiêu chí được chấm từ 0 đến 10.\n"
        "- 0 = hoàn toàn không đạt, 5 = trung bình, 10 = xuất sắc.\n"
        "- Chỉ sử dụng dữ liệu được cung cấp. KHÔNG suy đoán hoặc tự thêm thông tin.\n"
        "- Hãy khắt khe và trừ điểm các kế hoạch không thực tế.\n\n"
        "ĐỊNH DẠNG OUTPUT (BẮT BUỘC):\n"
        "- Chỉ trả về JSON hợp lệ.\n"
        "- Không markdown, không giải thích ngoài JSON.\n"
        "- Phải đúng schema sau:\n"
        '{"overall": float, "subscores": {string: float}, "reasons": {string: string}}\n'
        "- overall phải là trung bình của các subscores.\n"
    )

    travel_request_dict = travel_request_to_dict(travel_request)

    user = (
        f"Lịch trình cần chấm điểm:\n{output_text}\n"
        "CÁC TIÊU CHÍ (chấm độc lập từng tiêu chí):\n"
        "- spatial_coherence\n"
        "- temporal_feasibility\n"
        "- poi_relevance_travel_type\n"
        "- poi_relevance_budget\n\n"
        "ĐỊNH NGHĨA TIÊU CHÍ:\n\n"
        "1. spatial_coherence:\n"
        "- Các địa điểm có gần nhau về mặt địa lý không?\n"
        "- Lịch trình có tránh di chuyển xa hoặc zig-zag không hợp lý không?\n\n"
        "2. temporal_feasibility:\n"
        "- Thời lượng ở mỗi địa điểm có thực tế không?\n"
        "- Lịch trình có bị chồng chéo thời gian không?\n"
        "- Có tính đến thời gian di chuyển hợp lý không?\n\n"
        "3. poi_relevance_travel_type:\n"
        "- Địa điểm có phù hợp với travel_type của người dùng không?\n"
        "- Ví dụ: food → nhà hàng, chill → cafe/bãi biển, adventure → hoạt động trải nghiệm\n\n"
        "4. poi_relevance_budget:\n"
        "- Địa điểm có phù hợp với ngân sách không?\n"
        "- low → rẻ/miễn phí, high → cao cấp/trải nghiệm trả phí\n\n"
        f"Yêu cầu người dùng về lịch trình:\n{json.dumps(travel_request_dict, ensure_ascii=False)}\n\n"
        "HƯỚNG DẪN ĐÁNH GIÁ:\n"
        "- Chấm từng tiêu chí độc lập.\n"
        "- Mỗi tiêu chí phải có điểm và lý do ngắn gọn.\n"
        "- Lý do phải dựa trên dữ liệu cụ thể trong lịch trình.\n"
        "- Trừ điểm nếu thiếu thông tin, không thực tế hoặc mâu thuẫn.\n\n"
    )

    raw = client.run_llm(system=system, user=user, temperature=0.0)

    try:
        parsed: dict[str, Any] = json.loads(raw)
        overall = float(parsed.get("overall"))
        subscores = {
            str(k): float(v) for k, v in (parsed.get("subscores") or {}).items()
        }
        reasons = {str(k): str(v) for k, v in (parsed.get("reasons") or {}).items()}
    except Exception as e:
        overall, subscores, reasons = (
            0.0,
            {},
            {"parse_error": f"Failed to parse judge JSON: {e}; raw={raw!r}"},
        )

    score = TrustScore(overall=overall, subscores=subscores, reasons=reasons)

    if log_path is not None:
        run_id = str(uuid.uuid4())
        lp = Path(log_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "run_id": run_id,
            "llm_raw": raw,
            "model": judge_model,
            "timestamp": _utc_now_iso(),
            "input": travel_request_dict,
            "output": output_text,
            "score": {
                "overall": score.overall,
                "subscores": score.subscores,
                "reasons": score.reasons,
            },
        }
        lp.open("a", encoding="utf-8").write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )

    return score


def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def generate_and_evaluate_itinerary(
    *,
    travel_request: TravelRequest,
    log_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate itinerary using internal generator and evaluate it with OpenRouter judge."""

    itinerary = generate_itinerary(travel_request)
    if not itinerary:
        raise ValueError("generate_itinerary returned None")

    itinerary_text = json.dumps(
        asdict(itinerary), ensure_ascii=False, default=serialize
    )
    if not itinerary_text:
        raise ValueError("Generator returned empty itinerary")

    score = evaluate_output(
        output_text=itinerary_text,
        travel_request=travel_request,
        log_path=log_path,
    )

    return {"itinerary": itinerary, "itinerary_text": itinerary_text, "score": score}
