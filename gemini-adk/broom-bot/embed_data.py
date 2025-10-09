from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import CSVLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from uuid import uuid4
import os


class QdrantEmbedGemini:
    def __init__(self, collection_name: str):
        load_dotenv()

        abspath = os.path.dirname(os.path.abspath(__file__))
        self.collection_name = collection_name
        qdrant_path = os.path.join(abspath, "vector-database", self.collection_name)
        self.qdrant = QdrantClient(path=qdrant_path)

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
        )

        # cek apakah collection sudah ada
        try:
            self.qdrant.get_collection(self.collection_name)
            # kalau ada, langsung buat vector_store
            self.vector_store = QdrantVectorStore(
                client=self.qdrant,
                collection_name=self.collection_name,
                embedding=self.embeddings
            )
            print(f"Collection '{self.collection_name}' ditemukan, vector_store siap.")
        except Exception:
            # kalau tidak ada, biarkan None
            self.vector_store = None
            print(f"Collection '{self.collection_name}' belum ada, silakan create_collection() dulu.")

    def create_collection(self):
        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )
        self.vector_store = QdrantVectorStore(
            client=self.qdrant,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )
        print("Create collection success")

    def embedding_data_service(self):
        if self.vector_store is None:
            raise ValueError("Vector store belum siap. Jalankan create_collection() dulu!")

        abspath = os.path.dirname(os.path.abspath(__file__))
        service_data_path = os.path.join(abspath, "service_data", "kerusakan.csv")
        loader = CSVLoader(file_path=service_data_path)
        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=40)
        docs = text_splitter.split_documents(data)
        uuids = [str(uuid4()) for _ in range(len(docs))]
        self.vector_store.add_documents(documents=docs, ids=uuids)
        print("Embed success")

    def embedding_data_product(self):
        if self.vector_store is None:
            raise ValueError("Vector store belum siap. Jalankan create_collection() dulu!")

        abspath = os.path.dirname(os.path.abspath(__file__))
        product_data_path = os.path.join(abspath, "product_data", "product.pdf")
        loader = PyPDFLoader(file_path=product_data_path)
        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=40)
        docs = text_splitter.split_documents(data)
        uuids = [str(uuid4()) for _ in range(len(docs))]
        self.vector_store.add_documents(documents=docs, ids=uuids)
        print("Embed success")

    def fewshot_embed(self):
        
        if self.vector_store is None:
            raise ValueError("Vector store belum siap. Jalankan create_collection() dulu!")

        docs = [
            Document(page_content="Request: Cari dealer di kecamatan Pancoran. \nSQL: SELECT * FROM Dealers WHERE district LIKE '%Pancoran%';"),
            Document(page_content="Request: Saya tinggal di Rengat. \nSQL: SELECT * FROM Dealers WHERE district LIKE '%Rengat%';"),
            Document(page_content="Request: Saya tinggal di Pekanbaru. Bisa tolong carikan dealer terdekat? \nSQL: SELECT * FROM Dealers WHERE city LIKE '%Pekanbaru%';"),
            Document(page_content="Request: Saya berada di provinsi Jawa Timur, ada dealer yang dekat? \nSQL: SELECT * FROM Dealers WHERE province LIKE '%Jawa Timur%';"),
            Document(page_content="Request: Saya tinggal di Kecamatan Sukaraja, Kabupaten Bogor. Apakah ada dealer di daerah ini? \nSQL: SELECT * FROM Dealers WHERE district LIKE '%Sukaraja%' AND city LIKE '%Bogor%';"),
            Document(page_content="Request: Saya berada di Kabupaten Sleman, Provinsi Yogyakarta. Ada dealer terdekat? \nSQL: SELECT * FROM Dealers WHERE city LIKE '%Sleman%' AND province LIKE '%Yogyakarta%';"),
            Document(page_content="Request: Saya tinggal di Kecamatan Margahayu, Kota Bandung, Provinsi Jawa Barat. Dimana dealer terdekat? \nSQL: SELECT * FROM Dealers WHERE district LIKE '%Margahayu%' AND city LIKE '%Bandung%' AND province LIKE '%Jawa Barat%';"),
            Document(page_content="Request: Saya tinggal di area Bogor. Ada dealer di sini? \nSQL: SELECT * FROM Dealers WHERE city LIKE '%Bogor%';"),
            Document(page_content="Request: Saya di kota Denpasar, apakah ada dealer yang menyediakan servis motor? \nSQL: SELECT * FROM Dealers WHERE city LIKE '%Denpasar%';")
        ]
        uuids = [str(uuid4()) for _ in range(len(docs))]
        self.vector_store.add_documents(documents=docs, ids=uuids)

        print("Few Shot Successfully Embed")

    def search(self, query: str, k: int = 3):
        if self.vector_store is None:
            raise ValueError("Vector store belum siap. Jalankan create_collection() dulu!")

        results = self.vector_store.similarity_search(query, k=k)
        for res in results:
            print(f"* {res.page_content} [{res.metadata}]")
        return results
