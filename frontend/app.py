import os
import json
import requests
import streamlit as st
import plotly.express as px
import pandas as pd
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Correct model
model = genai.GenerativeModel("models/gemini-2.5-flash")

def ai_reply(prompt, context):
    try:
        full_prompt = f"""
        You are a smart analytics assistant.

        Use the data below carefully and give precise answers.

        If data is insufficient, say so.

        Data:
        {json.dumps(context, indent=2)}

        User Question:
        {prompt}

        Answer clearly and concisely.
        """

        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        return f"Error: {str(e)}"
    
    
# --- PDF ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Student Analytics", layout="wide", page_icon="📊")

# -------------------------
# Theme Toggle (session)
# -------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def apply_theme(theme: str):
    if theme == "dark":
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0f172a, #1e293b); color: #e5e7eb; }
                    h1, h2, h3, h4, h5, h6, p, span, div {
                        color: #e5e7eb !important;
                    }

                    [data-testid="stDataFrame"] {
                        background-color: #1e293b !important;
                        color: white !important;
                    }
        .card { background: rgba(255,255,255,0.05); padding:20px; border-radius:16px;
                backdrop-filter: blur(12px); box-shadow:0 8px 32px rgba(0,0,0,.25); margin-bottom:20px; }
        .title { font-size:40px; font-weight:700; background: -webkit-linear-gradient(#38bdf8,#6366f1);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .stButton>button { border-radius:10px; background: linear-gradient(90deg,#6366f1,#38bdf8);
                           color:white; border:none; padding:.6em 1em; font-weight:600; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
                    /* Fix input box background */
                    input, textarea {
                        background-color: white !important;
                        color: black !important;
                    }

                    /* Fix chat input specifically */
                    [data-testid="stChatInput"] textarea {
                        background-color: white !important;
                        color: black !important;
                        border: 1px solid #ccc !important;
                    }
                            .stApp {
            background: linear-gradient(135deg, #f1f5f9, #ffffff);
            color: #0f172a;
        }
                    
                    h1, h2, h3, h4, h5, h6, p, span, div {
                        color: #0f172a !important;
                    }

                    [data-testid="stDataFrame"] {
                        background-color: white !important;
                        color: black !important;
                    }

                    input, textarea {
                        color: black !important;
                    }

                    [data-testid="stChatMessage"] {
                        color: black !important;
                    }

        /* Fix all text visibility */
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #0f172a !important;
        }

        /* Fix dataframe */
        [data-testid="stDataFrame"] {
            background-color: white !important;
            color: black !important;
        }

        /* Fix input boxes */
        input, textarea {
            color: black !important;
        }

        /* Fix chat bubbles */
        [data-testid="stChatMessage"] {
            color: black !important;
        }
        .card { background: #ffffff; padding:20px; border-radius:16px;
                box-shadow:0 8px 32px rgba(0,0,0,.08); margin-bottom:20px; }
        .title { font-size:40px; font-weight:700; color:#0f172a; }
        .stButton>button { border-radius:10px; background: linear-gradient(90deg,#2563eb,#22c55e);
                           color:white; border:none; padding:.6em 1em; font-weight:600; }
        </style>
        """, unsafe_allow_html=True)

apply_theme(st.session_state.theme)

# ✅ ADD HERE (outside both)
st.markdown("""
<style>
.stChatMessage {
    border-radius: 10px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# Chatbot helper
# -------------------------
def local_assistant(prompt: str, context: dict) -> str:
    # simple deterministic helper (no API)
    p = prompt.lower()
    if "top" in p:
        return f"Top students (by total marks): {context.get('top_students', [])[:3]}"
    if "average" in p:
        return f"Average marks by subject: {context.get('avg_marks', [])}"
    if "students" in p:
        return f"Total students: {len(context.get('students', []))}"
    return "I can answer about students, averages, top performers, and predictions."


# -------------------------
# PDF generator
# -------------------------
def build_pdf(file_path, metrics: dict, students: list, avg: list):
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph("Student Analytics Report", styles["Title"]))
    elems.append(Spacer(1, 12))

    elems.append(Paragraph(f"Total Students: {metrics.get('students')}", styles["Normal"]))
    elems.append(Paragraph(f"Total Records: {metrics.get('records')}", styles["Normal"]))
    elems.append(Spacer(1, 12))

    # table: average marks
    table_data = [["Subject", "Average Marks"]]
    for r in avg:
        table_data.append([r["subject"], round(r["average_marks"], 2)])

    t = Table(table_data)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))
    elems.append(Paragraph("Average Marks by Subject", styles["Heading2"]))
    elems.append(t)

    doc.build(elems)


# -------------------------
# 🔥 ADD HERE (TOP LEVEL)
# -------------------------
def kpi_card(title, value, icon):
    st.markdown(f"""
    <div style="
        padding:20px;
        border-radius:15px;
        background: linear-gradient(135deg,#6366f1,#38bdf8);
        color:white;
        text-align:center;
        box-shadow:0 4px 20px rgba(0,0,0,0.2);">
        <h3>{icon} {title}</h3>
        <h1>{value}</h1>
    </div>
    """, unsafe_allow_html=True)



# -------------------------
# Session
# -------------------------
if "token" not in st.session_state:
    st.session_state.token = None

# -------------------------
# Login
# -------------------------
if not st.session_state.token:
    st.markdown('<p class="title">🎓 Student Analytics</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            r = requests.post(f"{API_URL}/login", data={"username": u, "password": p})
            if r.status_code == 200:
                st.session_state.token = r.json()["access_token"]
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# App
# -------------------------
else:
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # Top bar
    c1, c2, c3 = st.columns([7,1,1])
    with c1:
        st.markdown('<p class="title">📊 Dashboard</p>', unsafe_allow_html=True)
    with c2:
        if st.button("🌗 Toggle"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    with c3:
        if st.button("Logout"):
            st.session_state.token = None
            st.rerun()

    st.divider()

    tabs = st.tabs(["📊 Dashboard","➕ Add Student","📋 Students","🔮 Prediction","🤖 AI Assistant","📄 Report"])

    # ---------- Dashboard ----------
    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        students = requests.get(f"{API_URL}/students", headers=headers).json()
        perf = requests.get(f"{API_URL}/performance", headers=headers).json()
        avg = requests.get(f"{API_URL}/analytics/average-marks", headers=headers).json()

        c1, c2, c3 = st.columns(3)

        with c1:
            kpi_card("Students", len(students), "👥")

        with c2:
            kpi_card("Records", len(perf), "📊")

        with c3:
            kpi_card("Subjects", len(avg), "📚")
        st.markdown('</div>', unsafe_allow_html=True)

        if avg:
            df = pd.DataFrame(avg)
            fig = px.bar(df, x="subject", y="average_marks", title="Average Marks")
            st.plotly_chart(fig, use_container_width=True)

        if perf:
            df_perf = pd.DataFrame(perf)

            if "subject" in df_perf.columns:
                fig = px.pie(
                    df_perf,
                    names="subject",
                    title="📊 Subject Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)

        if perf:
            df_perf = pd.DataFrame(perf)

            if "marks" in df_perf.columns:
                fig = px.histogram(
                    df_perf,
                    x="marks",
                    nbins=10,
                    title="📈 Marks Distribution",
                    color_discrete_sequence=["#6366f1"]
                )
                st.plotly_chart(fig, use_container_width=True)

        if avg:
            df_avg = pd.DataFrame(avg)

            fig = px.bar(
                df_avg,
                x="subject",
                y="average_marks",
                color="subject",
                title="📊 Average Marks per Subject",
                template="plotly_dark"
            )

            st.plotly_chart(fig, use_container_width=True)

        top = requests.get(f"{API_URL}/analytics/top-students", headers=headers).json()

        if top:
            df_top = pd.DataFrame(top)

            if "name" in df_top.columns and "total_marks" in df_top.columns:
                fig = px.bar(
                    df_top,
                    x="name",
                    y="total_marks",
                    title="🏆 Top Students",
                    color="name"
                )
                st.plotly_chart(fig, use_container_width=True)


    # ---------- Add Student ----------
    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        a, b = st.columns(2)
        with a:
            name = st.text_input("Name")
            roll = st.text_input("Roll Number")
        with b:
            cls = st.text_input("Class")
            email = st.text_input("Email")
        if st.button("Add Student", use_container_width=True):
            r = requests.post(f"{API_URL}/students",
                              json={"name":name,"roll_number":roll,"class_name":cls,"email":email},
                              headers=headers)
            st.success("Added") if r.status_code==200 else st.error("Error")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Students ----------
    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        q = st.text_input("Search")
        if q:
            r = requests.get(f"{API_URL}/students/filter?name={q}", headers=headers)
        else:
            r = requests.get(f"{API_URL}/students", headers=headers)
        if r.status_code == 200:
            st.dataframe(r.json(), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Prediction ----------
    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        subs = requests.get(f"{API_URL}/meta/subjects", headers=headers).json()
        exams = requests.get(f"{API_URL}/meta/exam-types", headers=headers).json()
        c1, c2, c3 = st.columns(3)
        with c1:
            marks = st.number_input("Marks", 0, 100)
        with c2:
            subject = st.selectbox("Subject", subs)
        with c3:
            exam = st.selectbox("Exam Type", exams)
        if st.button("Predict", use_container_width=True):
            r = requests.post(f"{API_URL}/predict",
                              json={"marks":marks,"subject":subject,"exam_type":exam},
                              headers=headers)
            if r.status_code == 200:
                d = r.json()
                st.success(f"{d['prediction']} (p={d['probability']})")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- AI Assistant ----------
    with tabs[4]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🤖 AI Assistant")
        col1, col2 = st.columns([8,1])

        with col2:
            if st.button("🧹 Clear"):
                st.session_state.chat = []
                st.rerun()

        # Build context
        ctx = {
            "students": students if 'students' in locals() else requests.get(f"{API_URL}/students", headers=headers).json(),
            "avg_marks": avg if 'avg' in locals() else requests.get(f"{API_URL}/analytics/average-marks", headers=headers).json(),
            "top_students": requests.get(f"{API_URL}/analytics/top-students", headers=headers).json()
        }

        if "chat" not in st.session_state:
            st.session_state.chat = []

        # Chat display
        for role, msg in st.session_state.chat:
            if role == "You":
                st.chat_message("user").write(msg)
            else:
                st.chat_message("assistant").write(msg)

        # Chat input
        user_q = st.chat_input("Ask something about students...")

        if user_q:
            st.session_state.chat.append(("You", user_q))

            with st.spinner("Thinking..."):
                ans = ai_reply(user_q, ctx)

            st.session_state.chat.append(("AI", ans))
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- PDF Report ----------
    with tabs[5]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Generate PDF Report")

        # reuse data
        students = requests.get(f"{API_URL}/students", headers=headers).json()
        perf = requests.get(f"{API_URL}/performance", headers=headers).json()
        avg = requests.get(f"{API_URL}/analytics/average-marks", headers=headers).json()

        metrics = {"students": len(students), "records": len(perf)}

        if st.button("Generate Report", use_container_width=True):
            path = "report.pdf"
            build_pdf(path, metrics, students, avg)
            with open(path, "rb") as f:
                st.download_button("Download PDF", f, file_name="student_report.pdf")
        st.markdown('</div>', unsafe_allow_html=True)

