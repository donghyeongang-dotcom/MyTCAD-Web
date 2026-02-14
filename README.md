# ⚡ AI-Powered Semiconductor Simulator (MyTCAD)
> 전자공학 전공 지식(Semiconductor Physics)을 바탕으로 수치해석 시뮬레이터를 직접 구현하고, Google Gemini API를 연동하여 실시간 AI 튜터링 기능을 탑재한 웹 애플리케이션입니다.

## 📌 1. 프로젝트 개요 (Overview)
반도체 소자의 동작 원리를 이해하기 위해 상용 TCAD 툴(Synopsys 등)을 사용하는 대신, Python으로 핵심 물리 엔진을 직접 구현했습니다.
여기에 LLM(Large Language Model)을 결합하여, 시뮬레이션 결과 그래프를 AI가 실시간으로 분석하고 설명해주는 교육용 플랫폼을 구축했습니다.

### 🚀 핵심 기능
1.  Physics Engine (자체 구현): 1D Poisson Equation을 FDM(유한차분법)으로 풀고 Newton-Raphson Method로 수렴시켜 PN 접합의 전위, 전기장, 전하 분포를 정밀하게 계산합니다.
2.  AI Tutor (Gemini Pro): 시뮬레이션 결과(도핑 농도, 바이어스 등)를 바탕으로 AI가 물리적 현상을 실시간으로 해석하고, 교수님 페르소나로 질의응답을 제공합니다.
3.  Interactive UI: Streamlit을 활용하여 파라미터(N_a, N_d, V_{bias})를 조절하며 즉각적인 물리량 변화를 시각화합니다.
4.  Database Integration: Supabase와 연동하여 실험 데이터를 클라우드에 저장 및 관리합니다.

---

## 🛠 2. 기술 스택 (Tech Stack)

| Language: Python 3.10+(전체 애플리케이션 로직 구현)
| Physics: `NumPy`, `SciPy`(행렬 연산, 비선형 미분방정식 수치해석 (Jacobian Matrix 계산)) 
| AI / LLM: `Google Gemini API`(시뮬레이션 결과 자동 분석 및 AI 튜터 챗봇 구현) 
| Web / UI: `Streamlit`(대화형 웹 대시보드 및 데이터 시각화) 
| Visualization: `Matplotlib`(Energy Band Diagram, I-V Curve 렌더링) 
| Database:  `Supabase` (시뮬레이션 로그 및 파라미터 저장 (Cloud DB)) 

---
```markdown
## 📂 3. 파일 구조 및 설명 (File Structure)

```bash
📦 Semiconductor-Simulator
 ┣ 📜 MyTCAD.py          # [Main] 시뮬레이션 메인 실행 파일 (UI + Physics Engine)
 ┣ 📜 ai_manager.py      # [AI Agent] Gemini API 연동 및 프롬프트 엔지니어링 모듈
 ┣ 📜 requirements.txt   # 프로젝트 의존성 라이브러리 목록
 ┗ 📜 README.md          # 프로젝트 설명서

🧠 핵심 코드 설명
MyTCAD.py
solve_pn_junction(): 포아송 방정식을 이산화(Discretization)하여 자코비안 행렬을 구성하고, 비선형 방정식을 풉니다.
calculate_iv_sweep(): 전압을 스윕(Sweep)하며 전류 밀도(J)를 계산하여 I-V 곡선을 생성합니다.

ai_manager.py:
AITutor 클래스: 시뮬레이션 변수(N_a, N_d, V_{bias})를 프롬프트에 동적으로 주입(Context Injection)합니다.
페르소나 설정: AI에게 "반도체 물리학 교수님" 역할을 부여하여 전문적인 해석을 제공하도록 설계했습니다.

📸 4. 실행 결과 (Screenshots)

(1) 물리적 특성 분석 (Spatial Distribution)
<img width="804" height="486" alt="image" src="https://github.com/user-attachments/assets/247a6299-668d-4c1f-9080-1f1510ed99d1" />
<img width="826" height="415" alt="image" src="https://github.com/user-attachments/assets/98461fff-a24a-4941-b17f-0b192fa5e67d" />
(2) AI 튜터 분석(AI Analysis)
<img width="806" height="430" alt="image" src="https://github.com/user-attachments/assets/959087c1-7e4d-4923-ae97-f3044b4a52c4" />
전위(Potential), 전기장(Electric Field), 전하 밀도(Charge Density), 캐리어 농도(Carrier Conc.)가 물리 법칙에 맞게 계산됨을 확인했습니다.
시뮬레이션 결과에 대해 AI가 "공핍층이 확장되는 원리" 등을 실시간으로 설명해줍니다.

💡 5. 향후 계획 (Future Works)
이 프로젝트는 단순한 수치해석을 넘어, 데이터 기반의 AI 모델링(Data-Driven AI)으로 확장할 계획입니다.
Physics-Informed Neural Networks (PINN): 미분방정식을 직접 푸는 대신, AI가 물리 법칙을 학습하여 연산 속도를 획기적으로 단축하는 연구를 진행할 예정입니다.
Inverse Design: 원하는 소자 특성(I-V)을 입력하면, AI가 역으로 최적의 공정 파라미터(N_a, N_d)를 제안하는 기능을 추가하고자 합니다.

⚠️ 설치 및 실행 (Installation)
레포지토리 클론
Bash git clone https://github.com/donghyeongang-dotcom/MyTCAD-Web.git

라이브러리 설치
Bash pip install -r requirements.txt

실행
Bash streamlit run MyTCAD.py
(Note: AI 기능을 사용하려면 .streamlit/secrets.toml에 Google Gemini API Key 설정이 필요합니다.)
