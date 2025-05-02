import streamlit as st
from datetime import datetime, timedelta

# 初始化 Session State
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

st.title("📋 今日代辦任務安排面板")

st.subheader("➕ 新增一筆任務")
with st.form("task_form"):
    title = st.text_input("任務標題")
    priority = st.selectbox("優先順序", ["高", "中", "低"])
    start_time = st.time_input("開始時間", value=datetime.now().time())
    duration_minutes = st.number_input("所需時長（分鐘）", min_value=1, value=30)
    details = st.text_area("活動細節")
    submitted = st.form_submit_button("加入今日清單")

    if submitted:
        task = {
            "title": title,
            "priority": priority,
            "start_time": start_time.strftime('%H:%M'),
            "duration": duration_minutes,
            "details": details,
            "done": False,
        }
        st.session_state.tasks.append(task)
        st.success(f"✅ 任務「{title}」已加入！")

# 顯示任務列表
st.subheader("📌 今日任務清單（模組 A + B）")

if st.session_state.tasks:
    for i, task in enumerate(st.session_state.tasks):
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown(f"**{task['title']}** | ⏰ {task['start_time']} | 🕒 {task['duration']} 分鐘  ")
            st.markdown(f"_優先順序: {task['priority']} | {task['details']}_")
        with col2:
            task_done = st.checkbox("完成", key=f"done_{i}")
            st.session_state.tasks[i]['done'] = task_done
else:
    st.info("尚未新增任何任務")
