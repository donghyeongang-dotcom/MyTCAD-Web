import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from types import SimpleNamespace # AI에게 데이터 넘길 때 객체처럼 만들기 위해 사용

# AI 매니저 모듈 불러오기
try:
    from ai_manager import ai_tutor
    ai_available = True
except ImportError:
    ai_available = False
    st.warning("⚠️ 'ai_manager.py' 파일이 없습니다. AI 기능을 사용할 수 없습니다.")

# ==========================================
# 1. 페이지 설정 및 초기화
# ==========================================
st.set_page_config(
    layout="wide",
    page_title="MyTCAD - Semiconductor Simulator",
    page_icon="⚡"
)

# --- DB 연결 (Resource Caching) ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except Exception:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_supabase()

# --- 세션 상태 초기화 ---
if "na_log" not in st.session_state: st.session_state.na_log = 16.0
if "nd_log" not in st.session_state: st.session_state.nd_log = 16.0
if "bias_val" not in st.session_state: st.session_state.bias_val = 0.0
# I-V 스윕 실행 여부 체크용
if "iv_done" not in st.session_state: st.session_state.iv_done = False

# --- 콜백 함수 ---
def load_params_callback(na, nd, bias):
    st.session_state.na_log = float(na)
    st.session_state.nd_log = float(nd)
    st.session_state.bias_val = float(bias)

# ==========================================
# 2. 물리 엔진 (Physics Engine)
# ==========================================
@st.cache_data
def solve_pn_junction(Na, Nd, V_bias):
    L_cm = 2.0e-4
    N_points = 200
    x_cm = np.linspace(0, L_cm, N_points)
    dx = x_cm[1] - x_cm[0]
    x_um = x_cm * 1e4
    
    q = 1.602e-19; eps_si = 11.7 * 8.854e-14; ni = 1.5e10; VT = 0.0259

    junction_idx = N_points // 2
    net_doping = np.zeros(N_points)
    net_doping[:junction_idx] = -Na
    net_doping[junction_idx:] = Nd
    
    V_bi = VT * np.log(Na * Nd / ni**2)
    current_barrier = V_bi - V_bias
    
    V = np.zeros(N_points)
    V[:junction_idx] = -current_barrier / 2
    V[junction_idx:] = current_barrier / 2
    
    A = np.zeros((N_points, N_points))
    for i in range(1, N_points-1):
        A[i, i-1] = 1; A[i, i] = -2; A[i, i+1] = 1
    A = A / (dx**2)
    
    # Newton-Raphson Solver
    for i in range(20): 
        V_safe = np.clip(V, -5, 5)
        n = ni * np.exp(V_safe / VT)
        p = ni * np.exp(-V_safe / VT)
        rho = q * (net_doping + p - n)
        F = np.dot(A, V) + rho / eps_si
        F[0] = 0; F[-1] = 0
        J = A.copy()
        d_rho = (q/eps_si) * (-p/VT - n/VT)
        np.fill_diagonal(J, J.diagonal() + d_rho)
        J[0,:]=0; J[0,0]=1; J[-1,:]=0; J[-1,-1]=1
        delta_V = np.linalg.solve(J, -F)
        V += delta_V
        if np.max(np.abs(delta_V)) < 1e-5: break
            
    E_field = -np.gradient(V, dx)
    term = max(0, V_bi - V_bias)
    W_theory = np.sqrt((2 * eps_si * term / q) * ((Na + Nd) / (Na * Nd))) * 1e4
    
    return x_um, V, n, p, rho, E_field, V_bi, W_theory

@st.cache_data
def calculate_iv_sweep(Na, Nd):
    q = 1.602e-19; ni = 1.5e10; VT = 0.0259
    mu_n = 1400; mu_p = 450
    Dn = mu_n * VT; Dp = mu_p * VT
    tau_n = 1e-6; tau_p = 1e-6
    Ln = np.sqrt(Dn * tau_n); Lp = np.sqrt(Dp * tau_p)
    
    bias_sweep = np.linspace(-2.0, 0.8, 50)
    Js = q * ni**2 * ((Dn / (Ln * Na)) + (Dp / (Lp * Nd)))
    currents = Js * (np.exp(bias_sweep / VT) - 1)
    
    return bias_sweep, currents

# ==========================================
# 3. UI 및 시뮬레이션 제어
# ==========================================
st.title("⚡ MyTCAD: 반도체 물성 교육용 시뮬레이터")

with st.sidebar:
    st.header("🎛️ 파라미터 제어")
    st.slider("Na (P-type) 10^x", 14.0, 18.0, step=0.1, key="na_log")
    st.slider("Nd (N-type) 10^x", 14.0, 18.0, step=0.1, key="nd_log")
    st.number_input("인가 전압 (Bias V)", min_value=-5.0, max_value=1.0, step=0.1, key="bias_val")
    st.divider()
    
    Na = 10**st.session_state.na_log
    Nd = 10**st.session_state.nd_log
    V_bias = st.session_state.bias_val
    
    # 메인 시뮬레이션 실행
    _, _, _, _, _, _, V_bi, W_dep = solve_pn_junction(Na, Nd, V_bias)
    
    st.info(f"**📊 실시간 분석**\n- **$W_{{dep}}$:** `{W_dep:.3f} μm`\n- **$V_{{bi}}$:** `{V_bi:.3f} V`")
    
    if st.button("💾 결과 DB 저장", use_container_width=True):
        if supabase:
            try:
                data = {"input_params": {"Na": Na, "Nd": Nd, "bias_val": V_bias}, "results_summary": {"W_dep": W_dep, "V_bi": float(V_bi)}}
                supabase.table("simulation_logs").insert(data).execute()
                st.toast("✅ 저장 완료!", icon="💾")
            except Exception as e:
                st.error(f"저장 실패: {str(e)}")
        else:
            st.error("DB 연결 정보 없음")

# 메인 데이터 가져오기
x_um, V, n, p, rho, E, _, _ = solve_pn_junction(Na, Nd, V_bias)

tab1, tab2, tab3 = st.tabs(["📈 물리적 특성 (Dashboard)", "⚡ I-V 특성 곡선", "📜 실험 기록 (History)"])

# --- Tab 1: 물리적 특성 ---
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown(f"### 🔍 PN 접합 내부 분석 (Bias: {V_bias}V)")
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    plt.tight_layout(pad=3.0)
    
    axes[0,0].plot(x_um, V, 'r-'); axes[0,0].set_title("1. Electric Potential"); axes[0,0].grid(True)
    axes[0,1].plot(x_um, E/1e3, 'g-'); axes[0,1].set_title("2. Electric Field (kV/cm)"); axes[0,1].grid(True)
    axes[1,0].plot(x_um, rho, 'm-'); axes[1,0].set_title("3. Space Charge Density"); axes[1,0].ticklabel_format(style='sci', axis='y', scilimits=(0,0)); axes[1,0].grid(True)
    axes[1,1].semilogy(x_um, n, 'b-', label='n'); axes[1,1].semilogy(x_um, p, 'r--', label='p'); axes[1,1].set_title("4. Carrier Conc."); axes[1,1].legend(); axes[1,1].grid(True); axes[1,1].set_ylim(1e4, 1e19)
    st.pyplot(fig)
    plt.close(fig)

# --- Tab 2: I-V 커브 ---
with tab2:
    st.markdown("### ⚡ Current-Voltage Characteristics")
    if st.button("🚀 스윕 시뮬레이션 시작 (Run Sweep)"):
        st.session_state.iv_done = True # 실행 기록
        with st.spinner("계산 중..."):
            volts, currents = calculate_iv_sweep(Na, Nd)
            iv_fig, iv_ax = plt.subplots(1, 2, figsize=(12, 5))
            plt.tight_layout(pad=3.0)
            iv_ax[0].plot(volts, currents*1000, 'b-'); iv_ax[0].set_title("Linear Scale"); iv_ax[0].grid(True)
            iv_ax[1].semilogy(volts, np.abs(currents), 'r-'); iv_ax[1].set_title("Log Scale"); iv_ax[1].grid(True)
            st.pyplot(iv_fig)
            plt.close(iv_fig)

# --- Tab 3: 히스토리 ---
with tab3:
    st.markdown("### 📜 실험 기록 (History)")
    if st.button("🔄 새로고침"): st.rerun()
    if supabase:
        try:
            response = supabase.table("simulation_logs").select("*").order("created_at", desc=True).limit(5).execute()
            if response.data:
                st.dataframe(pd.DataFrame(response.data)[['created_at', 'input_params', 'results_summary']])
            else: st.info("기록 없음")
        except: st.info("기록 로딩 실패")

# ==========================================
# 4. [AI 튜터] 통합 섹션
# ==========================================
if ai_available:
    st.divider()
    st.markdown("### 🤖 AI 반도체 랩 튜터")
    st.caption("그래프 해석이 필요한가요? 아래에서 분석할 대상을 선택하세요.")

    col_ai_left, col_ai_right = st.columns([1, 1])
    current_config = SimpleNamespace(Na=Na, Nd=Nd, bias_voltage=V_bias)
    current_result = SimpleNamespace(depletion_width=W_dep, v_bi=V_bi)

    # [왼쪽] 분석 요청 (Radio Button)
    with col_ai_left:
        st.info("💡 **물리적 현상 분석 (Auto-Analysis)**")
        analysis_mode = st.radio("분석할 그래프 선택:", ("📊 공간 분포 (Potential, E-Field 등)", "⚡ I-V 특성 곡선 (Current-Voltage)"), index=0)
        
        if st.button("🔍 선택한 그래프 해석 요청", use_container_width=True):
            with st.spinner("AI 교수님이 분석 중입니다..."):
                if "공간 분포" in analysis_mode:
                    explanation = ai_tutor.get_analysis(current_config, current_result, mode="spatial")
                else:
                    if not st.session_state.iv_done:
                        explanation = "⚠️ **먼저 '⚡ I-V 특성 곡선' 탭에서 [스윕 시뮬레이션 시작] 버튼을 눌러주세요!** 데이터가 없어서 분석할 수 없습니다."
                    else:
                        explanation = ai_tutor.get_analysis(current_config, current_result, mode="iv")
                
                st.markdown(f"""<div style="background-color:#f0f2f6; padding:15px; border-radius:10px; border-left: 5px solid #4CAF50;">{explanation}</div>""", unsafe_allow_html=True)

    # [오른쪽] 채팅창
    with col_ai_right:
        st.info("💬 **심화 질문 (Q&A)**")
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        chat_container = st.container(height=300)
        with chat_container:
            for role, text in st.session_state.chat_history:
                with st.chat_message(role): st.write(text)
        
        if prompt := st.chat_input("예: 공핍층 폭이 정확히 얼마야?"):
            st.session_state.chat_history.append(("user", prompt))
            with chat_container:
                with st.chat_message("user"): st.write(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("생각 중..."):
                        answer = ai_tutor.chat_with_student(prompt, current_config)
                        st.write(answer)
                        st.session_state.chat_history.append(("assistant", answer))