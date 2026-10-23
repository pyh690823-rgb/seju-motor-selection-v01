SEJUMOTION Motor Selection Dashboard V0.1
=============================================

[목적]
세주모션 모터 PDF 사양을 구조화한 67개 Motor Specification Archive와
Ball Screw / Belt 설계 계산 Logic을 연결한 Local Prototype입니다.

[중요]
이 프로그램은 최종 모터 선정/설계 승인 도구가 아닙니다.
현재 Archive에는 Torque-Speed Curve, Rated/Maximum Torque,
최대/허용 회전속도, Driver Matching 정보가 충분하지 않습니다.
따라서 Holding Torque와 Rotor Inertia를 이용한 '1차 후보 Screening' 용도입니다.

[처음 1회]
1. Python 설치
2. 이 폴더의 01_최초1회_설치.bat 더블클릭
3. 설치 완료까지 진행

[이후 실행]
1. run_local.bat 더블클릭
2. 브라우저가 열리면 Dashboard 사용
3. 종료하려면 실행 중인 CMD 창에서 Ctrl+C 또는 창 닫기

[기본 체험]
Ball Screw 예:
- Work Mass 10 kg
- 이동거리 0.3 m
- ta 0.1 s / tb 0.8 s / td 0.1 s / Cycle 2.0 s
- 효율 0.9 / 마찰계수 0.1
- Screw Length 0.5 m / Diameter 0.02 m / Lead 0.02 m/rev

Belt 예:
- Work Mass 2 kg
- 이동거리 1.0 m
- ta 0.1 s / tb 0.8 s / td 0.1 s / Cycle 2.0 s
- 효율 0.8 / 마찰계수 0.1
- Pulley Diameter 0.05 m / Pulley Mass 0.5 kg

[데이터]
data/SEJUMOTION_Motor_Specification_Archive_Integrated_67models.xlsx

[향후 고도화]
- 57SJM4972-21B 추가
- Torque-Speed Curve
- Rated Torque / Maximum Torque
- Max / Operating Speed
- Driver Matching
- 제조사별 허용 관성비
- Shaft / Mount Dimension
