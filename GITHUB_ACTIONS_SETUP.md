# GitHub Actions 완전 자동화 설정

이 구성은 GitHub Actions가 매일 `오전 7시 KST`에 자동 실행되어:

1. 서울 기준 날짜, 요일, 계절, 날씨를 읽고
2. 명언 풀에서 오늘 분위기에 맞는 글귀를 선택하고
3. AI로 한국어 대본과 새로운 배경 이미지를 생성하고
4. Gemini Lyria RealTime으로 배경음악을 생성하고, 실패 시 분위기별 라이브러리 음원으로 fallback 한 뒤
5. YouTube에 업로드한 뒤
6. `data/state.json`을 커밋해 중복을 피합니다

중요:

- 이 방식은 `GitHub 서버`에서 실행됩니다.
- 따라서 `내 컴퓨터가 꺼져 있어도` 자동 업로드가 계속 동작합니다.
- 조건은 저장소가 GitHub에 푸시되어 있고, `Actions`가 활성화되어 있으며, 필요한 `Secrets`가 모두 등록되어 있어야 합니다.

## 실행 시각

- GitHub cron: `0 22 * * *`
- UTC 기준 전날 22:00
- 한국 시간 기준 매일 07:00

주의:

- GitHub Actions 스케줄은 수분 단위 지연이 생길 수 있습니다.
- GitHub 스케줄 실행은 기본 브랜치의 워크플로만 사용합니다.
- 저장소가 장기간 비활성 상태면 스케줄 워크플로가 일시 중지될 수 있습니다. 이 경우 `Actions` 탭에서 다시 활성화하면 됩니다.

## 필요한 GitHub Secrets

저장소의 `Settings > Secrets and variables > Actions`에 아래 값을 등록합니다.

### `OPENAI_API_KEY`

- OpenAI API 키
- 대본 생성과 배경 이미지 생성에 사용

### `GEMINI_API_KEY`

- Gemini API 키
- Lyria RealTime 배경음악 생성에 사용
- 값이 없거나 생성이 실패해도 `content/music/<bgm_mood>` 라이브러리 음원이 있으면 업로드는 계속 진행됩니다

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

## 배경과 BGM 생성 동작

- 배경 이미지는 명언 분위기에 맞추되 `반복 캐릭터 금지`, `얼굴 클로즈업 금지`, `배경 중심 장면` 제약을 적용합니다
- BGM 우선순위는 `Gemini 생성 -> content/music/<bgm_mood> 라이브러리 음원 -> 로컬 합성 fallback` 입니다
- 따라서 Actions 환경에서 Gemini가 일시 실패해도 분위기별 음원 파일이 준비되어 있으면 저역 합성음으로 바로 내려가지 않습니다

## 중요한 파일

- 워크플로우: [.github/workflows/daily-youtube-short.yml](/Users/kimgwonil/youtube-shorts-automation/.github/workflows/daily-youtube-short.yml)
- 메인 실행 파일: [scripts/run_daily.py](/Users/kimgwonil/youtube-shorts-automation/scripts/run_daily.py)
- 상태 파일: [data/state.json](/Users/kimgwonil/youtube-shorts-automation/data/state.json)

## 설정 순서

1. 이 프로젝트를 GitHub 저장소로 올립니다.
2. 위 4개 Secret을 등록합니다.
3. `Actions` 탭에서 `Daily YouTube Short`를 `workflow_dispatch`로 1회 실행합니다.
4. 업로드 결과를 확인합니다.
5. 이후 매일 오전 7시 KST에 자동 실행됩니다.

## 꼭 확인할 점

1. 저장소 기본 브랜치가 `main`인지 확인합니다.
2. `Settings > Actions > General`에서 Actions 실행이 허용되어 있는지 확인합니다.
3. `Settings > Secrets and variables > Actions`에 아래 4개 Secret이 모두 들어 있는지 확인합니다.
4. `Actions > Daily YouTube Short`에서 수동 실행 1회를 성공시킵니다.
5. 이후에는 로컬 Mac 전원이 꺼져 있어도 GitHub가 자체적으로 실행합니다.
6. 첫 실행 후 `output` 메타데이터 또는 Actions 로그에서 실제 선택된 BGM 경로와 배경 결과를 확인합니다.

## 중요한 제약

- GitHub Actions는 로컬처럼 파일을 계속 들고 있지 않으므로 매 실행마다 새 환경입니다.
- 따라서 배경 이미지와 음악은 그날 새로 생성하도록 구성했습니다.
- 다만 음악은 Gemini 생성 실패 시에도 `content/music/<bgm_mood>`의 저장소 자산을 사용할 수 있도록 구성했습니다.
- YouTube 토큰이 만료되면 로컬에서 다시 인증한 뒤 새 `token.json` 내용을 Secret으로 업데이트해야 합니다.
