from langchain_openai import AzureOpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import CSVLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from dotenv import load_dotenv
import os
load_dotenv(override=True)

embeddings = AzureOpenAIEmbeddings(
    api_key=os.environ['OPENAI_API_AZURE_KEY'],
    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
    api_version=os.environ['OPENAI_API_VERSION'],
    model=os.environ['OPENAI_API_EMBEDDINGS_MODEL']
)

def search_data(question):
    abspath = os.path.dirname(os.path.abspath(__file__))
    # print(os.path.abspath(__file__)) # dapatin nama file
    # Connect to your Qdrant instance
    path_qdrant = os.path.join(abspath, "qdran_data_service")
    print(path_qdrant)
    qdrant = QdrantClient(path=path_qdrant)
    vector_store = QdrantVectorStore(
        client=qdrant,
        collection_name="service_data",
        embedding=embeddings,
    )
    print(qdrant)
    context = vector_store.similarity_search(question)
    print(context)
    return context

def search_data_product(question):

    # Connect to your Qdrant instance
    qdrant = QdrantClient(path=".\\qdran_data_product")
    vector_store = QdrantVectorStore(
        client=qdrant,
        collection_name="product_data",
        embedding=embeddings,
    )
    print(qdrant)
    context = vector_store.similarity_search(question)
    print(context)
    return context

def embed_data_service():

    # service_data_path = os.path.join("service_data", "kerusakan.csv")
    # print(service_data_path)
    abspath = os.path.dirname(os.path.abspath(__file__))
    # print(os.path.abspath(__file__)) # dapatin nama file
    # Connect to your Qdrant instance
    service_data_path = os.path.join(abspath, "service_data", "kerusakan.csv")
    print(service_data_path)
    qdrant_path = os.path.join(abspath, "qdran_data_service")
    # Load data dari file CSV
    loader = CSVLoader(file_path=service_data_path)
    data = loader.load()

    # Split data menjadi chunk
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=40)
    docs = text_splitter.split_documents(data)

    Qdrant.from_documents(
        docs,
        embeddings,
        path=qdrant_path,
        collection_name="service_data",
    )

    print("Berhasil Embed Service Data") 

def embed_data_product():

    service_data_path = os.path.join("product_data", "Produk.pdf")
    # Load data dari file CSV
    loader = PyPDFLoader(file_path=service_data_path)
    data = loader.load()

    # Split data menjadi chunk
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=40)
    docs = text_splitter.split_documents(data)

    Qdrant.from_documents(
        docs,
        embeddings,
        path="./qdran_data_product",
        collection_name="product_data",
    )

    print("Berhasil Embed Product Data") 

def fewshot_embed():
    fewshot = [
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

    Qdrant.from_documents(
        fewshot,
        embeddings,
        path="./qdrant_data_few_shots",
        collection_name="few_shots",
    )

    print("Few Shot Successfully Embed")