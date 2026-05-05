from pathlib import Path
import json

def prompt_template(input_data: dict, output_data: dict) -> str:
    return f"""
Bạn là một hệ thống đánh giá (judge) nghiêm ngặt và khách quan.
Nhiệm vụ của bạn là chấm điểm lịch trình dựa CHỈ trên các tiêu chí được cung cấp.

QUY TẮC CHẤM ĐIỂM:
- Mỗi tiêu chí được chấm từ 0 đến 10.
- 0 = hoàn toàn không đạt, 5 = trung bình, 10 = xuất sắc.
- Chỉ sử dụng dữ liệu được cung cấp. KHÔNG suy đoán hoặc tự thêm thông tin.

ĐỊNH DẠNG OUTPUT (BẮT BUỘC):
- Chỉ trả về JSON hợp lệ.
- Không markdown, không giải thích ngoài JSON.
- Schema:
{{
  "overall": float,
  "subscores": {{
    "spatial_coherence": float,
    "temporal_feasibility": float,
    "poi_relevance_travel_type": float,
    "poi_relevance_budget": float
  }},
  "reasons": {{
    "spatial_coherence": string,
    "temporal_feasibility": string,
    "poi_relevance_travel_type": string,
    "poi_relevance_budget": string
  }}
}}
- overall = trung bình cộng của các subscores.

YÊU CẦU NGƯỜI DÙNG:
{json.dumps(input_data, ensure_ascii=False, indent=2)}

LỊCH TRÌNH CẦN CHẤM:
{json.dumps(output_data, ensure_ascii=False, indent=2)}

TIÊU CHÍ ĐÁNH GIÁ:
1. spatial_coherence: 
- Các địa điểm có gần nhau không? 
- Có di chuyển zig-zag không hợp lý không? 
2. temporal_feasibility: 
- Thời lượng có hợp lý không? 
- Có chồng chéo thời gian không? 
- Có tính thời gian di chuyển không? 
3. poi_relevance_travel_type: 
- Có phù hợp travel_type không? 
4. poi_relevance_budget: 
- Có phù hợp ngân sách không?

HƯỚNG DẪN:
- Chấm từng tiêu chí độc lập.
- Mỗi tiêu chí PHẢI có điểm và lý do.
- Lý do phải dựa trên dữ liệu cụ thể trong lịch trình.
- Trừ điểm nếu: vi phạm các tiêu chí
"""

def main():
    request_path = Path(__file__).with_name("request.json")
    travel_requests = json.loads(request_path.read_text(encoding="utf-8"))

    response_path = Path(__file__).with_name("response.json")
    travel_responses = json.loads(response_path.read_text(encoding="utf-8"))

    log_path = Path(r"C:\Users\Admin\OneDrive\Desktop\logs.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)


    with log_path.open("w", encoding="utf-8") as f:
        for i in range (0,50):

            input_data = travel_requests[i]
            output_data = travel_responses[i]
            prompt = prompt_template(input_data, output_data)

            f.write(f"===== PROMPT {i} =====\n")
            f.write(prompt)
            f.write("\n\n\n")

if __name__ == "__main__":
    main()