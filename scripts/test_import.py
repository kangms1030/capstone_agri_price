"""백엔드 임포트 검증 스크립트"""
import sys
sys.path.insert(0, r"c:\Users\minsoo\Desktop\capstone")

try:
    from backend.app.services.kamis import KamisClient
    print("[OK] kamis.py")
    from backend.app.services.predictor import CabbagePricePredictor
    print("[OK] predictor.py")
    from backend.app.services.explainer import PriceExplainer
    print("[OK] explainer.py")
    from backend.app.main import app
    print("[OK] main.py - FastAPI app loaded")
    print("\n=== Backend import OK! ===")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\n[ERROR] {e}")
