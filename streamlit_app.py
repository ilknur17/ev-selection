import streamlit as st
import pandas as pd
import numpy as np

# Load the cleaned EV dataset
@st.cache_data
def load_data():
    return pd.read_excel("waspas.xlsx", skiprows=3).iloc[:, 2:11].dropna().rename(columns={
        "Brand": "Brand",
        "Model": "Model",
        "Body Type": "Body Type",
        "Range": "Range",
        "Safety": "Safety",
        "Resale Value & Depreciation": "Resale Value",
        "Acceleration (0–100)": "Acceleration",
        "Torque (Nm)": "Torque",
        "Charging Time (10–80%)": "Charging Time"
    })

df = load_data()

# Define criteria and direction
criteria = {
    "Range": "max",
    "Safety": "max",
    "Resale Value": "max",
    "Acceleration": "min",
    "Torque": "max",
    "Charging Time": "min"
}

# --------------- 1. LOGIN SCREEN ---------------
if "username" not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url('4babadfc-ff34-4568-ab8a-d0443be4926c.png');
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
        .login-box {{
            background-color: rgba(255, 255, 255, 0.8);
            padding: 2rem;
            border-radius: 10px;
            width: 300px;
            margin: auto;
            margin-top: 20vh;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    username = st.text_input("Enter your name to start:")
    if st.button("Login"):
        if username.strip():
            st.session_state.username = username.strip()
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --------------- 2. WELCOME SCREEN ---------------
elif "weights" not in st.session_state:
    st.title(f"Welcome, {st.session_state.username}! 👋")

    st.markdown("""
    ### Welcome to the EV Selection Assistant

    This intelligent system helps you choose the most suitable electric vehicles based on **your preferences** using the **WASPAS decision-making method**.

    You'll be asked to rate how important each criterion is to you from **1 (Very Unimportant)** to **5 (Very Important)**.
    """)

    if st.button("Next"):
        st.session_state.weights = {}
        st.experimental_rerun()

# --------------- 3. WEIGHT INPUT SCREEN ---------------
elif st.session_state.weights == {}:
    st.title("Step 2: Rate the Importance of Each Criterion")

    sliders = {}
    for crit in criteria:
        sliders[crit] = st.slider(f"{crit} Importance", 1, 5, 3)

    if st.button("Calculate"):
        st.session_state.weights = sliders
        st.experimental_rerun()

# --------------- 4. WASPAS CALCULATION AND OUTPUT ---------------
else:
    st.title("🚗 Your Top 3 EV Recommendations")

    weights = st.session_state.weights
    weight_values = np.array(list(weights.values()), dtype=float)
    weight_values /= weight_values.sum()  # Normalize

    norm_df = pd.DataFrame()
    for i, (crit, goal) in enumerate(criteria.items()):
        col = df[crit]
        if goal == "max":
            norm_df[crit] = col / col.max()
        else:
            norm_df[crit] = col.min() / col

    # WASPAS scores
    wsm = norm_df.mul(weight_values).sum(axis=1)
    wpm = norm_df.pow(weight_values).prod(axis=1)
    waspas_score = 0.5 * wsm + 0.5 * wpm

    result_df = df.copy()
    result_df["WASPAS Score"] = waspas_score
    top3 = result_df.sort_values("WASPAS Score", ascending=False).head(3)

    for i, row in top3.iterrows():
        top_factors = [crit for crit, v in weights.items() if v >= 4]
        st.markdown(f"""
        ### 🏆 {row['Brand']} {row['Model']}
        - **Body Type**: {row['Body Type']}
        - **WASPAS Score**: `{row['WASPAS Score']:.4f}`
        - **Why?** This EV stands out for its performance in:  
          **{', '.join(top_factors)}**
        """)

    with st.expander("Show Full Results Table"):
        st.dataframe(result_df.sort_values("WASPAS Score", ascending=False))
