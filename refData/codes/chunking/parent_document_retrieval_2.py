from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import DeterministicFakeEmbedding
from langchain_community.vectorstores import Chroma
from langchain_milvus import Milvus
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Packages I use:
# chromadb==0.4.24
# langchain==0.2.8
# pymilvus==2.4.4
# langchain-community==0.2.7
# langchain-milvus==0.1.2

document_id = "Employee-Handbook.pdf"
embedding = DeterministicFakeEmbedding(size=384)

def preprocess_file(file_path: str) -> list[Document]:
    """Load pdf file, chunk and build appropriate metadata"""
    loader = PyPDFLoader(file_path=file_path)
    pdf_docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
    )

    docs = text_splitter.split_documents(documents=pdf_docs)
    chunks_metadata = [
        {"document_id": file_path, "sequence_number": i} for i, _ in enumerate(docs)
    ]
    for chunk, metadata in zip(docs, chunks_metadata):
        chunk.metadata = metadata

    return docs


def get_milvus() -> Milvus:
    return Milvus(
        embedding_function=embedding,
        connection_args={"host": "127.0.0.1", "port": "19530"},
        auto_id=True,
    )


def get_chroma() -> Chroma:
    return Chroma(embedding_function=embedding)


def parent_document_retrieval(
    query: str, client: Milvus | Chroma, window_size: int = 4
):
    top_1 = client.similarity_search(query=query, k=1)[0]
    doc_id = top_1.metadata["document_id"]
    seq_num = top_1.metadata["sequence_number"]
    ids_window = [seq_num + i for i in range(-window_size, window_size, 1)]

    if isinstance(client, Milvus):
        expr = f"document_id LIKE '{doc_id}' && sequence_number in {ids_window}"
        res = client.col.query(
            expr=expr, output_fields=["sequence_number", "text"], limit=len(ids_window)
        )  # This is Milvus specific
        docs_to_return = [
            Document(
                page_content=d["text"],
                metadata={
                    "sequence_number": d["sequence_number"],
                    "document_id": doc_id,
                },
            )
            for d in res
        ]
    elif isinstance(client, Chroma):
        expr = {
            "$and": [
                {"document_id": {"$eq": doc_id}},
                {"sequence_number": {"$gte": ids_window[0]}},
                {"sequence_number": {"$lte": ids_window[-1]}},
            ]
        }
        res = client.get(where=expr)  # This is Chroma specific
        texts, metadatas = res["documents"], res["metadatas"]
        docs_to_return = [
            Document(
                page_content=t,
                metadata={
                    "sequence_number": m["sequence_number"],
                    "document_id": doc_id,
                },
            )
            for t, m in zip(texts, metadatas)
        ]
    else:
        raise TypeError("Currently we only support Milvus and Chroma.")

    docs_to_return.sort(key=lambda x: x.metadata["sequence_number"])
    return docs_to_return


def main():
    documents = preprocess_file(file_path=document_id)

    # Milvus example
    milvus = get_milvus()
    milvus.add_documents(documents=documents)
    docs = parent_document_retrieval(query="How are you?", client=milvus)
    print(docs)

    # Chroma example
    chroma = get_chroma()
    chroma.add_documents(documents=documents)
    docs = parent_document_retrieval(query="How are you?", client=chroma)
    print(docs)


if __name__ == "__main__":
    main()
