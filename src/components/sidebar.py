import streamlit as st
from services.db_service import get_all_sessions, delete_session, create_session

def render_sidebar():
    """渲染側邊欄"""
    with st.sidebar:
        st.title("📝 行程規劃")
        
        # 帳號設定區塊
        st.subheader("👤 帳號設定")
        st.button("🔑 登入", use_container_width=True)
        
        # 規劃模式選擇
        st.subheader("⚙️ 規劃模式")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📅 行程規劃助手", use_container_width=True):
                st.session_state.planning_mode = "行程規劃助手"
                st.session_state.chat_history = []
        with col2:
            if st.button("🤖 AI 幫你規劃", use_container_width=True):
                st.session_state.planning_mode = "AI 幫你規劃"
                # 創建新的聊天會話
                st.session_state.current_session = create_session()
                st.session_state.chat_history = []
        
        # 聊天會話管理
        if st.session_state.planning_mode == "AI 幫你規劃":
            st.subheader("💬 聊天會話")
            sessions = get_all_sessions()
            for session_id, created_at, mode in sessions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(
                        f"📅 {created_at.strftime('%Y-%m-%d %H:%M')}",
                        key=f"session_{session_id}",
                        use_container_width=True
                    ):
                        st.session_state.current_session = session_id
                        st.session_state.chat_history = []
                with col2:
                    if st.button("🗑️", key=f"delete_{session_id}"):
                        delete_session(session_id)
                        st.rerun()
        
        # 系統狀態
        st.subheader("🔧 系統狀態")
        st.info("API 狀態: 正常")
        st.info("資料庫狀態: 正常")
        
        # 除錯資訊
        if st.checkbox("顯示除錯資訊"):
            st.write("Session State:", st.session_state) 