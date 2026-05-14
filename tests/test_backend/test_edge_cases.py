import pytest
import requests

def test_chat_empty_query(api_urls, auth_headers):
    """Gửi query rỗng -> 400."""
    s_res = requests.post(f"{api_urls['golang']}/chat/session", headers=auth_headers)
    sid = s_res.json().get("id") or s_res.json().get("session_id")
    
    res = requests.post(
        f"{api_urls['golang']}/chat/session/{sid}/messages",
        headers=auth_headers,
        json={"query": ""}
    )
    assert res.status_code == 400

def test_chat_long_query(api_urls, auth_headers):
    """Gửi query cực dài (>2000 ký tự) -> 400."""
    s_res = requests.post(f"{api_urls['golang']}/chat/session", headers=auth_headers)
    sid = s_res.json().get("id") or s_res.json().get("session_id")
    
    long_query = "a" * 2001
    res = requests.post(
        f"{api_urls['golang']}/chat/session/{sid}/messages",
        headers=auth_headers,
        json={"query": long_query}
    )
    assert res.status_code == 400

def test_chat_invalid_session_history(api_urls, auth_headers):
    """Lấy lịch sử của session_id không tồn tại -> 200 với mảng rỗng."""
    res = requests.get(
        f"{api_urls['golang']}/chat/session/00000000-0000-0000-0000-000000000000/messages",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_cors_preflight(api_urls):
    """Kiểm tra OPTIONS request (CORS)."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization"
    }
    res = requests.options(f"{api_urls['golang']}/auth/login", headers=headers)
    # Một số backend trả 204 No Content cho OPTIONS, một số trả 200.
    assert res.status_code in [200, 204]
    # Header này có thể không có nếu CORS chưa được cấu hình đúng trên server
    assert "Access-Control-Allow-Origin" in res.headers

def test_content_type_validation(api_urls, auth_headers):
    """Gửi POST có body mà không có Content-Type: application/json -> 415 hoặc 400."""
    # 1. Tạo session
    s_res = requests.post(f"{api_urls['golang']}/chat/session", headers=auth_headers)
    sid = s_res.json().get("id") or s_res.json().get("session_id")
    
    # 2. Gửi message nhưng bỏ Content-Type
    headers = {k: v for k, v in auth_headers.items() if k.lower() != "content-type"}
    res = requests.post(
        f"{api_urls['golang']}/chat/session/{sid}/messages",
        headers=headers,
        data='{"query": "test"}'
    )
    # Kỳ vọng 415 (Unsupported Media Type) hoặc 400 (Bad Request)
    assert res.status_code in [415, 400]

def test_compare_single_keyword(api_urls):
    """Compare với chỉ 1 keyword -> verify vẫn trả về mảng có 1 phần tử."""
    res = requests.get(f"{api_urls['golang']}/compare/search", params={"keywords": "Java"})
    assert res.status_code == 200
    data = res.json().get("data", [])
    assert len(data) == 1
    assert data[0]["keyword"] == "Java"
