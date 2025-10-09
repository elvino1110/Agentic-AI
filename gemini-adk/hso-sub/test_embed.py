from .embed_data import QdrantEmbedGemini

planning_qdrant = QdrantEmbedGemini("planning_data")

# planning_qdrant.create_collection()
# planning_qdrant.embedding_data_plan()
result = planning_qdrant.search("berikan saya user untuk motor listrik")

# text = ""
# for res in result:
#     text += res.page_content
# print("============ RESULT ===========")
# print(result)
# print("============ TEXT ===========")
# print(text)
