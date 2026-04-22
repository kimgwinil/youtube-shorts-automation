# 배경 파일 안내

`mood/style` 구조로 배경을 관리하세요. 같은 분위기 안에서도 실사, 수채화, 수묵화, 서화풍을 나눠 두면 자동 선택이 훨씬 안정적입니다.

예시:

```text
backgrounds/
  dawn/
    photoreal/
      sunrise.mp4
    watercolor/
      dawn_wash.png
    calligraphy/
      quiet_garden.png
  rain/
    ink/
      rainy_window.png
  city/
    photoreal/
      city_morning.mp4
```

스타일 키 예시:

- `photoreal`: 실사 사진, 현실적 영상
- `watercolor`: 수채화
- `ink`: 수묵화
- `calligraphy`: 서화풍, 동양화풍

스타일 폴더가 비어 있으면 `backgrounds/<mood>` 바로 아래 파일을 대신 사용합니다.
