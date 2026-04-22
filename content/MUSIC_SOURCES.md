# 배경음악 소스 가이드

## 가장 안전한 기본 선택

### 1. YouTube Audio Library

- 위치: YouTube Studio > `Audio library`
- 공식 안내: https://support.google.com/youtube/answer/3376882?hl=en-EN
- 장점:
  - YouTube가 저작권 안전하다고 안내하는 음원
  - 쇼츠/일반 영상 운영과 궁합이 가장 좋음
  - 분위기, 길이, attribution 여부로 필터 가능

운영 팁:

- `Attribution not required` 우선 사용
- 차분한 명언 채널이면 `Ambient`, `Cinematic`, `Classical`, `Meditation`, `Piano` 계열 중심으로 선택
- 곡 길이는 `30초 이상` 권장

YouTube는 오디오 라이브러리 음원과 효과음을 `copyright-safe`라고 안내합니다. 다만 Creative Commons 곡은 설명란에 출처 표기가 필요할 수 있습니다.

### 2. 직접 제작 또는 직접 연주

- 가장 깔끔한 방식
- 저작권 추적 이슈가 거의 없음
- 대금, 피아노, 패드, 빗소리 같은 짧은 루프를 만들어 넣으면 좋음

## 배경 이미지/영상 소스

### 1. Pexels

- 공식 라이선스 안내: https://help.pexels.com/hc/en-us/articles/360042295174-What-is-the-license-of-the-photos-and-videos-on-Pexels
- 요약:
  - 무료 사용 가능
  - 개인/상업 목적 사용 가능
  - 출처 표기 필수 아님

주의:

- 원본 그대로 재판매하는 방식은 피해야 함
- 브랜드, 인물, 초상권 이슈가 있는 화면은 보수적으로 사용

### 2. Pixabay

- 공식 라이선스 요약: https://pixabay.com/ko/service/license-summary/
- 요약:
  - 무료 사용 가능
  - 수정/가공 가능
  - 출처 표기 필수 아님

주의:

- 콘텐츠를 원본 그대로 독립적으로 판매/배포하는 것은 금지

## 음악 선택 기준

명언 채널에는 아래 기준이 잘 맞습니다.

- `meditative`: 대금, 명상 패드, 느린 피아노
- `reflective`: 빗소리 질감, 낮은 현악, 잔잔한 피아노
- `focused`: 미니멀 피아노, 부드러운 스트링, 절제된 앰비언트

피해야 할 것:

- 보컬이 강한 곡
- 훅이 너무 강한 곡
- 드럼 드롭이나 큰 전환이 있는 곡
- 저작권 표기 조건이 불명확한 음원

## 폴더에 넣는 방법

```text
content/music/
  meditative/
  reflective/
  focused/
  default/
```

파일 확장자:

- `.mp3`
- `.m4a`
- `.wav`
- `.aac`

## 추천 운영 순서

1. YouTube Audio Library에서 `Attribution not required` 필터 사용
2. 분위기별로 3~5곡씩만 먼저 다운로드
3. `content/music/<bgm_mood>`에 저장
4. `--dry-run`으로 실제 자막과 음악 분위기 확인
5. 채널 톤에 맞지 않는 곡은 바로 교체

## 확인한 공식 자료

- YouTube Audio Library 도움말: https://support.google.com/youtube/answer/3376882?hl=en-EN
- YouTube 저작권 안전 음악 찾기 팁: https://support.google.com/youtube/answer/15577610?hl=en
- Pexels 라이선스: https://help.pexels.com/hc/en-us/articles/360042295174-What-is-the-license-of-the-photos-and-videos-on-Pexels
- Pixabay 라이선스 요약: https://pixabay.com/ko/service/license-summary/
