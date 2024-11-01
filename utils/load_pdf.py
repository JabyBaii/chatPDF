import streamlit as st  # 导入Streamlit库，用于创建Web应用界面
import os  # 导入os库，用于文件操作
import io  # 导入io库，用于处理二进制数据流
import base64  # 导入base64库，用于PDF文件的编码
from PIL import Image  # 导入PIL库中的Image模块，用于图像处理
from PyPDF2 import PdfReader, PdfWriter
from conf import container_height

def show_pdf(file_data):
    """
    显示PDF文件的函数
    参数:
        file_data: 可以是PDF文件的路径(字符串)或二进制数据
    """
    try:
        # 如果输入是文件路径，则读取文件内容
        if isinstance(file_data, str):
            with open(file_data, "rb") as f:
                file_data = f.read()

        # 将PDF文件数据转换为base64编码
        base64_pdf = base64.b64encode(file_data).decode('utf-8')

        # 创建HTML嵌入标签来显示PDF
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" \
        width="100%" height="{container_height}" type="application/pdf"></iframe>'

  
        # 使用Streamlit显示PDF
        st.markdown(pdf_display, unsafe_allow_html=True)
    
    except Exception as e:
        # 如果发生错误，显示错误信息
        st.error(f"发生错误: {str(e)}")

def show_original_pdf(file_data, file_size):
    try:
        # st.write("PDF 预览：")
        # 创建PDF阅读器
        pdf_reader = PdfReader(io.BytesIO(file_data))
        # 获取PDF的页数
        num_pages = len(pdf_reader.pages)
        st.session_state.num_pages = num_pages

         # 使用 session_state 来保存当前页码
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        # 创建一个新的 PDF 写入器，只包含选中的页面
        pdf_writer = PdfWriter()
        current_pages = st.session_state.current_page - 1
        pdf_writer.add_page(pdf_reader.pages[current_pages])

        # 将单页 PDF 转换为字节流
        output_bytes = io.BytesIO()
        pdf_writer.write(output_bytes)
        pdf_bytes = output_bytes.getvalue()

        # 将PDF字节数据转换为base64编码
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

        # 创建HTML嵌入标签来显示PDF
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" \
        width="100%" height="{container_height}" type="application/pdf"></iframe>' 
        
        # 使用Streamlit显示PDF
        st.markdown(pdf_display, unsafe_allow_html=True)

        # 创建三列布局
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col2:
            # 上一页按钮
            if st.button('← prev'):
                if st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                
        with col1:
            # 页码输入框
            page_input = st.number_input(
                f'input page',
                label_visibility='collapsed',  # 隐藏输入框的标签
                min_value=1, 
                max_value=num_pages, 
                value=st.session_state.current_page,
                key='page_input'
            )
            st.session_state.current_page = page_input
            
        with col3:
            # 下一页按钮
            if st.button('next →'):
                if st.session_state.current_page < num_pages:
                    st.session_state.current_page += 1
        with col4:
            # 显示文件信息
            st.write(f'{num_pages} pages, \ntotal {file_size:.1f} MB')

    except Exception as e:
        st.error(f"发生错误: {str(e)}")

# if __name__ == "__main__":
#     # 创建文件上传组件
#     uploaded_file = st.file_uploader("上传你的PDF文件", type="pdf")

#     # 当用户上传文件后处理文件
#     if uploaded_file is not None:
#         if uploaded_file.size > 0:
#             file_size = uploaded_file.size / (1024 * 1024)
#             if file_size > 10:
#                 st.warning(f"文件大小为 {file_size:.1f} MB，可能需要等待较长的时间或者无法显示。")

#         # 读取上传的文件数据
#         bytes_data = uploaded_file.read()
#         # 显示PDF文件
#         show_original_pdf(bytes_data)