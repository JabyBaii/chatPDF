import streamlit as st
import base64
import tempfile
import os
import time
import fitz  # PyMuPDF

from mybase import extract_text_from_pdf
from mybase import get_embeddings
from mybase import get_completion
from VectorDB import MyVectorDBConnector
from RAG_Bot import RAG_Bot


def pdf_viewer(file):
    """
    PDF文件浏览
    """
    # 将PDF文件转换为base64编码
    base64_pdf = base64.b64encode(file.getvalue()).decode('utf-8')

    # 使用PDF.js嵌入PDF查看器
    pdf_display = f'''
    <iframe 
        src="data:application/pdf;base64,{base64_pdf}" 
        width="100%" 
        height="800" 
        type="application/pdf">
    </iframe>
    '''

    # 使用st.markdown显示PDF
    st.markdown(pdf_display, unsafe_allow_html=True)

# 解决大文件无法预览的问题，转为图片
def pdf_to_images(uploaded_file):
    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # 打开PDF文件并将每一页转换为图像
    pdf_document = fitz.open(tmp_file_path)
    images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        # 创建分辨率是原始PDF页面2倍的图像，以提高清晰度
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img_path = f"./data/pdf_to_images/page_{page_num}.png"
        pix.save(img_path)
        images.append(img_path)

    # 删除临时PDF文件
    pdf_document.close()  # 确保PDF文件关闭
    time.sleep(1)  # 等待1秒
    try:
        os.unlink(tmp_file_path)
    except PermissionError:
        st.warning("无法删除临时文件，可能是因为文件正在被使用。")
    
    return images

def chat_interface(mypdf):
    """
    人机对话窗口功能后端实现
    """    
    # 加载PDF
    paragraphs = extract_text_from_pdf(
        mypdf, 
        [0, 1],             # 只提取前两页
        min_line_length=10  # 每段至少包含10个字符
    )

    # 存入向量数据库
    vector_db = MyVectorDBConnector("demo1", get_embeddings)
    vector_db.add_documents(paragraphs)
    # st.write("段落已添加到向量数据库")  # 添加调试信息

    # 验证向量数据库写入是否完成
    doc_count = vector_db.count_documents()

    if doc_count == len(paragraphs):
        # 正常面向用户的场景：
            # 1. 加载完成后，作为一个服务提供给用户使用；
            # 2. 对于新的PDF，加载完成后给于提示，然后才开启对话功能
        st.write("向量数据库写入完成")
    else:
        st.write("向量数据库写入失败")

    # 创建一个RAG机器人
    bot = RAG_Bot(
        vector_db,
        llm_api=get_completion
    )

    # 初始化聊天历史
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 接受用户输入
    if prompt := st.chat_input("请输入您的问题"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 调用后端功能获取回答
        response = bot.chat(prompt)

        # 显示 AI 回答
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})


def main():
    st.set_page_config(layout="wide")
    st.title("PDF 聊天机器人")

    # 文件上传
    uploaded_file = st.file_uploader("上传 PDF 文件", type="pdf")

    # 文件已上传触发
    if uploaded_file is not None:
        images = pdf_to_images(uploaded_file)

        # 初始化session_state中的page_number
        if 'page_number' not in st.session_state:
            st.session_state.page_number = 0

        num_pages = len(images)
        page_number = st.session_state.page_number
        
        # 创建两列布局
        col1, col2 = st.columns(2)

        with col1:
            # 创建左右布局
            left_col, right_col = st.columns([1, 1])  # 创建两个相等宽度的列

            if left_col.button("上一页"):
                if page_number > 0:
                    st.session_state.page_number -= 1

            if right_col.button("下一页"):
                if page_number < num_pages - 1:
                    st.session_state.page_number += 1

            # 显示页码
            st.write(f"当前页: {page_number + 1} / {num_pages}")

            # 显示当前页的图像
            st.image(images[page_number], use_column_width=True)

        with col2:
            st.subheader("聊天界面")
            chat_interface(uploaded_file)

if __name__ == "__main__":
    main()
