import chromadb
from chromadb.config import Settings

class MyVectorDBConnector:
    def __init__(self, collection_name, embedding_fn) -> None:
        # chroma_client = chromadb.Client(Settings(
        #     allow_reset=True,
        # ))
        # 不需要每次都reset
        # chroma_client.reset()

        chroma_client = chromadb.HttpClient(host='localhost', port=8000)
        
        self.collection = chroma_client.get_or_create_collection(
            name=collection_name)
        self.embedding_fn = embedding_fn
        self.documents = []

    def count_documents(self):
        return len(self.documents)

    def add_documents(self, documents):
        """向 collection 中添加文档与向量"""
        self.collection.add(
            embeddings=self.embedding_fn(documents),  # 每个文档的向量
            documents=documents,  # 文档的原文
            ids=[f"id{i}" for i in range(len(documents))]  # 每个文档的 id
        )
        # 更新 self.documents 列表
        self.documents.extend(documents)
        # 调试信息
        # print(f"添加的文档数: {len(documents)}")
        # print(f"当前文档总数: {len(self.documents)}")

    def search(self, query, top_k=5):
        """检索向量数据库"""
        results = self.collection.query(
            query_embeddings=self.embedding_fn([query]),
            n_results=top_k
        )
        return results

class MyClass:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}!"