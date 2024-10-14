import streamlit as st
import base64
import tempfile
import os
import time
import fitz  # PyMuPDF
from PIL import Image
import io
import logging
import streamlit.components.v1 as components
from datetime import datetime

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 导入自定义模块
from mybase import extract_text_from_pdf
from mybase import get_embeddings
from mybase import get_completion
from VectorDB import MyVectorDBConnector
from RAG_Bot import RAG_Bot

@st.cache_data
def load_page(_pdf_document, page_num, scale=2):
    """
    加载PDF页面并转换为图像
    
    :param _pdf_document: PDF文档对象
    :param page_num: 页码
    :param scale: 缩放比例
    :return: 页面图像
    """
    page = _pdf_document.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

def pdf_to_images(uploaded_file, num_pages_to_load=5):
    """
    将上传的PDF文件转换为图像
    
    :param uploaded_file: 上传的PDF文件
    :param num_pages_to_load: 要加载的页面数量
    :return: 加载的页面和总页数
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # 打开PDF文档
    pdf_document = fitz.open(tmp_file_path)
    total_pages = len(pdf_document)

    # 只加载指定数量的页面
    loaded_pages = {}
    for page_num in range(min(num_pages_to_load, total_pages)):
        loaded_pages[page_num] = load_page(pdf_document, page_num)

    # 关闭PDF文档并删除临时文件
    pdf_document.close()
    os.unlink(tmp_file_path)
    
    return loaded_pages, total_pages

# 添加一个新的会话状态变量来跟踪PDF是否已处理
if 'pdf_processed' not in st.session_state:
    st.session_state.pdf_processed = False

def chat_interface(pdf_file, user_input):
    """
    聊天接口函数
    """
    # 检查PDF是否已处理
    if 'pdf_processed' not in st.session_state or not st.session_state.pdf_processed:
        # 从PDF提取文本
        paragraphs = extract_text_from_pdf(pdf_file, [0, 1], min_line_length=10)

        # 使用自定义向量数据库
        vector_db = MyVectorDBConnector("demo1", get_embeddings)
        vector_db.add_documents(paragraphs)

        # 标记PDF已处理
        st.session_state.pdf_processed = True
    else:
        # 重新创建向量数据库连接
        vector_db = MyVectorDBConnector("demo1", get_embeddings)

    # 创建一个RAG机器人
    bot = RAG_Bot(vector_db, llm_api=get_completion)

    # 获取回答
    response = bot.chat(user_input)
    return response

def pdf_viewer():
    """
    PDF查看器函数
    """
    # 自定义CSS
    custom_css = """
    <style>
    .pdf-viewer {
        width: 100%;
        height: 800px;
        border: none;
    }
    </style>
    """
    # PDF.js代码
    pdf_js_code = """
    <script src="/static/pdfjs/build/pdf.js"></script>
    <script>
    // 使用fetch API获取PDF数据
    fetch('/get_pdf_data')
        .then(response => response.arrayBuffer())
        .then(arrayBuffer => {
            var loadingTask = pdfjsLib.getDocument({data: arrayBuffer});
            loadingTask.promise.then(function(pdf) {
                pdf.getPage(1).then(function(page) {
                    var scale = 1.5;
                    var viewport = page.getViewport({scale: scale});
                    var canvas = document.getElementById('pdf-canvas');
                    var context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    var renderContext = {
                        canvasContext: context,
                        viewport: viewport
                    };
                    page.render(renderContext);
                });
            });
        });
    </script>
    <canvas id="pdf-canvas" class="pdf-viewer"></canvas>
    """
    
    st.markdown(custom_css + pdf_js_code, unsafe_allow_html=True)

def get_pdf_data():
    """
    获取PDF数据
    """
    if 'pdf_file' in st.session_state:
        return st.session_state.pdf_file
    return None

@st.cache_resource
def load_css_and_js():
    """
    加载CSS和JavaScript
    """
    return """
    <style>
    /* CSS样式 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .main-container {
        display: flex;
        height: 100vh;
        width: 100vw;
    }
    .pdf-container {
        flex: 7;
        height: 100vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    .chat-container {
        flex: 3;
        height: 100vh;
        display: flex;
        flex-direction: column;
        background-color: white;
        border-left: 1px solid #ddd;
    }
    .chat-history {
        flex-grow: 1;
        overflow-y: auto;
        padding: 10px;
    }
    .chat-input {
        padding: 10px;
        border-top: 1px solid #ddd;
    }
    .stButton button {
        width: 100%;
    }
    </style>
    <script>
    // JavaScript函数
    function adjustLayout() {
        const appElement = document.querySelector('.stApp');
        if (appElement) {
            appElement.style.position = 'fixed';
            appElement.style.top = '0';
            appElement.style.left = '0';
            appElement.style.right = '0';
            appElement.style.bottom = '0';
            appElement.style.overflow = 'hidden';
            appElement.style.padding = '0';
            appElement.style.margin = '0';
        }
        const mainElement = document.querySelector('.main');
        if (mainElement) {
            mainElement.style.margin = '0';
            mainElement.style.padding = '0';
            mainElement.style.maxWidth = '100%';
            mainElement.style.overflow = 'hidden';
            const children = mainElement.children;
            for (let i = 0; i < children.length; i++) {
                children[i].style.margin = '0';
                children[i].style.padding = '0';
            }
        }
    }
    window.addEventListener('load', adjustLayout);
    setInterval(adjustLayout, 1000);
    </script>
    """

def main():
    """
    主函数
    """
    # 设置页面配置
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    
    # 加载CSS和JavaScript
    components.html(load_css_and_js(), height=0)

    # PDF显示区域
    st.markdown('<div class="pdf-container">', unsafe_allow_html=True)
    handle_pdf_upload()
    st.markdown('</div>', unsafe_allow_html=True)

    # AI聊天区域
    with st.sidebar:
        # 初始化聊天历史
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # 显示聊天历史
        messages = st.container(height=700)
        for message in st.session_state.chat_history:
            role, content = message.split(": ", 1)
            with messages.chat_message(role):
                st.markdown(content)

        # 聊天输入
        user_input = st.chat_input("请输入您的问题")
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


def handle_pdf_upload():
    """
    处理PDF上传
    """
    uploaded_file = st.file_uploader("上传PDF文件", type="pdf")
    if uploaded_file is not None:
        try:
            if 'pdf_file' not in st.session_state or st.session_state.pdf_file != uploaded_file:
                st.session_state.pdf_file = uploaded_file
                loaded_pages, total_pages = pdf_to_images(uploaded_file)
                st.session_state.loaded_pages = loaded_pages
                st.session_state.total_pages = total_pages
            
            for page_num, img in st.session_state.loaded_pages.items():
                st.image(img, caption=f"第 {page_num + 1} 页", use_column_width=True)

        except Exception as e:
            st.error(f"加载PDF时发生错误: {str(e)}")

def get_ai_response(user_input):
    if 'pdf_file' in st.session_state:
        try:
            # 获取AI响应
            response = chat_interface(st.session_state.pdf_file, user_input)
            return response
        except Exception as e:
            return f"处理问题时发生错误: {str(e)}"
    else:
        return "请先上传PDF文件"

if __name__ == "__main__":
    if "get_pdf_data" in st.query_params:
        pdf_data = get_pdf_data()
        if pdf_data:
            st.write(pdf_data.getvalue())
        else:
            st.error("No PDF data available")
    else:
        main()
