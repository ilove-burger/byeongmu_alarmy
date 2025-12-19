# 게시판 모니터링 및 알림

사회복무요원 관련 키워드를 포함한 신규 게시글을 자동으로 감지해 카카오톡과 이메일로 알림을 보내는 스크립트입니다.

## 요구사항

- Python 3.11+
- `requests`, `beautifulsoup4`, `schedule`, `python-dotenv`

## 설정

1. `.env.example`을 복사해 `.env`를 생성하고 값을 채웁니다.

```bash
cp .env.example .env
```

필수/주요 변수:

- `BOARD_URL`: 모니터링할 게시판 주소
- `FILTER_KEYWORD`: 제목 필터 키워드(기본값 `사회복무요원`)
- `POLL_INTERVAL_MINUTES`: 크롤링 주기(분)
- `STATE_DB_PATH`: 게시글 ID를 저장할 SQLite 경로
- `KAKAO_ACCESS_TOKEN`: 카카오 REST API 토큰
- 이메일 발송 설정:
  - `SMTP_HOST`, `SMTP_PORT`
  - `SMTP_USE_TLS` (기본 true: STARTTLS/587, SSL 465를 쓰면 false)
  - `SMTP_USER`, `SMTP_PASSWORD`
  - `EMAIL_FROM`, `EMAIL_TO`

## 실행 방법

### 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

### Docker

```bash
docker build -t board-monitor .
docker run --env-file .env board-monitor
```

### Docker Compose

`docker-compose.yml` 예시를 제공합니다.

```bash
docker compose up -d
```

### Systemd/cron 샘플

- `deploy/board-monitor.service`: systemd 서비스 예시
- `deploy/board-monitor.cron`: cron 항목 예시

파일 내용을 필요에 맞게 수정 후 설치합니다.

## 동작 개요

1. `src/monitor.py`: Requests + BeautifulSoup로 게시판 목록을 파싱해 제목, 게시글 ID/URL, 등록일을 추출합니다.
2. `src/state.py`: SQLite에 최근 본 게시글 ID를 저장/불러오기 하며 신규 게시글만 반환합니다.
3. `src/notifiers/kakao.py` & `src/notifiers/email.py`: 카카오 REST API와 SMTP로 알림을 발송합니다.
4. `src/main.py`: 주기적 크롤링 → 키워드 필터 → 신규 감지 시 알림 전송 파이프라인을 조립합니다.

## 배포 샘플

- `Dockerfile`, `docker-compose.yml`로 컨테이너 빌드 및 실행
- `deploy/board-monitor.service`: `/etc/systemd/system/board-monitor.service`로 배치 후 `systemctl enable --now board-monitor`
- `deploy/board-monitor.cron`: `crontab -e`에 삽입해 주기 실행
