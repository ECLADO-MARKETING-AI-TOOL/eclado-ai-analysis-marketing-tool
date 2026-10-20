# Eclado Marketing AI

FastAPI와 Streamlit으로 구성한 ECLADO 사장님 대시보드 초안입니다. 공식몰에서 수집한 공개 상품명·표시 가격을 보여주며, 매출·환불·고객·리뷰는 실제 연동 대기입니다. 별도 모드에서 가상 실적 화면을 검토할 수 있습니다. Supabase 자동 저장·직원 로그인·Gemini·문자 발송은 아직 연결하지 않았습니다.

## Requirements

- Windows 10/11 with PowerShell
- Python 3.12 or newer
- `uv` package manager
- Supabase project and provider credentials are not needed for local checks

Install `uv` using the official Windows installer, then from this repository root run:

```powershell
uv sync
```

## Run locally

Start the API in one terminal:

```powershell
uv run uvicorn eclado_backend.main:app --app-dir backend --host 127.0.0.1 --reload
```

Start the admin screen in another terminal:

```powershell
uv run streamlit run admin/eclado_admin/main.py --server.headless=true
```

The API is available at `http://127.0.0.1:8000`; its OpenAPI page is at `/docs`. Streamlit is normally available at `http://localhost:8501`.

첫 화면은 데모 로그인입니다. 이메일 `user@example.com`, 비밀번호는 아무 값이나 한 글자 이상 입력하면 기존 분석 화면으로 바로 이동합니다. 사이드바의 로그아웃으로 로그인 화면에 돌아갑니다. 데모 세션은 현재 브라우저 연결에서만 유지되며 실제 Supabase Auth·권한 검사나 API 보호를 제공하지 않습니다. 입력 비밀번호는 인증 서버로 보내거나 저장·기록하지 않습니다.

로그인 후 기본 화면은 **매출 분석 → 매출 요약**입니다. 사이드바에서 **매출 추이**, **고객별 매출 추이**를 선택하세요. 2020년부터 조회하고, 이력이 없는 기간은 실제 0원으로 채우지 않습니다. 기존 가상 실적 또는 나중에 업로드할 더미 데이터로 화면을 확인할 수 있습니다. 각 화면의 **더미 데이터 연결**에서 JSON 예제 다운로드·업로드를 제공합니다. [1,000건 생성 전 입력 계약](docs/ver1-sales-analysis.md)을 먼저 확인하세요. 기존 카탈로그는 **상품·리뷰·AI** 메뉴에 있습니다.

상품은 **매출·상품** 탭에서 검색·분류·가격을 확인하세요. **공식몰 상품 · 실적 연동 대기**가 기본이며, 화면의 매출 예시를 보려면 왼쪽에서 **가상 실적 화면 미리보기**를 선택하세요. 가상 시나리오 기간은 2026-09-06~2026-10-20입니다. 실제 실적과 공개 가격을 혼합해 해석하지 않습니다.

공유 DTO를 변경한 뒤 기존 화면에서 `DashboardResponse` 속성 오류가 나면 Streamlit 터미널에서 `Ctrl+C`로 서버를 종료하고 위 명령으로 다시 실행하세요. 브라우저 새로고침이나 Streamlit의 데이터 새로고침만으로는 실행 중인 Python의 이전 모델이 교체되지 않을 수 있습니다.

백엔드 주소를 변경할 때만 실행 환경에 `ECLADO_API_BASE_URL`을 설정합니다. 공개 카탈로그 재수집과 실제 데이터→Supabase→요약→AI 연동 방향은 [Ver.1 초안 안내](docs/ver1-preview.md)를 참고하세요. API와 Streamlit은 로컬 주소로 실행하며, 실제 고객 데이터 연결 전에 인증·역할 검사를 구현해야 합니다.

## Checks

```powershell
uv run pytest
uv run ruff check .
uv run mypy
```

## Project layout

- `backend/eclado_backend/api/routers/`: HTTP endpoints and request/response handling
- `backend/eclado_backend/services/`: business rules and orchestration
- `backend/eclado_backend/stores/`: persistence boundary; runtime SQL belongs here
- `admin/eclado_admin/`: Streamlit pages and UI components
- `admin/eclado_admin/repositories/`: the only admin layer that calls backend APIs
- `shared/eclado_shared/`: shared API transport and schemas; no database access
- `supabase/migrations/`: reviewed, ordered database schema changes
- `docs/`: architecture, decisions, and client change tracking

See [docs/architecture.md](docs/architecture.md) before adding integrations or handling production customer data.
