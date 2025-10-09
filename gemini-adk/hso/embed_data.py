from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http.models import Distance, VectorParams
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
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

    def embedding_data_plan(self):
        if self.vector_store is None:
            raise ValueError("Vector store belum siap. Jalankan create_collection() dulu!")

        data = """
            Plan:
            Step 1:  Buying Cycle 360 - Buying Cycle 360 Lookup ke CustomerProfileSales Dragon
            1.1 Filter customer yang isCustomerRO = True & Customer Consent = Setuju/Lain Kali
            1.2 Ambil data berdasarkan unit key customer 360 dengan detail berikut
            1.3 Ambil data pembelian sebelum last purchase: Lookup ke customer CustomerProfileSales berdasarkan no HP untuk mencari
            pembelian last purchase, gap pembelian serta age dan range age
            1.4 Hitung age, range age, gap pembelian
            1.5 Lookup ke data MIG berdasarkan No Hp untuk mencari segment macro & micro 
            
            Step 2: Buying Cycle cust Non RO - 360		Step 2: Buying Cycle cust Non RO -Customer Profile Sales
            2.1	Filter customer yang IsCustomerRO=False  & Customer Consent = Setuju / Lain Kali	Poin no 1,  filter data yang  ditemukan gap pembelian =0 
            2.2	Ambil data berdasarkan unik key customer 360 dengan detail berikut	Ambil data berdasarkan unik key customer 360 dengan detail berikut
            2.3	Hitung age, range age	 -
            2.4	Lookup ke data MIG berdasatkanNo HP?? untuk mencari segment macro & micro	Lookup ke data MIG berdasatkanNo HP?? untuk mencari segment macro & micro
            2.5	Lookup data ke hasil poin 1 berdasarkan tanda bold, jika menemukan lebih dari 1 maka ambil last transaction.	Lookup data ke hasil poin 1 berdasarkan tanda bold, jika menemukan lebih dari 1 maka ambil last transaction.
            2.6	Ambil data dari Poin 1. last unit & gap pembelian	Ambil data dari Poin 1. last unit & gap pembelian
            2.7	Ambil minimal 80% berdasarkan Last segment reference	Ambil minimal 80% berdasarkan Last segment reference

            Step 3 : Mengihitung Next Pembelian - 360		Step 3 : Mengihitung Next Pembelian - Customer Profile Sales
            3.1	Gabunga data hasil poin 1 & 2	 -
            3.2	Hitung Next Pembelian	 -

            Step 4 : Menentukan M, M+1, M+2 	Prioritisasi	Step 4 : Menentukan M, M+1, M+2 
            4.1	Ambil yang hanya M, M+1 & M+2 berdasarkan next pembelian	Ambil yang hanya M, M+1 & M+2 berdasarkan next pembelian

            Step 5:  Check Redundansi Lead		Step 5:  Check Redundansi Lead
            5.1	Ambil data last SPK: Region, Dealer, Salespeople, No Hp	Ambil data last SPK: Region, Dealer, Salespeople, No Hp
            5.2	Cek rules redundansi lead based on No HP	Cek rules redundansi lead based on No HP
        """
        document_1 = Document(page_content=data, metadata={"source": "plan"})
        documents = [document_1]
        uuids = [str(uuid4()) for _ in range(len(documents))]

        self.vector_store.add_documents(documents=documents, ids=uuids)
        print("Embed success")

    def search(self, query: str, k: int = 3):
        if self.vector_store is None:
            raise ValueError("Vector store belum siap. Jalankan create_collection() dulu!")

        results = self.vector_store.similarity_search(query, k=k)
        for res in results:
            print(f"* {res.page_content} [{res.metadata}]")
        return results
