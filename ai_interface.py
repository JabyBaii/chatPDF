import streamlit as st

from mybase import extract_text_from_pdf, get_embeddings, get_completion
from VectorDB import MyVectorDBConnector
from RAG_Bot import RAG_Bot


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

def chat_interface(pdf_file, user_input):
    """
    聊天接口函数
    """
    # 检查PDF是否已处理
    if 'pdf_processed' not in st.session_state or not st.session_state.pdf_processed:
        # 从PDF提取文本，提取所有页码
        paragraphs = extract_text_from_pdf(pdf_file, [0, st.session_state.num_pages-1], min_line_length=10)
        

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