import streamlit as st
from services.ai_service import call_together_api
from services.db_service import save_message, load_chat_history

def render_schedule_assistant():
    """渲染行程規劃助手模式"""
    st.header("📅 行程規劃助手")
    st.write("請輸入您的行程資訊，我們會幫您整理成固定格式。")
    
    # 輸入框
    user_input = st.text_area(
        "輸入行程資訊",
        placeholder="例如：我今天早上要跟欣欣銀行開會、中午要與同事聚餐、下午要先去聿聿人壽完成駐點、然後要回到公司開會、最後完成 merge request 審核、最後晚上要去練跑",
        height=150
    )
    
    # 生成按鈕
    if st.button("生成行程", use_container_width=True):
        if user_input:
            with st.spinner("正在生成行程..."):
                response = call_together_api(user_input)
                st.session_state.schedule = response
                st.session_state.editable_schedule = response
        else:
            st.warning("請輸入行程資訊")
    
    # 顯示生成的行程
    if st.session_state.schedule:
        st.subheader("生成的行程")
        st.markdown(st.session_state.schedule)
        
        # 可編輯區域
        st.subheader("編輯行程")
        edited_schedule = st.text_area(
            "編輯行程",
            value=st.session_state.editable_schedule,
            height=300
        )
        if edited_schedule != st.session_state.editable_schedule:
            st.session_state.editable_schedule = edited_schedule

def render_ai_planner():
    """渲染 AI 幫你規劃模式"""
    st.header("🤖 AI 幫你規劃")
    st.write("請告訴我您的想法，我會透過對話幫您規劃行程。")
    
    # 顯示聊天歷史
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 聊天輸入框
    if prompt := st.chat_input("請輸入您的想法..."):
        # 顯示用戶輸入
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # 儲存用戶訊息
        save_message(st.session_state.current_session, "user", prompt)
        
        # 載入最近的聊天歷史
        recent_messages = load_chat_history(st.session_state.current_session)
        
        # 生成 AI 回應
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = call_together_api(prompt, mode="AI 幫你規劃", recent_messages=recent_messages)
                st.write(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                # 儲存 AI 回應
                save_message(st.session_state.current_session, "assistant", response)
                
                # 如果回應包含行程，更新可編輯區域
                if "**" in response and "-" in response:
                    st.session_state.schedule = response
                    st.session_state.editable_schedule = response 