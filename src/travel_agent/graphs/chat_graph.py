"""
chat_graph.py - Chatbot để tương tác với người dùng về du lịch
"""

from ..llm.llm_vertex import VertexLLM


def chat(message: str) -> str:
    """
    Chatbot trả lời các câu hỏi về du lịch
    
    Args:
        message: Tin nhắn từ người dùng
    
    Returns:
        str: Phản hồi từ chatbot
    """
    llm = VertexLLM()
    
    prompt = f"""
Bạn là TripJoy AI - trợ lý du lịch trong ứng dụng chat nhóm.

NGUYÊN TẮC TRẢ LỜI:
- Trả lời ngắn gọn (tối đa 8–10 dòng).
- Ưu tiên bullet point.
- Không viết dạng bài blog dài.
- Không dùng tiêu đề lớn (###).
- Không dùng quá nhiều markdown.
- Giọng điệu thân thiện, tự nhiên như đang chat.
- Không lặp lại câu hỏi của người dùng.
- Không lan man.

Bởi vì đây là context trong 1 cuộc hội thoại nhắn tin nhóm nên bạn hãy trả lời tự nhiên và ngắn gọn nhé

Người dùng hỏi:
{message}

Trả lời:
"""
    
    try:
        response = llm.run(prompt)
        return response.strip()
    except Exception as e:
        print(f"✗ Error in chatbot: {e}")
        return f"Xin lỗi, có lỗi xảy ra: {str(e)}"
