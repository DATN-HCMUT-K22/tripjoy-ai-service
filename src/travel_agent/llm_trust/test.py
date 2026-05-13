from datetime import datetime
from pathlib import Path

from ..models.models import TravelRequest, Coordinate
from ..llm_trust.evaluator import evaluate_output


def main():
    req = TravelRequest(
        destination_name="Đà Lạt",
        coordinate=Coordinate(latitude=11.94, longitude=108.4583),
        travel_type="food",
        budget=4000000,
        start_date=datetime(2026, 4, 30),
        end_date=datetime(2026, 5, 2),
        people_quantity=2,
    )

    log_path = Path(r"C:\Users\Admin\OneDrive\Desktop\eval_log.jsonl")

    # result = generate_and_evaluate_itinerary(
    #     travel_request=req,
    #     log_path=log_path
    # )

    # print("\n=== ITINERARY TEXT ===")
    # print(result["itinerary_text"])

    # print("\n=== SCORE ===")
    # print(result["score"])

    # print(f"\n✅ Log đã ghi vào: {log_path}")

    itinerary_text = """{
    "name": "Trip to Đà Lạt",
    "start_date": "2026-04-30",
    "end_date": "2026-05-02",
    "people_quantity": 2,
    "budget_estimate": "medium",
    "themes": [
        "Food"
    ],
    "destination": "Đà Lạt",
    "trip_items": [
        {
            "start_time": "2026-04-30T09:00:00",
            "duration": 60,
            "note": "Lâm Viên Square là một điểm đến trung tâm, rộng lớn và mang tính biểu tượng ở Đà Lạt, nổi bật với kiến trúc hiện đại của Bông Atisô và Bông Hoa Dã Quỳ khổng lồ. Đây là nơi lý tưởng để đi dạo, chụp ảnh, thưởng thức không khí trong lành bên Hồ Xuân Hương, hay đơn giản là ngắm nhìn cuộc sống nhộn nhịp với nhiều hoạt động giải trí và ăn uống, cả ngày lẫn đêm.",
            "location_name": "Lâm Viên Square",
            "place_id": "ChIJKQb-oyQTcTERiVn-etOO62Y"
        },
        {
            "start_time": "2026-04-30T10:05:00",
            "duration": 90,
            "note": "Vườn hoa thành phố Đà Lạt thực sự là một nơi đáng ghé thăm với rất nhiều loại hoa được chăm sóc tỉ mỉ, từ vườn hồng rực rỡ đến khu trưng bày bonsai ấn tượng và nhà kính lan độc đáo. Không chỉ đẹp mắt và yên bình để tản bộ, vườn còn có các khu vui chơi cho trẻ em và quán cà phê, rất phù hợp cho một buổi dạo chơi thư giãn bên hồ.",
            "location_name": "Dalat City Flower Garden",
            "place_id": "ChIJZ0qug8wTcTER0m4S0SZkp2I"
        },
        {
            "start_time": "2026-04-30T11:42:00",
            "duration": 90,
            "note": "Crazy House là một công trình kiến trúc độc đáo và siêu thực ở Đà Lạt, giống như bước vào một thế giới cổ tích với những cầu thang uốn lượn, hình khối hữu cơ lấy cảm hứng từ thiên nhiên. Đây không chỉ là một điểm tham quan thú vị để chụp ảnh và khám phá những góc bất ngờ mà còn là một trải nghiệm đáng giá nếu bạn muốn cảm nhận không gian kỳ ảo này vào ban đêm.",
            "location_name": "Crazy House - Hang Nga Villa",
            "place_id": "ChIJpTjuGjMTcTERhjx317psdj8"
        },
        {
            "start_time": "2026-04-30T13:16:00",
            "duration": 90,
            "note": "Dinh Bảo Đại III mang đến cái nhìn sâu sắc về cuộc sống của vị Hoàng đế cuối cùng của Việt Nam trong một không gian cổ kính nhưng rất được giữ gìn. Với kiến trúc pha trộn giữa nét sang trọng và giản dị, cùng những khu vườn tuyệt đẹp và quang cảnh hùng vĩ, đây là điểm đến lý tưởng để tìm hiểu lịch sử và thưởng thức vẻ đẹp kiến trúc tại Đà Lạt.",
            "location_name": "Bao Dai Palace 3",
            "place_id": "ChIJD6_GOjUTcTERT0qgP1esodo"
        },
        {
            "start_time": "2026-04-30T14:55:00",
            "duration": 60,
            "note": "Nhà thờ Domaine de Marie nổi bật với kiến trúc Pháp cổ độc đáo, màu hồng rực rỡ và không có tháp chuông, tọa lạc trên một ngọn đồi yên bình giữa rừng thông. Nơi đây không chỉ là một điểm đến tâm linh mà còn là một không gian tuyệt đẹp với những khu vườn hoa được chăm sóc kỹ lưỡng, rất lý tưởng để chụp ảnh và tận hưởng sự tĩnh lặng.",
            "location_name": "Domaine de Marie",
            "place_id": "ChIJ94S-Y9UScTER509fieB9s5I"
        },
        {
            "start_time": "2026-05-01T09:12:00",
            "duration": 120,
            "note": "Cáp treo Đà Lạt là một trải nghiệm không thể bỏ lỡ, mang đến tầm nhìn tuyệt đẹp toàn cảnh rừng thông và thành phố từ trên cao trong một hành trình êm ái. Điểm đến cuối cùng là Thiền viện Trúc Lâm với kiến trúc độc đáo và khu vườn thanh bình, rất đáng để khám phá thêm, đặc biệt nếu đi vào sáng sớm để tránh đông đúc.",
            "location_name": "Dalat Cable Car Tourist Area",
            "place_id": "ChIJE8cuCEcTcTERB0WLwyEghrw"
        },
        {
            "start_time": "2026-05-01T11:18:00",
            "duration": 150,
            "note": "Khu du lịch Thác Datanla là sự kết hợp hoàn hảo giữa vẻ đẹp thiên nhiên hùng vĩ của thác nước và những trải nghiệm mạo hiểm đầy phấn khích như máng trượt Alpine Coaster hay zipline. Đây là một điểm đến tuyệt vời cho những ai tìm kiếm cả sự thư giãn giữa thiên nhiên và những hoạt động sôi động, mặc dù đôi khi có thể đông đúc.",
            "location_name": "Khu du lịch Thác Datanla",
            "place_id": "ChIJQTO5pKEUcTERZcAVKbeOzvg"
        },
        {
            "start_time": "2026-05-02T09:20:00",
            "duration": 90,
            "note": "Puppy Farm là một điểm đến rất đáng yêu và đa dạng, nơi bạn có thể tương tác với nhiều loài động vật như chó, capybara, lạc đà alpaca, cùng với những khu vườn hoa và nhà kính đẹp mắt. Bên cạnh đó, các hoạt động giải trí như máng trượt cầu vồng siêu tốc và đi go-kart sẽ mang đến niềm vui cho mọi lứa tuổi, rất phù hợp cho chuyến đi chơi gia đình.",
            "location_name": "Puppy Farm",
            "place_id": "ChIJ0_q8BhJtcTERbdJWwhlkJPU"
        }
    ]
}
"""

    score = evaluate_output(
        output_text=itinerary_text, travel_request=req, log_path=log_path
    )
    print(score)


if __name__ == "__main__":
    main()
