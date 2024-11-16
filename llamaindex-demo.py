import os

from dotenv import load_dotenv,find_dotenv

from utils.base import show_json
from utils.timer import Timer

_ = load_dotenv(find_dotenv())

# 文件加载
def file_load(file_path):
    from llama_index.core import SimpleDirectoryReader
    from llama_index.readers.file import PyMuPDFReader

    reader = SimpleDirectoryReader(
        input_dir=file_path,            # 目标目录
        recursive=False,                # 是否递归遍历子目录
        required_exts=[".pdf"],         # (可选)只读取指定后缀的文件
        file_extractor={".pdf": PyMuPDFReader()} # 指定特定的文件加载器
    )
    documents = reader.load_data()

    return documents

def print_documents(file_path):
    documents = file_load(file_path)
    # 打印第一页的metadata
    print(documents[0].metadata, "\n")
    # {'page_label': '1', 'file_name': 'llama2-back.pdf', 'file_path': 'D:\\IT_project\\DeepLearning\\chatPDF\\data\\llama2-back.pdf', 'file_type': 'application/pdf', 'file_size': 13661300, 'creation_date': '2024-10-12', 'last_modified_date': '2024-05-23'}
    # 打印第一页内容
    print(documents[0].text, "\n")
    # 打印第一页的json格式
    show_json(documents[0].json())

def feishu_load():
    from llama_index.readers.feishu_docs import FeishuDocsReader

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    # 文档ID列表
    doc_ids = [os.getenv("FEISHU_DOC_ID1")]

    # 定义飞书文档加载器
    loader = FeishuDocsReader(app_id, app_secret)

    # 加载文档
    documents = loader.load_data(document_ids=doc_ids)

    # 显示前1000字符
    print(documents[0].text[:1000])

    return documents

# 切分文档
def node_parser(documents, chunk_size=100, chunk_overlap=50):
    from llama_index.core.node_parser import TokenTextSplitter

    node_parser = TokenTextSplitter(
        chunk_size=chunk_size,      # 每个 chunk 的最大长度
        chunk_overlap=chunk_overlap # chunk 之间重叠长度 
    )

    nodes = node_parser.get_nodes_from_documents(
        documents, show_progress=False
    )

    return nodes

def print_nodes(documents):
    # documents = file_load(file_path)
    print("加载文档数量(页)：", len(documents))
    nodes = node_parser(documents)
    print("节点数量：", len(nodes), "\n")
    print("节点0开始字符索引：", nodes[0].start_char_idx, "节点0结束字符索引：", nodes[0].end_char_idx, "\n")
    print("节点1开始字符索引：", nodes[1].start_char_idx, "节点1结束字符索引：", nodes[1].end_char_idx, "\n")
    print("节点9开始字符索引：", nodes[9].start_char_idx, "节点9结束字符索引：", nodes[9].end_char_idx, "\n")
    print("节点10开始字符索引：", nodes[10].start_char_idx, "节点10结束字符索引：", nodes[10].end_char_idx, "\n")
    print("节点0文本：\n", nodes[0].text, "\n")
    print("节点0json：\n", nodes[0].json(), "\n")
    print("节点1文本：\n", nodes[1].text, "\n")
    print("节点1json：\n", nodes[1].json(), "\n")

# markdown格式文件的解析
def node_parser_markdown(file_path):
    from llama_index.readers.file import FlatReader
    from llama_index.core.node_parser import MarkdownNodeParser
    from pathlib import Path

    md_docs = FlatReader().load_data(Path(file_path))
    parser = MarkdownNodeParser()
    nodes = parser.get_nodes_from_documents(md_docs)
    
    return nodes

def print_nodes_markdown():
    nodes = node_parser_markdown("./data/ChatALL.md")
    print(nodes[0].text, "\n")
    print(nodes[0].json(), "\n")

# 构建 index（向量化）
def build_index(nodes, storage_context=None):
    from llama_index.core import VectorStoreIndex

    with Timer("构建索引"):
        index = VectorStoreIndex(nodes, storage_context=storage_context)

    return index

# 获取 retriever
def get_retriever(index, top_k):
    with Timer("获取 retriever"):
        vector_retriever = index.as_retriever(
            similarity_top_k=top_k # 返回2个结果
        )
    print(f"获取 retriever 成功，相似度top_k={top_k}")

    return vector_retriever

# 检索相似结果
def retrieve(vector_retriever, query):
    with Timer("检索结果"):
        results = vector_retriever.retrieve(query)
    print(f"检索结果成功，检索到 {len(results)} 个结果")

    return results

def qdrant_store():
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index.core import StorageContext

    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance

    # 创建 Qdrant 客户端
    client = QdrantClient(location=":memory:")
    # 创建集合
    collection_name = "demo"
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )
    # 创建向量存储
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
    # 指定存储空间
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    return storage_context, vector_store

def pipeline_cache(vector_store, documents, chunk_size=300, chunk_overlap=100):
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.core.extractors import TitleExtractor
    from llama_index.core.ingestion import IngestionPipeline, IngestionCache
    from llama_index.core import VectorStoreIndex

    # 检查vector store是否为空
    try:
        collection = vector_store.client.get_collection("demo")
        vector_count = collection.points_count  # 使用正确的方法获取向量数量
        print(f"Vector store中的向量数量: {vector_count}")
    except Exception as e:
        print(f"检查vector store失败: {e}")
        vector_count = 0

    if vector_count == 0 and not os.path.exists("./pipeline_storage"):
        print("Vector store为空且无缓存，需要完整处理文档")
        # 构建 pipeline 缓存
        pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
                TitleExtractor(),
                OpenAIEmbedding(),
            ],
            # # 使用本地embedding模型
            # transformations=[
            #     SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap), # 按句子切分
            #     # 跳过标题提取
            #     # 使用本地embedding模型
            #     HuggingFaceEmbedding(
            #         model_name="BAAI/bge-small-zh-v1.5",  # 中文embedding模型
            #         cache_folder="./model_cache"  # 本地缓存目录
            #     ),  
            # ],
            vector_store=vector_store,
        )
        # 运行pipeline处理文档
        with Timer("pipeline处理文档"):
            pipeline.run(documents=documents)
            print("文档处理完成，已生成向量嵌入")

        pipeline.persist("./pipeline_storage")
        print("pipeline缓存已保存至./pipeline_storage")

    elif vector_count == 0 and os.path.exists("./pipeline_storage"):
        print("Vector store为空但发现缓存，从缓存重建向量存储")
        # 虽然创建了完整pipeline，但由于使用缓存，不会实际调用OpenAI API
        pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
                TitleExtractor(),
                OpenAIEmbedding(),  # 需要定义，但不会实际调用
            ],
            vector_store=vector_store,
        )
        # 加载缓存后，pipeline会优先使用缓存中的向量
        pipeline.cache = IngestionCache.from_persist_path("./pipeline_storage/llama_cache")
        # 运行pipeline时会直接使用缓存的向量数据
        with Timer("从缓存重建向量存储"):
            pipeline.run(documents=documents)
            print("向量存储重建完成")

    try:
        # 验证向量是否成功存入
        new_count = vector_store.client.get_collection("demo").points_count
        print(f"处理后Vector store中的向量数量: {new_count}")
    except Exception as e:
        print(f"验证vector store失败: {e}")
    
    # 基于处理后的vector store创建索引
    with Timer("从vector store创建索引"):
        pipeline_index = VectorStoreIndex.from_vector_store(vector_store)

    return pipeline_index

# 检索后排序
def rerank(top_n):
    from llama_index.core.postprocessor import SentenceTransformerRerank

    # 检索后排序模型
    postprocessor = SentenceTransformerRerank(
        model="BAAI/bge-reranker-large", top_n=top_n
    )

    return postprocessor

def one_chat(index, query):
    print(f"\nuser: \n{query}")
    # 使用query engine查询
    query_engine = index.as_query_engine(streaming=True)
    print("bot: ")
    streaming_response = query_engine.query(query)
    streaming_response.print_response_stream()

def multi_chat(index):
    # 使用chat engine
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        system_prompt=(
            "你是一个文档助手，可以回答关于文档的问题"
            " 如果问题不在文档范围内，请回答：对不起，我无法回答这个问题"
        ),
        # 配置检索参数
        similarity_top_k=3,  # 检索top k个相似结果
        verbose=True,        # 显示详细信息
    )
    
    # 获取retriever用于显示检索结果
    retriever = index.as_retriever(similarity_top_k=3)

    while True:
        query = input("\nuser (输入'exit'退出): \n")
        if query == "exit":
            print("退出对话")
            break
        
        # 显示检索结果
        print("\n检索相关文档片段：")
        results = retriever.retrieve(query)
        for i, node in enumerate(results):
            print(f"\n相关片段 {i + 1}:")
            print(f"相似度得分: {node.score}")
            print(f"文本内容: {node.text[:200]}...")  # 只显示前200个字符

        print("bot: ")
        streaming_response = chat_engine.stream_chat(query)
        for token in streaming_response.response_gen:
            print(token, end="")
        print("\n")

def main():
    file_path = "./data"
    # 文件加载
    documents = file_load(file_path)
    print_documents(file_path)

    chunk_size = 300
    chunk_overlap = 100

    # 构建存储空间
    storage_context, vector_store = qdrant_store()
    
    # # 节点解析(切分文档)
    # nodes = node_parser(documents, chunk_size, chunk_overlap)
    # print_nodes(documents)
    # # 构建 index(向量化)
    # index = build_index(nodes, storage_context)

    # 使用pipeline处理文档(切分)和向量存储
    index = pipeline_cache(vector_store, documents, chunk_size, chunk_overlap)
        
    # # 获取 retriever top_n结果
    # top_n = 3
    # vector_retriever = get_retriever(index, top_n)
    # # 检索
    # query = "Llama2有多少参数"
    # results = retrieve(vector_retriever, query)
    # print(f"\n检索到 {len(results)} 个结果")

    # # 检索后排序    
    # postprocessor = rerank(top_n)
    # # 创建查询包
    # from llama_index.core import QueryBundle
    # query_bundle = QueryBundle(query)   
    # # 将查询和每个文档计算相似性
    # reranked_nodes = postprocessor.postprocess_nodes(results, query_bundle=query_bundle)
    
    # # 打印重排序后的结果
    # for i, node in enumerate(reranked_nodes):
    #     print(f"检索结果 {i}:\n", node, "\n")

    # 单轮对话
    # one_chat(index, "Llama2 有多少参数?")

    # 多轮对话
    multi_chat(index)

if __name__ == "__main__":
    main()

