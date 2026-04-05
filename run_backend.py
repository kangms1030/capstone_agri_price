"""백엔드 서버 실행 스크립트"""
import os
import socket
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# .env 로드 (HOST/PORT 등)
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
load_dotenv(_env_path)


def _parse_port() -> int:
    raw = os.getenv("PORT", "8000").strip()
    try:
        return int(raw)
    except ValueError:
        return 8000


def _parse_host() -> str:
    return os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"


def _assert_port_available(host: str, port: int) -> None:
    """
    이미 127.0.0.1:port 에서 리슨 중이면 connect_ex 가 0을 반환합니다.
    bind 사전검사는 Windows에서 10013이 나기 쉬워 제거했습니다.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(0.5)
    try:
        err = probe.connect_ex(("127.0.0.1", port))
    finally:
        probe.close()

    if err == 0:
        print()
        print(f"[오류] 포트 {port} 를 이미 다른 프로세스가 사용 중입니다 (연결 성공).")
        print("  - 이전에 실행한 python run_backend.py / uvicorn 을 종료하세요.")
        print("  - backend/.env 의 PORT 를 바꾸거나:")
        print()
        print("  (확인) netstat -ano | findstr :" + str(port))
        print("  (종료) taskkill /PID <위에서 본 PID> /F")
        print()
        sys.exit(1)

    # Windows: 10061 = 연결 거부 → 리슨 없음. Linux: errno 111
    if err not in (10061, 111):
        # 그 외는 대부분 ‘비어 있음’에 가깝지만, 알 수 없는 경우는 그대로 진행
        pass


if __name__ == "__main__":
    host = _parse_host()
    port = _parse_port()
    print(f"[Agri-Insight] API: http://127.0.0.1:{port}/docs  (host={host}, port={port})")
    _assert_port_available(host, port)

    import uvicorn
    from backend.app.main import app

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )
