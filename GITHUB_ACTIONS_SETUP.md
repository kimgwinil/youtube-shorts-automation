# GitHub Actions 완전 자동화 설정

이 구성은 GitHub Actions가 매일 `오전 7시 KST`에 자동 실행되어:

1. 서울 기준 날짜, 요일, 계절, 날씨를 읽고
2. 명언 풀에서 오늘 분위기에 맞는 글귀를 선택하고
3. AI로 한국어 대본과 새로운 배경 이미지를 생성하고
4. 절차적으로 새로운 배경음악을 생성하고
5. YouTube에 업로드한 뒤
6. `data/state.json`을 커밋해 중복을 피합니다

## 실행 시각

- GitHub cron: `0 22 * * *`
- UTC 기준 전날 22:00
- 한국 시간 기준 매일 07:00

주의:

- GitHub Actions 스케줄은 수분 단위 지연이 생길 수 있습니다.

## 필요한 GitHub Secrets

저장소의 `Settings > Secrets and variables > Actions`에 아래 값을 등록합니다.

### `OPENAI_API_KEY`

- OpenAI API 키
- 대본 생성과 배경 이미지 생성에 사용

### `YOUTUBE_CLIENT_SECRET_JSON`

- 현재 가지고 있는 `client_secret.json`의 전체 내용
- JSON 파일 내용을 그대로 붙여넣으면 됩니다

### `YOUTUBE_TOKEN_JSON`

- 현재 로컬에서 이미 생성된 `secrets/token.json`의 전체 내용
- GitHub Actions는 브라우저 인증을 할 수 없으므로 이 토큰이 필수입니다

## 현재 중복 방지 방식

- 최근 사용한 명언 제외
- 최근 제목과 유사한 표현 피하기
- 최근 이미지 fingerprint 피하기
- 날짜와 날씨를 반영한 배경음악 signature 생성
- 업로드 후 `data/state.json`을 저장소에 다시 커밋

## 중요한 파일

- 워크플로우: [.github/workflows/daily-youtube-short.yml](/Users/kimgwonil/youtube-shorts-automation/.github/workflows/daily-youtube-short.yml)
- 메인 실행 파일: [scripts/run_daily.py](/Users/kimgwonil/youtube-shorts-automation/scripts/run_daily.py)
- 상태 파일: [data/state.json](/Users/kimgwonil/youtube-shorts-automation/data/state.json)

## 설정 순서

1. 이 프로젝트를 GitHub 저장소로 올립니다.
2. 위 3개 Secret을 등록합니다.
3. `Actions` 탭에서 `Daily YouTube Short`를 `workflow_dispatch`로 1회 실행합니다.
4. 업로드 결과를 확인합니다.
5. 이후 매일 오전 7시 KST에 자동 실행됩니다.

## 중요한 제약

- GitHub Actions는 로컬처럼 파일을 계속 들고 있지 않으므로 매 실행마다 새 환경입니다.
- 따라서 배경 이미지와 음악은 그날 새로 생성하도록 구성했습니다.
- YouTube 토큰이 만료되면 로컬에서 다시 인증한 뒤 새 `token.json` 내용을 Secret으로 업데이트해야 합니다.

