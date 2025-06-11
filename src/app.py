import streamlit as st
from services.db_service import init_db
from components.sidebar import render_sidebar
from components.main_ui import render_schedule_assistant, render_ai_planner

def main():
    """主應用程式"""
    # 初始化資料庫
    init_db()
    
    # 初始化 session state
    if "planning_mode" not in st.session_state:
        st.session_state.planning_mode = "行程規劃助手"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "schedule" not in st.session_state:
        st.session_state.schedule = ""
    if "editable_schedule" not in st.session_state:
        st.session_state.editable_schedule = ""
    
    # 渲染側邊欄
    render_sidebar()
    
    # 根據模式渲染主界面
    if st.session_state.planning_mode == "行程規劃助手":
        render_schedule_assistant()
    else:
        render_ai_planner()

if __name__ == "__main__":
    main() 