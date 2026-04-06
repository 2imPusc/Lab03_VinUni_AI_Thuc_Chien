"""
5 Test Cases for TravelWise Chatbot vs Agent evaluation.
Mix of simple and multi-step travel queries.
"""

TEST_CASES = [
    {
        "id": 1,
        "query": "Thủ đô của Việt Nam là gì?",
        "type": "simple",
        "expected_behavior": "Chatbot trả lời được từ kiến thức chung. Không cần tool.",
        "requires_tools": [],
    },
    {
        "id": 2,
        "query": "Thời tiết Đà Nẵng cuối tuần này thế nào?",
        "type": "single-tool",
        "expected_behavior": "Cần web_search để lấy dữ liệu thời tiết real-time. Chatbot sẽ từ chối hoặc đoán.",
        "requires_tools": ["web_search", "get_system_time"],
    },
    {
        "id": 3,
        "query": "Hà Nội đi Hải Phòng, lên lịch trình 2 ngày 1 đêm cho 2 người.",
        "type": "multi-step",
        "expected_behavior": "Cần get_system_time + web_search (thời tiết, vé tàu, khách sạn) + calculator (tổng chi phí). Chatbot sẽ đưa thông tin chung chung, không có số liệu thực.",
        "requires_tools": ["get_system_time", "web_search", "calculator"],
    },
    {
        "id": 4,
        "query": "Sài Gòn đi Đà Lạt, budget 3 triệu cho 2 người, 3 ngày 2 đêm.",
        "type": "multi-step",
        "expected_behavior": "Cần web_search (giá vé, khách sạn, ăn uống) + calculator (kiểm tra budget). Chatbot không thể verify budget có đủ hay không.",
        "requires_tools": ["web_search", "calculator"],
    },
    {
        "id": 5,
        "query": "So sánh chi phí đi Sapa vs Ninh Bình từ Hà Nội cho chuyến đi cuối tuần.",
        "type": "multi-tool",
        "expected_behavior": "Cần get_system_time + web_search gọi nhiều lần (giá 2 điểm đến) + calculator (so sánh). Chatbot chỉ đoán chung.",
        "requires_tools": ["get_system_time", "web_search", "calculator"],
    },
]
