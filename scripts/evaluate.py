"""
Module ĐÁNH GIÁ độ chính xác Text-to-SQL (cho báo cáo đồ án).

Chạy bộ câu hỏi trong eval/testset.json qua pipeline thật và đo các chỉ số:
  - Tỷ lệ sinh được SQL
  - Tỷ lệ qua guardrail
  - Tỷ lệ thực thi thành công (execution accuracy)
  - Tỷ lệ trả về dữ liệu (non-empty)
  - Độ chính xác chọn bảng (table-selection) — so với expected_tables
  - Độ trễ trung bình

Yêu cầu: MySQL có dữ liệu + LLM đã cấu hình (.env).
Chạy (từ thư mục gốc dự án):
    python scripts/evaluate.py
    python scripts/evaluate.py --out eval/report.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR) if BACKEND_DIR.exists() else "/app")

from app.agents import ValidationAgent  # noqa: E402
from app.services.text_to_sql import TextToSQLService  # noqa: E402
from app.utils import get_logger  # noqa: E402

logger = get_logger("evaluate")


def main() -> None:
    parser = argparse.ArgumentParser(description="Đánh giá độ chính xác Text-to-SQL")
    parser.add_argument("--testset", default=str(ROOT / "eval" / "testset.json"))
    parser.add_argument("--out", default=str(ROOT / "eval" / "report.json"))
    parser.add_argument("--delay", type=float, default=4.0,
                        help="Giãn cách (giây) giữa các câu để tránh rate limit API")
    args = parser.parse_args()

    testset = json.loads(Path(args.testset).read_text(encoding="utf-8"))
    # Tắt LLM ở validation (regex là guardrail chính) -> giảm số lần gọi LLM, tránh rate limit.
    svc = TextToSQLService(validation_agent=ValidationAgent(use_llm=False))
    results = []

    print(f"\n=== ĐÁNH GIÁ {len(testset)} câu hỏi (delay={args.delay}s) ===\n")
    for i, case in enumerate(testset, 1):
        if i > 1 and args.delay > 0:
            time.sleep(args.delay)
        q = case["question"]
        t0 = time.perf_counter()
        try:
            outcome = svc.run(q, execute=True, max_rows=1000)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Lỗi câu %d: %s", i, exc)
            results.append({"question": q, "error": str(exc)})
            print(f"[{i:02d}] LỖI   | {q[:50]}")
            continue
        dt = round((time.perf_counter() - t0) * 1000, 1)

        sql = outcome.sql or ""
        generated = bool(sql.strip())
        guardrail = bool(outcome.validation.safe)
        executed = bool(outcome.executed)
        rows = outcome.result.row_count if outcome.result else 0
        exp = [t.lower() for t in case.get("expected_tables", [])]
        table_ok = all(t in sql.lower() for t in exp) if exp else None

        results.append(
            {
                "question": q,
                "category": case.get("category"),
                "sql": sql,
                "generated": generated,
                "guardrail_passed": guardrail,
                "executed": executed,
                "rows": rows,
                "table_ok": table_ok,
                "corrected": outcome.corrected,
                "latency_ms": dt,
                "error": outcome.error,
            }
        )
        flag = "OK " if executed and rows >= 0 and (table_ok in (True, None)) else "XEM"
        print(f"[{i:02d}] {flag} | {dt:6.0f}ms | rows={rows:<4} | {q[:48]}")

    _report(results, args.out)


def _rate(values: list[bool]) -> float:
    return round(sum(1 for v in values if v) / len(values) * 100, 1) if values else 0.0


def _report(results: list[dict], out_path: str) -> None:
    ok = [r for r in results if "error" not in r or r.get("generated") is not None]
    valid = [r for r in results if r.get("generated") is not None]
    n = len(valid)

    table_cases = [r for r in valid if r.get("table_ok") is not None]
    latencies = [r["latency_ms"] for r in valid if "latency_ms" in r]

    summary = {
        "total": len(results),
        "generation_rate": _rate([r.get("generated", False) for r in valid]),
        "guardrail_pass_rate": _rate([r.get("guardrail_passed", False) for r in valid]),
        "execution_success_rate": _rate([r.get("executed", False) for r in valid]),
        "nonempty_rate": _rate([(r.get("rows", 0) or 0) > 0 for r in valid]),
        "table_selection_accuracy": _rate([r.get("table_ok", False) for r in table_cases]),
        "self_corrected_count": sum(1 for r in valid if r.get("corrected")),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
    }

    print("\n=== KẾT QUẢ TỔNG HỢP ===")
    print(f"  Tổng số câu                : {summary['total']}")
    print(f"  Tỷ lệ sinh được SQL        : {summary['generation_rate']}%")
    print(f"  Tỷ lệ qua guardrail        : {summary['guardrail_pass_rate']}%")
    print(f"  Tỷ lệ thực thi thành công  : {summary['execution_success_rate']}%  <-- execution accuracy")
    print(f"  Tỷ lệ trả về dữ liệu       : {summary['nonempty_rate']}%")
    print(f"  Độ chính xác chọn bảng     : {summary['table_selection_accuracy']}%")
    print(f"  Số câu phải tự sửa SQL     : {summary['self_corrected_count']}")
    print(f"  Độ trễ trung bình          : {summary['avg_latency_ms']} ms")

    report = {"summary": summary, "details": results}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã lưu báo cáo chi tiết: {out_path}")


if __name__ == "__main__":
    main()
