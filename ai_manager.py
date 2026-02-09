import google.generativeai as genai
import streamlit as st
import numpy as np

class AITutor:
    def __init__(self):
        # 1. API 키 설정 (secrets.toml에서 가져옴)
        try:
            if "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
                api_key = st.secrets["gemini"]["api_key"]
                genai.configure(api_key=api_key)
                # [중요] 사용자 계정에서 확인된 최신 모델 사용
                self.model = genai.GenerativeModel('gemini-2.5-flash') 
                self.is_active = True
            else:
                self.is_active = False
        except Exception as e:
            print(f"AI 초기화 오류: {e}")
            self.is_active = False

    def get_analysis(self, config, result, mode="spatial"):
        """
        자동 분석 함수
        mode: 'spatial' (물리적 특성 4개 그래프) 또는 'iv' (I-V 커브)
        """
        if not self.is_active:
            return "⚠️ API 키가 설정되지 않았거나 오류가 발생했습니다. (.streamlit/secrets.toml 확인 필요)"

        # 1. [Dashboard] 물리적 특성 4개 그래프 해석 모드
        if mode == "spatial":
            prompt = f"""
            당신은 반도체 물리학 교수님입니다. 학생이 시뮬레이션을 돌린 결과(그래프 4개)를 보고 있습니다.
            
            [현재 설정]
            - Na: 1e{np.log10(config.Na):.1f}, Nd: 1e{np.log10(config.Nd):.1f}, Bias: {config.bias_voltage}V
            
            [요청 사항]
            다음 4가지 그래프의 형태와 물리적 원리를 **각각 한 문장씩 요약**해서 설명해주세요.
            **공핍층 폭이나 전위 장벽의 구체적인 수치는 언급하지 말고**, 그래프가 왜 이런 모양이 나왔는지 **물리적 원리 위주**로 설명하세요.
            
            1. **전위 (Potential):** 전위 장벽의 형성 원리와 바이어스에 따른 변화
            2. **전기장 (Electric Field):** 접합부에서 최대치가 되는 이유
            3. **전하 밀도 (Space Charge):** 공핍층 내 고정 전하($N_a^-$, $N_d^+$)의 분포
            4. **캐리어 농도 (Carrier Conc):** 다수 캐리어와 소수 캐리어의 분포 차이 및 공핍층 형성
            """

        # 2. [I-V Curve] 전류-전압 특성 해석 모드
        elif mode == "iv":
            prompt = f"""
            당신은 반도체 물리학 교수님입니다. 학생이 생성한 PN 접합 다이오드의 I-V 커브(전류-전압 곡선)를 분석해주세요.
            
            [현재 설정]
            - Na: 1e{np.log10(config.Na):.1f}, Nd: 1e{np.log10(config.Nd):.1f}
            
            [요청 사항]
            Linear Scale과 Log Scale 그래프를 보고 다음 내용을 학생에게 설명하듯 쉽게 풀어서 써주세요.
            1. **Turn-on Voltage (문턱 전압):** 전류가 급격히 흐르기 시작하는 구간과 그 이유 (확산 전류 vs 드리프트 전류 균형 깨짐)
            2. **Leakage Current (누설 전류):** 역방향 바이어스에서도 미세하게 흐르는 전류의 원인 (소수 캐리어)
            3. **Rectification (정류 작용):** 왜 전류가 한쪽 방향으로만 잘 흐르는지 요약
            """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI 응답 생성 실패: {e}"

    def chat_with_student(self, user_question, config):
        """
        자유 질문(Q&A) 함수 - 여기서는 구체적인 수치를 물어봐도 됨
        """
        if not self.is_active:
            return "⚠️ AI 기능이 활성화되지 않았습니다."

        try:
            context = f"""
            현재 시뮬레이션 상황: 
            Na=1e{np.log10(config.Na):.1f}, Nd=1e{np.log10(config.Nd):.1f}, Bias={config.bias_voltage}V.
            
            학생 질문: {user_question}
            
            위 상황을 고려하여 답변해주세요. 학생이 '공핍층 폭'이나 '전위차' 같은 구체적인 수치를 물어본다면 계산된 값을 바탕으로 친절하게 알려주세요.
            """
            response = self.model.generate_content(context)
            return response.text
        except Exception as e:
            return f"오류 발생: {e}"

# 외부에서 import 할 수 있도록 인스턴스 생성
ai_tutor = AITutor()