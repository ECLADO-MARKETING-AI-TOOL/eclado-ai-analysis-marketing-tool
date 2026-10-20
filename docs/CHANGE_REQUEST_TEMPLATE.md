# Client Change Request

## Ver.1 후속 요청 · 사이드바 공식 ECLADO 로고

- 요청/승인: 2026-10-20 대화 요청자. 확정: 왼쪽 사이드바의 임시 브랜드 표시를 공식 로고로 교체.
- 구현: 로그인에서 사용 중인 공식몰 원본 PNG를 그대로 사용. 흰색 패널·원래 비율·대체 텍스트 적용. 색상 변형/재제작/외부 이미지 호출 없음.
- 검증/복구: pytest/Ruff/mypy 및 실제 Edge 표시 확인. 테마의 brand 렌더/CSS를 복원하면 복구 가능. 데이터·인증·DB·커밋 변경 없음.

## Ver.1 수정 요청 · 새로고침 로그인 복원 안정화

- 요청/확정: 2026-10-20 대화 요청자, 새로고침해도 로그인 만료되지 않도록 요청. 기존 60분 고정 기한은 유지하며 새로고침을 로그아웃 사유로 삼지 않음.
- 발견한 취약점: 이전 확인 정보는 Streamlit 서버 메모리에만 있어 서버 재시작 시 소실. 브라우저 창은 유지되고 Streamlit 세션만 재연결되면 전역 중복 보고 방지 코드가 토큰 재전달을 막을 수 있음.
- 수정: backend `preview_session_store`에 토큰 해시/만료 시각만 SQLite로 저장. router → service → store, admin repository → shared transport 경유. 브라우저는 세션별 request ID를 사용해 토큰 재보고. 복원 실패와 서버 연결 장애를 구분.
- 저장/보안: `.local/preview_sessions.sqlite3`는 Git 제외인 로컬 데모 세션 저장소. 비밀번호/이메일/고객 정보/원문 토큰 저장 없음. 만료 세션은 새 토큰 발급 시 정리. API는 데모 UI 연속성 전용이며 공개 예제 API의 운영 인증/권한을 구현한 것이 아님.
- 수명: 로그인부터 60분이며 새로고침으로 연장 안 함. 서버 재시작 후에도 유효 기한 안에서 복원. 같은 탭 sessionStorage는 탭 종료 시 사라지며 브라우저 저장이 차단되면 복원 불가. 이전 메모리 토큰은 전환 후 한 번 재로그인 필요. 이 항목은 앞선 기록의 ‘서버 재시작 시 재로그인’ 한계를 대체함.
- 검증: 38개 테스트, Ruff/mypy 통과. 스토어/서비스 재생성 후 복원·만료 경계·해시만 저장·로그아웃 폐기·새 웹소켓 세션 재보고 검증. 실제 Edge 브라우저 로그인 후 3회 새로고침 유지, 로그아웃 후 새로고침 시 로그인 화면 확인.
- 복구: 새 admin/API/service/store/DTO 변경을 이전 방식으로 복원하고 서버 재시작. 세션 파일 제거 시 해당 세션은 재로그인 필요. 매출 더미·카탈로그·Supabase DB는 변경하지 않음. 운영 DB 마이그레이션·발송·커밋 없음.

## Ver.1 후속 요청 · 단일 매출 분석 메뉴와 리뷰/매출 급변

- 요청/확정: 2026-10-20 대화 요청자. 매출 분석 아래 네 화면, 긍정/부정/급증 리뷰 Top 10, 월 이동평균 10% 이상 매출/주문수량 변화와 연령층 변화 요청. 신제품은 출시 후 30일 이내로 추가 확정.
- 제안/확인 필요: 30일 평균 비교 구간, 리뷰 증가 7일 비교, 점수 건수순 순위는 화면에 명시한 초안. 현재 더미의 상품 출시일 미제공이므로 확정 목록과 미확인 후보 분리. 담당자/최종 검토 일자는 확인 필요.
- 구현: 단일 sidebar 라디오 네 메뉴, 동일 매출 API/DTO의 insights service 집계, 신제품 출시일 선택 매핑과 검증, 기존 카탈로그 보존. 상세 [정의·검증·복구](ver1-product-insights.md).
- 검증: 36개 테스트 및 Ruff/mypy. 실제 API와 AppTest로 Top 10, 급변 후보/연령층, 공식 상품 가격 보존 확인. 더미 데이터/가격/실제 연동/발송/DB 적용/커밋 변경 없음.

## Ver.1 수정 요청 · 더미는 있지만 매출 분석이 비어 보이는 현상

- 요청/근거: 2026-10-20 대화 요청자, 더미 저장 여부와 분석 미표시 문제 확인 요청. 저장 파일과 실제 API 조회에서 데이터 유지·정상 집계 확인.
- 원인/수정: 실제 실적 미연동 모드가 기본값. 초안의 매출 데이터 기본 선택을 업로드 더미로 변경하고, 명시적 소스 선택은 유지. 실제 실적 대기에 더미 전환 버튼, 더미에 전체 기간 버튼 추가.
- 확인값: 2026-10-01~20에 주문 398건/순상품매출 96,788,655원. 전체 기간과 월 조회의 숫자는 다름. 더미 2,000고객/2,000주문/400리뷰 보존.
- 검증: AppTest로 로그인 직후 더미 기본 분석, 실제 대기 전환 시 가상 합계 미표시, 버튼 재전환, 전체 기간 적용 검증. pytest/Ruff/mypy 실행. repository 경유 유지, DB·산식·실제 연동·커밋 변경 없음.
- 상태/복구: 로컬 미리보기 수정. 최종 사용자 확인 필요. 소스 기본값/추가 버튼을 복원하고 Streamlit 재시작하면 되며 데이터 재적재 불필요.

## Ver.1 후속 요청 · 새로고침 시 로그인 60분 유지

- 요청/승인: 2026-10-20 대화 요청자. 확정: 새로고침 후 로그인 복원, 유지 시간 60분.
- 구현 기준: 로그인부터 60분 고정 기한. 같은 탭의 sessionStorage에는 임의 토큰/만료 시각만 저장하고 서버 메모리에 토큰 해시와 만료 시각을 보관. 모든 복원은 서버 검증. 새로고침은 기한 연장 안 함. 만료 타이머로 재실행하고 로그인 화면 복귀. 로그아웃은 서버 토큰과 브라우저 저장 모두 폐기.
- 한계: 로컬 데모 UI 인증이며 Supabase JWT/역할/API 보안 구현이 아님. 서버 재시작·탭 종료 시 재로그인. 브라우저 저장 차단 시 현재 세션 로그인은 가능하지만 새로고침 복원 불가. 필터 선택은 새로고침 시 기본값으로 복원될 수 있음.
- 변경: admin 세션 레지스트리/브라우저 컴포넌트/로그인, Streamlit 최소 1.66 및 lock. 외부 스크립트·URL 토큰·비밀번호 저장·DB/매출/더미 변경 없음.
- 검증: 서버 만료 경계·무효 토큰·로그아웃 폐기, 새 Streamlit 세션에서 복원 및 만료 차단 AppTest, Node에서 브라우저 JS의 저장/새로고침/타이머/삭제/저장 차단 검증. pytest/Ruff/mypy 실행. 실제 브라우저 전체 동작 시각 검토는 별도.
- 복구: admin 세션 관련 변경과 최소 버전/lock을 이전 상태로 복원하고 Streamlit 재시작. 현재 토큰은 무효화되며 데이터 복구 작업 없음. 운영 출시·실제 Auth 연동 승인과 별개.
- 참고 API: https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component

## Ver.1 후속 요청 · 2,000건 더미 데이터 저장 및 시험

- 요청/승인: 2026-10-20 대화 요청자. 확정 범위: 다양한 매출·고객·리뷰 합성 데이터 생성, 테스트 저장소에 적재 후 유지, 서버/화면 연결 확인. 실제 데이터/API 접근 승인과 별개.
- 구현 해석: 고객 2,000명과 주문 2,000건, 전체 고객 20%인 400명이 리뷰 작성. 400명 반복 구매/400명 미구매, 남녀·10~80대·시군구 지역, 단일/복수 상품·할인·환불 제공.
- 선택 필드 추가: 지역, 항목 용량/EAN, 리뷰. 구매 연결 및 작성일·중복 검증, 리뷰/지역 집계 UI. `routers → services → stores` 및 admin repository 경유 유지.
- 데이터: `.local/sales_dummy.json` 영구 저장, Git 제외. 로컬 JSON 테스트 저장소이며 Supabase 적재를 의미하지 않음. 원본 카탈로그 가격/규격 유지. 최종 화면 만족 여부는 요청자 확인 필요.
- 검증/복구: [데이터·대사·재현·복구 기록](ver1-dummy-seed.md). 31개 테스트, Ruff/mypy 및 실제 로컬 API/AppTest 검증. 데이터 유지, 메시지·실제 개인정보 접근·마이그레이션·커밋 없음.

## Ver.1 후속 요청 · 로그인 로고와 제목

- 요청일/담당자: 2026-10-20, 대화 요청자. 확정: ECLADO 로고·색상 및 `ECLADO 매출 분석 및 AI마케팅 도우미` 제목을 로그인 상단 중앙에 표시. 승인 근거: 사용자 대화 지시.
- 구현: 공식몰 로고를 로컬에 보관, 접근성 대체 텍스트, 로열블루 제목(화면별 약 25~40px), 하늘색·라벤더 배경과 흰색 로그인 카드. 최종 시각 검토는 사용자 확인 필요.
- 범위/복구: 로그인 표현만 변경. 인증 정책·가격·매출·API/DB 변경 없음. 헤더·CSS·로고 파일을 이전 상태로 복원하면 복구 가능.
- 검증: 기존 로그인·로그아웃 및 분석 화면 AppTest와 pytest/Ruff/mypy 실행. 운영 출시 아님.

## Ver.1 후속 요청 · ECLADO 테마 및 대시보드 디자인

- 요청일/담당자: 2026-10-20, 대화 요청자. 참고 화면 배치와 최신 첨부 ECLADO 색상 혼합 요청.
- 확정: 블루·하늘색·라벤더·흰색 테마 적용 범위. 승인 근거는 사용자 대화 지시.
- 제안: 이미지 기반 근사 색상 `#2534a4` / `#69b5f5` / `#8a85cf`, 네이비 사이드바, 흰색 카드, 강조 KPI 그라데이션. 공식 색상값·최종 화면 승인 담당자/일자는 확인 필요.
- 구현: 공통 테마, 로그인/메뉴/지표/차트 패널과 AI 추천 카드 배치, 최근 14일 매출·주문금액대 가로 막대. 음수·누락 및 정확한 금액 표시 유지.
- 변경 경계: 상품 가격·용량/EAN·매출 정책·API/DB·실제 연동·발송·커밋 변경 없음. repository 접근 유지.
- 검증: pytest 28개 통과, Ruff/mypy 및 Streamlit AppTest 실행. 로그인·세 매출 화면·1,000건 가상 입력·기존 카탈로그 회귀 확인. 실제 브라우저 픽셀 검토 미실시.
- 상태/복구: 로컬 초안 구현, 사용자 화면 검토 대기. 테마 모듈·UI·Streamlit 설정을 이전 상태로 복원 후 재시작. DB 작업 없음.

Use one copy per client-requested release (Ver.1, Ver.2, ...). Keep each version small enough to test and roll back independently.

## Request

- Business version:
- Request date / requester:
- Problem and desired outcome:
- Acceptance criteria:
- Impacted users, data, and workflows:
- Out of scope:

## Implementation record

- Git branch:
- Planned release tag (for example `v1.0.0`):
- Changed files / modules:
- API or admin behavior changes:
- Database migration(s):
- Privacy, consent, or permission impact:
- Provider/configuration changes:

## Verification and release

- Tests and results (`uv run pytest`, `uv run ruff check .`, `uv run mypy`):
- Manual acceptance check:
- Deployment steps:
- Rollback steps (including database rollback or forward-fix):
- Monitoring / owner:
- Release date and notes added to `CHANGELOG.md`:

## Ver.1 요청 기록 — 명세 검토 단계

### Request

- Business version: Ver.1 (미출시, 문서 초안 작성·업무 검토 대기).
- Request date / requester: 2026-10-20 (Asia/Seoul), 대화 요청자(실명 미기록).
- Problem and desired outcome: Cafe24 접근과 미결정 매출 정책을 코드로 가정하지 않도록 연동 전 데이터 계약·지표 명세와 승인 조건을 문서화한다.
- Acceptance criteria: 필드 의미·형식·필요 여부·누락 처리·목적, 매출 산식·가상 예제·미결정 목록, 결정별 상태·승인 담당자·일자·근거 및 접근 승인 체크리스트를 기록한다.
- Impacted users, data, and workflows: 사업·재무·데이터·개인정보 담당자의 명세 검토와 향후 Ver.1 구현 착수 판단. 실제 데이터는 수집하지 않는다.
- Out of scope: 연동 코드, API/DTO, DB 마이그레이션, 실제 데이터/API 접근, 발송, Gemini 전송, 배포, 커밋.

### Implementation record

- Git branch / planned release tag: 해당 없음. 이번 단계에서 브랜치·태그·커밋을 생성하지 않음.
- Changed files / modules: `docs/ver1-data-contract.md`, `docs/ver1-sales-metrics.md`, 이 파일, `CHANGELOG.md`.
- API or admin behavior changes / database migrations: 없음.
- Privacy, consent, or permission impact: 추가 수집·접근 권한 없음. 직원 인증과 구매 고객 식별을 분리해 검토하고, 기존 SQL의 고객=`auth.users` 가정은 채택하지 않음. 실제 모델·권한·보관·삭제는 승인 대기.
- Provider/configuration changes: 없음. Cafe24 사용·API/공식 내보내기 방법·권한·범위 미확인.
- Confirmed decision: 환불 완료일 차감, 환불로 원결제일 매출을 재작성하지 않음(요청자, 2026-10-20, 대화 선택).
- Pending decisions: 결제일 기준 순상품매출은 제안. 할인·적립금·세금·취소/환불 연결·고객/채널 범위·AOV·대사 오차 등은 각 명세의 승인표에서 관리.

### Verification and release

- Tests and results (2026-10-20): 문서만 변경. 기본 `uv run`은 사용자 전역 캐시 접근 거부로 실행되지 않아 작업공간 캐시와 기존 환경을 사용한 `uv --cache-dir .cache/uv run --offline --no-sync <command>`로 재검증. `pytest`: 2 passed(기존 httpx 사용 중단 예정 경고 및 pytest 캐시 생성 경고), `ruff check .`: 통과, `mypy`: 20개 소스 파일 통과. 문서 UTF-8·상대 파일 링크·계산 예제 산술 확인 통과. 실제 원천 매핑·관리자 대사·업무 승인은 미완료.
- Manual acceptance check: 두 명세의 상태·산식·월 경계 예제·승인 조건·상호 링크를 검토. 미정 Cafe24 필드/엔드포인트를 확정하지 않음.
- Deployment steps: 없음. 접근·매출 정책·개인정보 승인 후 승인 범위의 구현을 별도 진행.
- Rollback steps: 이번에 추가한 두 명세와 요청·변경 기록의 해당 추가분을 문서 이력에서 되돌림. DB rollback/forward-fix 해당 없음.
- Monitoring / owner: 문서 검토 단계, 사업·재무·데이터·개인정보 승인 담당자 미지정.
- Release date and notes added to `CHANGELOG.md`: 출시일 없음. Ver.1 명세 검토 상태만 기록.

## Ver.1 후속 요청 기록 — 화면 초안·공식몰 상품

### Request

- Business version / date / requester: Ver.1, 2026-10-20 (Asia/Seoul), 대화 요청자(실명 미기록).
- Desired outcome: Streamlit 초안을 보며 반복 수정. 공식몰 전체 공개 상품명·가격을 반영하고, 향후 실제 행동·고객 프로필·구매/환불/리뷰를 Supabase에 자동 저장해 사장님 요약과 AI 마케팅 제안으로 연결.
- Acceptance criteria: 공식몰 공개 카탈로그의 전체 페이지 수집·상품 ID 중복 제거·관측 근거 표시, 매출/상품/리뷰/고객/추천 탭·기간·정렬·연동 대기 상태 제공. 가상 실적은 별도 명시. 실제 데이터 연동 요구사항·미결정 사항 보존.
- Out of scope for this preview: 실제 고객 데이터 접근·Supabase 운영 저장·직원 로그인·Gemini 생성·메시지 발송·배포·커밋. 해당 기능을 완료로 표시하지 않음.

### Implementation record

- Changed modules: dashboard router/service/store, 공개 카탈로그 collector·snapshot store, shared dashboard DTO, admin dashboard repository·Streamlit, fake/API/UI 테스트, 로컬 테마와 문서.
- API/admin behavior: `/api/v1/dashboard/preview` 추가, 기본 pending·선택 demo, 기간 검증. 공개 카탈로그 검색/분류·가격/출처, 집계·순위·구매 목록·추천 미리보기. 관리자 API 통신은 repository 경유.
- Data provenance: 공개 분류 목록 70페이지, 상품 116개, 유형별 표시 건수 116개와 대사 일치. 실제 상품명·표시 가격만 수집. 비공개·미노출·삭제 상품 제외. 가격별 관측과 수집 이력 보존.
- Database / providers: DB 마이그레이션·적용 없음. 공개 목록 수집만 명시적으로 실행. 외부 AI·메시지·고객 API 연결 없음. 로그인 우회·보호 페이지 접근 없음.
- Permissions/privacy: 개인식별 정보 수집 없음. 직원 Auth와 고객 ID 분리·프로필 최소 수집·역할/RLS·보관/삭제·제공자 승인은 후속 실제 연동 조건.
- Metric policy: 환불 완료일 차감 유지. 나머지 정책은 데모 전용 시나리오이며 실제 정책 확정 아님. 기타 매출·AOV 미확정.

### Verification and release

- Tests and results (2026-10-20): `uv --cache-dir .cache/uv run --offline --no-sync pytest -p no:cacheprovider` 13 passed; 같은 uv 옵션의 `ruff check .` 통과, `mypy` 30개 소스 파일 통과. 외부 자격증명 없이 fake·로컬 공개 스냅샷·Streamlit AppTest로 기간/환불/집계/정렬/미연동/연결 실패/parser/중복/건수 대사 검증. 기존 httpx 사용 중단 예정 경고, Windows sandbox의 테스트 종료 시 임시 디렉터리 정리 권한 오류와 Ruff 탐색 경고가 있었으며 세 명령의 종료 코드는 모두 0. 제품 기능 실패는 없음.
- Manual acceptance: 실행 중 로컬 API와 admin repository 실제 호출에서 pending/demo 모두 catalog 116개 확인, pending totals 없음·demo totals 존재 확인. Streamlit `/_stcore/health` 정상. 문서 상대 링크·UTF-8 검사 통과. 실제 원장 관리자 대사와 업무 승인은 미완료.
- Deployment / rollback: 운영 배포 없음. 로컬 실행·복구 절차는 `docs/ver1-preview.md` 참고. DB rollback 해당 없음.
- Owner / release: 검토 요청자, 운영 승인 담당자 미지정. 미출시.

## Ver.1 오류 복구 — 이전 DashboardResponse 모델

- 요청일 / 요청자: 2026-10-20, 대화 요청자. 화면의 `AttributeError: DashboardResponse ... catalog` 스크린샷 제보.
- 원인·조치: 파일에는 catalog가 있으나 기존 Streamlit 프로세스가 이전 공유 모델을 유지한 상황. 로컬 8501 서버를 재시작해 최신 모델 로드, README에 DTO 변경 후 재시작 안내 추가.
- 검증: 실제 로컬 백엔드 연결(모킹 없음) Streamlit AppTest의 기본 모드에서 상품 116개, 가상 모드에서 지표 7개 렌더링·예외 없음. 서버 health 정상. 연결된 브라우저가 없어 브라우저 화면 직접 검증은 미실시. 기존 테스트 임시 디렉터리 정리 권한 경고는 제품 렌더링과 별개.
- 변경 범위 / 복구: 실행 프로세스·문서만 변경, DB/API/정책 변경·배포·커밋 없음. 재시작 시 화면 선택 상태는 초기화될 수 있음.

## Ver.1 후속 요청 — 분류 제거·용량/EAN 추가

- 요청일 / 요청자: 2026-10-20, 대화 요청자. 영문 Excel을 한국어 상품과 정확히 대조하고 용량·EAN만 추가, 기존 분류 제거, 가격 유지.
- 인수 기준 / 결과: 분류 열·필터 및 실적 표의 분류 제거. 82개 상품·94개 규격 연결, 34개 상품은 동일 상품·규격 확인 불가로 보류. 여러 용량의 EAN을 쌍으로 표시하고 단위 충돌·원본 EAN 중복·미기재를 별도 안내.
- 변경 범위: shared DTO·dashboard service·catalog store·Streamlit·규격 참조 JSON·테스트. 원천 영문명/행·원본 SHA256 보존. Excel 가격과 Sample 시트는 사용하지 않음.
- 가격·보안: 기존 공개 가격 스냅샷 바이트 불변 확인. 원본 Excel 수정 없음. 고객 데이터·DB·마이그레이션·제공자 연동·발송·커밋 없음.
- 검증: pytest 16 passed, Ruff 통과, mypy 31개 소스 통과. 전역 캐시 제한에 따라 기존 작업공간 캐시 옵션 사용. 테스트 종료 임시파일 정리 권한·탐색 경고는 기존 환경 제한.
- 출처·예외·복구: `docs/ver1-product-specifications.md` 참조. 미출시, 원본 EAN 충돌의 업무 확인 대기.

## Ver.1 후속 요청 — 데모 로그인

- 요청일 / 요청자: 2026-10-20, 대화 요청자. `user@example.com`과 임의 비밀번호로 로그인하고 기존 분석 화면으로 바로 이동.
- 구현·인수: 로그인 폼·비밀번호 마스킹·Streamlit 세션 로그인 게이트·사이드바 로그아웃 추가. 이메일은 공백 제거·대소문자 정규화 후 데모 주소만 허용. 비밀번호는 길이·형식 제한 없이 비어 있지 않은 값 허용. 로그인 전 분석 화면/데이터 요청 차단, 성공 후 자동 전환, 로그아웃 후 세션 삭제·로그인 화면 복귀. 재로그인은 기본 실제 실적 연동 대기 모드로 시작.
- 보안·아키텍처: 로컬 UI 검토용 세션이며 Supabase Auth·JWT·서버 역할·API 보호를 구현한 것이 아님. API는 기존 공개 카탈로그·가상 실적 preview만 유지. 비밀번호는 콜백에서 처리 후 세션 제거하며 백엔드/외부 제공자 전송·파일 저장·로그 기록 없음. 기존 데이터 repository 경유 유지.
- 변경: admin `demo_auth.py`, main, 화면 테스트 및 문서. DB·마이그레이션·가격·상품 규격·고객 데이터·제공자 설정·커밋 변경 없음.
- 검증: pytest 18 passed(로그아웃 상태의 API 미호출·잘못된 이메일·빈 비밀번호·임의 한 글자 비밀번호·자동 분석 전환·로그아웃·재로그인·기존 분석 화면 포함). 작업공간 uv 캐시 옵션 사용. 기존 테스트 종료 임시 디렉터리 정리 권한 경고 존재.
- 최종 확인: Ruff 통과, mypy 32개 소스 통과. 서버 재시작 후 모킹 없는 로컬 백엔드 연결 AppTest로 로그인→상품 116개 분석 화면→로그아웃→로그인 화면 복귀 확인. Streamlit health 정상.
- 출시·복구: 로컬 초안, 운영 인증 미완료. 복구 시 로그인 게이트·사이드바 로그아웃·추가 모듈/테스트를 이전 상태로 복원하고 Streamlit 재시작. DB 작업 없음.

## Ver.1 후속 요청 — 사이드바 매출 분석

- 요청일 / 요청자: 2026-10-20, 대화 요청자. 취소선처럼 보인 내용을 포함해 매출 요약·매출 추이·고객별 매출 추이와 향후 1,000건 더미 연결 요청.
- 인수 결과: 로그인 후 기본 메뉴 매출 분석, 하위 세 화면. 월/일/기간 매출·Top 120·환불·평균 주문금액·반복 구매 고객·비교 기간, 2020년부터 20/30/365일 이동평균, 1/7/30일 상승·하락별 최대 5개 Alert와 그래프/표·금액대 분포, 10~80대/성별/행동 고객군 필터·월별 추이.
- 더미 데이터: JSON 계약·예제 다운로드·업로드·서버 검증·원자적 store 교체·재시작 재조회. 현재는 합성 데이터 전용이며 1,000명·1,000주문은 테스트에서만 생성. 실제 화면 데이터는 사용자가 나중에 생성/업로드.
- 중요 기본값: 월/연 이동평균=30/365일 후행 단순 평균, 알림=직전 동일 구간 대비 절대 50%+10만원 이상(조절 가능), 고객 최소 표본 5명, 연령=구매연도−직접 제공 출생연도. 실제 매출 정책 확정 아님.
- 변경 범위: sales DTO·router·services·store·repository·Streamlit 화면/사이드바·더미 입력 transport·회귀 테스트·문서. 공개 상품 가격·용량/EAN 자료 유지. 기존 상품/리뷰/AI는 별도 메뉴로 보존.
- 보안/출시: 실제 개인정보·Supabase·직원 Auth/역할·제공자 연동·발송·DB 마이그레이션·배포·커밋 없음. 로컬 더미 파일은 git 제외.
- 검증: pytest 28 passed, Ruff 통과, mypy 39개 소스 파일 통과. 서버 재시작 후 실제 로컬 API를 사용하는 AppTest로 로그인·세 매출 페이지·기존 상품 116개 화면 전환을 예외 없이 확인. API pending/demo/dummy 모드 응답 정상, 더미 미입력 상태 유지, 공개 가격 파일 해시 불변·문서 링크 정상. 기존 테스트 종료 임시 디렉터리 정리 권한·탐색 경고는 환경 제한.
- 계약·예외·복구: `docs/ver1-sales-analysis.md`. 미출시, 실제 데이터 연동·업무 승인 대기.
