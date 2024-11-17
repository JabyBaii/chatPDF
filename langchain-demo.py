# 使用langchain构建一个PDF阅读助手
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

# 加载PDF文件
def file_loader(file_path):
    from langchain_community.document_loaders import PyMuPDFLoader

    loader = PyMuPDFLoader(file_path)
    pages = loader.load_and_split()

    print("文件页数：", len(pages))
    print("打印第 1 页内容：\n", pages[0].page_content, '\n')

    return pages

# 文本分割
def text_splitter(pages):
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200, 
        chunk_overlap=20,
        length_function=len,
        add_start_index=True,
    )
    # 切割所有页数文档
    docs = text_splitter.split_documents(pages)
    print("打印文档数：", len(docs))
    for doc in docs:
        print(doc.page_content)
        print('-------')

    # # 切割指定页数文档
    # paragraphs = text_splitter.create_documents([pages[0].page_content])
    # print("打印文档数量：", len(paragraphs))
    # for para in paragraphs:
    #     print(para.page_content)
    #     print('-------')

    return docs

# 向量化
def create_vector_db(docs):
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS

    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    # 创建向量数据库并建立索引
    db = FAISS.from_documents(docs, embeddings)

    return db

# 创建检索器
def create_retriever(db):
    # 创建检索器
    ret = db.as_retriever(
        search_type="similarity", # 相似度检索
        search_kwargs={"k": 4}    # 返回4个结果
        )

    return ret

# 创建聊天机器人
def chatbot(user_input, doc_content):  
    from langchain.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        SystemMessagePromptTemplate,
    )
    from langchain_openai import ChatOpenAI

    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                "你是{product}的文档助手。你的名字叫{name},"
                " 请你根据{doc_content}的内容回答用户的问题。"),
            HumanMessagePromptTemplate.from_template("{query}"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4o-mini")  # 默认是gpt-3.5-turbo
    prompt = template.format_messages(
        product="学习帮",
        name="小A",
        query=user_input,
        doc_content=doc_content
    )

    print("调用LLM的prompt:", prompt)

    ret = llm.invoke(prompt)
    print("LLM的回答:", ret)

def main():
    pages = file_loader("./data/llama2_page1-5.pdf")
    docs = text_splitter(pages)
    
    user_input = "llama2有多少参数"

    print("正在创建向量数据库...")
    db = create_vector_db(docs)

    print("正在创建检索器...")
    retriever = create_retriever(db)

    print("正在检索向量数据库...")
    retriever_result = retriever.invoke(user_input)
    # 打印检索结果
    for doc in retriever_result:
        print("文档内容:", doc.page_content)
        print("元数据:", doc.metadata)
        print("---")

    # 将相似度最高的文档内容给chatbot
    doc_content = retriever_result[0].page_content
    print("相似度最高的文档内容:", doc_content)

    print("正在创建聊天机器人...")
    chatbot(user_input, doc_content)

if __name__ == "__main__":
    main()

