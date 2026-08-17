repo: teo10a/orange-studio-portfolio
branch: main

## Last sync
date: 2026-08-17T12:32:00Z

### Updated in this project
- 업스트림에 새로 추가된 `guide.html`(A4 5쪽 서비스 소개서)을 확인
- 해당 문서를 `서비스 소개서.dc.html`로 재구축 (doc-page 기반, A4 고정 6쪽, 인쇄/PDF 대응)
- 원본에서 A4 한 장을 넘겼던 가격·FAQ 블록을 각각 별도 페이지로 분리
- 가격표·FAQ 표시 여부를 Tweaks 토글로 추가
- `index.html`은 이전에 반영한 배포본과 동일 — 변경 없음

## Screen map
| 프로젝트 화면 | 저장소 파일 |
| --- | --- |
| 주황색 영상공방.dc.html | index.html (WORKS 데이터, 섹션 구성, 카피) |
| 서비스 소개서.dc.html | guide.html (5쪽 소개서 전체 내용·가격표·FAQ) |
| deploy/index.html | index.html (배포본) |

## Sync history

### 2026-08-17T08:23:51Z
- 업스트림 변경 없음 — 저장소는 마지막 동기화 시점 그대로
- 배포용 파일 묶음(`deploy/`)을 준비

### 2026-08-17T08:10:00Z
- 기존 `index.html`을 Classical 디자인 시스템 위에서 재설계 (Design Component)
- 작업물을 전체화면 스크롤 + 좌측 인덱스 레일로 전환, 상세 오버레이 제거
- 절제된 스크롤 애니메이션(리빌·스티치 드로잉·숫자 카운트·진행 바) 추가
- 보정 전/후와 인물 사진을 드래그&드롭 이미지 슬롯으로 교체
