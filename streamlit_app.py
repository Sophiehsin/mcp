import streamlit as st
import requests
import datetime

webhook_url = 'https://hooks.zapier.com/hooks/catch/xxx/yyy'

task_list = ['讀書', '運動', '寫程式', '開會', '整理環境']

for task in task_list:
    if st.button(f'完成任務：{task}'):
        payload = {
            'task': task,
            'timestamp': datetime.datetime.now().isoformat()
        }
        requests.post(webhook_url, json=payload)
        st.success(f'{task} 完成 ✅')
