import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from config import Config

class VectorStore:
    def __init__(self):
        Config.validate()

        # Initialize embeddings based on configuration
        if Config.USE_LOCAL_MODEL:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=Config.OPENAI_API_KEY
            )

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_DB_PATH
        )

        # Initialize or get collection
        try:
            self.collection = self.client.get_collection(Config.COLLECTION_NAME)
        except:
            self.collection = self.client.create_collection(
                name=Config.COLLECTION_NAME,
                metadata={"description": "Document knowledge base collection"}
            )

        # Initialize LangChain Chroma wrapper
        self.vector_store = Chroma(
            client=self.client,
            collection_name=Config.COLLECTION_NAME,
            embedding_function=self.embeddings
        )

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store"""
        try:
            # Generate unique IDs for documents
            ids = [f"doc_{i}_{doc.metadata.get('source', 'unknown')}_{doc.metadata.get('chunk_id', 0)}"
                   for i, doc in enumerate(documents)]

            # Add documents to vector store
            self.vector_store.add_documents(documents, ids=ids)

            return ids
        except Exception as e:
            raise Exception(f"Error adding documents to vector store: {str(e)}")

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents"""
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            raise Exception(f"Error performing similarity search: {str(e)}")

    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Search for similar documents with similarity scores"""
        try:
            return self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            raise Exception(f"Error performing similarity search with scores: {str(e)}")

    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None):
        """Get a retriever for the vector store"""
        if search_kwargs is None:
            search_kwargs = {"k": 5}

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def delete_collection(self):
        """Delete the entire collection (useful for testing)"""
        try:
            self.client.delete_collection(Config.COLLECTION_NAME)
            print(f"Deleted collection: {Config.COLLECTION_NAME}")
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            collection = self.client.get_collection(Config.COLLECTION_NAME)
            count = collection.count()

            return {
                "document_count": count,
                "collection_name": Config.COLLECTION_NAME,
                "embedding_model": "OpenAI" if not Config.USE_LOCAL_MODEL else "HuggingFace",
                "database_path": Config.CHROMA_DB_PATH
            }
        except Exception as e:
            return {
                "error": f"Error getting collection stats: {str(e)}",
                "document_count": 0
            }

    def search_by_metadata(self, metadata_filter: Dict[str, Any], k: int = 5) -> List[Document]:
        """Search documents by metadata"""
        try:
            # Note: ChromaDB metadata filtering syntax may vary
            return self.vector_store.similarity_search("", k=k, filter=metadata_filter)
        except Exception as e:
            raise Exception(f"Error searching by metadata: {str(e)}")