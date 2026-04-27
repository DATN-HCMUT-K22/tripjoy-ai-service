tools = [
    {
        "name": "get_chat_message",
        "description": "Lấy lịch sử hội thoại để hiểu context trước đó",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_distance_between_places",
        "description": "Tính khoảng cách (mét) và thời gian (giây) giữa 2 địa điểm dựa trên Google Place ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin_place_id": {
                    "type": "string",
                    "description": "Google Place ID điểm xuất phát"
                },
                "destination_place_id": {
                    "type": "string",
                    "description": "Google Place ID điểm đến"
                },
                "travel_mode": {
                    "type": "string",
                    "description": "Phương tiện: DRIVE | WALK | BICYCLE | TRANSIT (default DRIVE)",
                    "default": "DRIVE"
                }
            },
            "required": ["origin_place_id", "destination_place_id"]
        }
    },
]