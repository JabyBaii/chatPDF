import streamlit as st

from utils import show_original_pdf
from ai_interface import get_ai_response
from conf import container_height


def pdf_preview(uploaded_file):

    # 当用户上传文件后处理文件
    if uploaded_file is not None:
        if uploaded_file.size > 0:
            file_size = uploaded_file.size / (1024 * 1024)
            # if file_size > 10:
            #     st.warning(f"文件大小为 {file_size:.1f} MB，可能需要等待较长的时间或者无法显示。")
        
        st.session_state.pdf_file = uploaded_file
        # 读取上传的文件数据
        bytes_data = uploaded_file.read()
        # 显示PDF文件
        show_original_pdf(bytes_data, file_size)

def pdf_chat():
    # 初始化聊天历史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    # 创建聊天容器
    messages = st.container(height=container_height)
    # 显示聊天历史
    for message in st.session_state.chat_history:
        role, content = message.split(": ", 1)
        with messages.chat_message(role):
            st.markdown(content)

    # 聊天输入
    user_input = st.chat_input("Ask me anything about this pdf")
    if user_input:
        # 显示用户输入
        with messages.chat_message("user"):
            st.markdown(user_input)
        
        # 使用spinner显示加载动画
        with st.spinner("AI正在思考中..."):
            # 获取并显示AI响应
            response = get_ai_response(user_input)
            with messages.chat_message("assistant"):
                st.markdown(response)

        # 更新聊天历史
        st.session_state.chat_history.append(f"user: {user_input}")
        st.session_state.chat_history.append(f"assistant: {response}")

if __name__ == "__main__":
    # 设置页面配置
    st.set_page_config(layout="wide", initial_sidebar_state="expanded")
    uploaded_file = st.file_uploader("upload your pdf file here", type="pdf", label_visibility="collapsed",)
    # 创建三列布局
    _left, _right = st.columns([1, 1])

    with _left:
        pdf_preview(uploaded_file)
                
    with _right:
        pdf_chat()
