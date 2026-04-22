# 유튜브 쇼츠 명언 자동화

매일 정해진 시간에 한국어 명언 쇼츠를 자동으로 생성하고 업로드하는 최소 파이프라인입니다.

## 구성

1. `content/quotes.yaml`에서 아직 사용하지 않은 명언 1개를 선택
2. 한국어 쇼츠용 긴 대본, 저자 표기, 배경 프롬프트, 제목/설명/태그 생성
3. 배경 이미지 또는 영상과 자막, 저자 패널, 배경음악을 합쳐 9:16 MP4 렌더링
4. YouTube Data API로 자동 업로드
5. `launchd` 또는 `cron`으로 매일 실행

## 폴더 구조

```text
youtube-shorts-automation/
  content/
    backgrounds/
    music/
    quotes.yaml
  data/
    state.json
  output/
  scripts/
    run_daily.py
  shorts_automation/
    config.py
    pipeline.py
    render.py
    script_builder.py
    upload.py
  launchd/
    com.kimgwonil.youtube-shorts-daily.plist
  .env.example
  requirements.txt
```

## 준비

### 1. 의존성 설치

```bash
cd /Users/kimgwonil/youtube-shorts-automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`를 복사해서 `.env`로 만들고 값을 채웁니다.

필수 항목:

- `YOUTUBE_CLIENT_SECRETS_FILE`: Google Cloud에서 받은 OAuth 클라이언트 JSON 파일 경로
- `YOUTUBE_TOKEN_FILE`: 최초 인증 후 저장할 토큰 파일 경로
- `FONT_FILE`: 한글 표시 가능한 폰트 경로
- `BACKGROUND_DIR`: 배경 이미지/영상 폴더

### 3. 유튜브 API 설정

Google Cloud Console에서 아래를 설정합니다.

1. 프로젝트 생성
2. `YouTube Data API v3` 활성화
3. OAuth 동의 화면 구성
4. `Desktop app` 유형의 OAuth Client 생성
5. 받은 JSON 파일 경로를 `.env`에 입력

첫 업로드 시 브라우저 인증이 1회 필요합니다.

## 콘텐츠 입력

`content/quotes.yaml`에 명언을 추가합니다.

```yaml
- author: "Confucius"
  source: "논어"
  quote: "군자는 말을 부끄러워하고 행동으로 증명한다."
  interpretation: "말보다 삶이 먼저다."
  mood: "dawn"
  visual_style: "calligraphy"
  bgm_mood: "meditative"
  context: "새벽 정원과 한지, 붓, 잔잔한 안개"
```

필드 설명:

- `mood`: 배경 장면 분위기
- `visual_style`: `photoreal`, `watercolor`, `ink`, `calligraphy`
- `bgm_mood`: 음악 폴더 선택 기준
- `context`: 배경 창작 프롬프트에 반영할 장면 설명

## 배경 파일

`content/backgrounds` 안에 아래처럼 넣습니다.

```text
content/backgrounds/
  dawn/
    photoreal/
      sunrise.mp4
    watercolor/
      calm_river.jpg
    calligraphy/
      dawn_garden.png
  rain/
    ink/
      rain_window.png
  city/
    photoreal/
      city_morning.mp4
```

지원 확장자:

- 이미지: `.jpg`, `.jpeg`, `.png`
- 영상: `.mp4`, `.mov`, `.m4v`

렌더링 시 메타데이터 JSON에 `visual_prompt`도 함께 저장됩니다. 이 프롬프트를 이미지 생성 도구에 넣어 배경을 계속 보강하면 됩니다.

## 배경음악 파일

`content/music/<bgm_mood>` 폴더에 음악 파일을 넣으면 자동으로 루프/페이드 처리되어 합성됩니다.

```text
content/music/
  meditative/
    bamboo_flute.mp3
  reflective/
    rain_piano.mp3
  focused/
    soft_strings.mp3
  default/
    ambient_pad.mp3
```

지원 확장자:

- `.mp3`, `.m4a`, `.wav`, `.aac`

## 실행

수동 실행:

```bash
cd /Users/kimgwonil/youtube-shorts-automation
source .venv/bin/activate
python scripts/run_daily.py
```

업로드 없이 렌더링만 테스트:

```bash
python scripts/run_daily.py --dry-run
```

실행 결과:

- 생성 영상: `output/YYYYMMDD_HHMMSS_*.mp4`
- 상태 저장: `data/state.json`

## 자동 실행

macOS에서는 `launchd` 사용을 권장합니다.

예시 plist 파일:

- [launchd/com.kimgwonil.youtube-shorts-daily.plist](/Users/kimgwonil/youtube-shorts-automation/launchd/com.kimgwonil.youtube-shorts-daily.plist)

등록 예시:

```bash
cd /Users/kimgwonil/youtube-shorts-automation
./scripts/install_launchd.sh
```

GitHub Actions로 노트북 없이 실행하려면 아래 문서를 따르세요.

- 워크플로우: [.github/workflows/daily-youtube-short.yml](/Users/kimgwonil/youtube-shorts-automation/.github/workflows/daily-youtube-short.yml)
- 설정 문서: [GITHUB_ACTIONS_SETUP.md](/Users/kimgwonil/youtube-shorts-automation/GITHUB_ACTIONS_SETUP.md)

## 권장 운영 방식

- 명언 풀은 최소 30개 이상 준비
- `backgrounds`는 `감정/스타일` 폴더로 분리
- `music`은 분위기별 폴더로 분리
- 업로드 제목은 50자 안쪽으로 유지
- 설명에는 저자, 원전, 한국어 해석 포함
- 상태 파일로 중복 업로드 방지

## 주의

- 자동 업로드 전에 비공개(`private`)로 충분히 테스트하는 것이 안전합니다.
- YouTube 정책상 반복적 대량 업로드는 제한될 수 있습니다.
- 완전 자동 명언 생성까지 원하면 이후 LLM 단계만 추가하면 됩니다. 현재 구조는 우선 안정적인 큐 기반 자동화입니다.

## 바로 해야 할 일

1. `.env.example`를 `.env`로 복사
2. `secrets/client_secret.json` 배치
3. `content/backgrounds/<mood>/<style>`에 배경 넣기
4. `content/music/<bgm_mood>`에 배경음악 넣기
5. `pip install -r requirements.txt`
6. `python scripts/run_daily.py --dry-run`으로 렌더링 테스트
7. 이상 없으면 `python scripts/run_daily.py`로 최초 인증 및 업로드 테스트

## 노트북 없이 자동 실행

현재 프로젝트는 두 가지 방식으로 실행할 수 있습니다.

- 로컬 자동화: `launchd`
- 완전 자동화: `GitHub Actions`

완전 자동화를 원하면 GitHub 저장소에 올린 뒤, 위 설정 문서대로 Secret을 등록하면 됩니다. 그러면 매일 오전 7시 KST에 GitHub가 직접 영상을 생성하고 업로드합니다.
