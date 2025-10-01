from typing import List, Dict, Any, Optional
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from vector_store import VectorStore
from config import Config

class RAGPipeline:
    def __init__(self):
        Config.validate()

        # Initialize vector store
        self.vector_store = VectorStore()

        # Initialize LLM based on configuration
        if Config.USE_LOCAL_MODEL:
            # For local models, you might use Ollama or other local LLM options
            # This is a placeholder - you'd need to implement local LLM integration
            raise NotImplementedError(
                "Local LLM integration not implemented. "
                "Set USE_LOCAL_MODEL=false and provide OPENAI_API_KEY"
            )
        else:
            self.llm = ChatOpenAI(
                openai_api_key=Config.OPENAI_API_KEY,
                model_name="gpt-3.5-turbo",
                temperature=0.1
            )

        # Custom prompt template for RAG
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful assistant that answers questions based on the provided context from documents.

Context from documents:
{context}

Question: {question}

Instructions:
1. Answer the question based only on the information provided in the context
2. If the context doesn't contain enough information to answer the question, say so
3. Include citations by mentioning the source document names when possible
4. Be concise but comprehensive in your answer

Answer:"""
        )

        # Initialize retrieval QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.get_retriever({"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt_template}
        )

    def add_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Add documents to the knowledge base"""
        try:
            document_ids = self.vector_store.add_documents(documents)

            return {
                "success": True,
                "message": f"Successfully added {len(documents)} document chunks",
                "document_ids": document_ids,
                "document_count": len(documents)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error adding documents: {str(e)}",
                "document_ids": [],
                "document_count": 0
            }

    def query(self, question: str, k: int = 5) -> Dict[str, Any]:
        """Query the knowledge base"""
        try:
            # Update retriever with specified k value
            self.qa_chain.retriever = self.vector_store.get_retriever({"k": k})

            # Run the QA chain
            result = self.qa_chain({"query": question})

            # Extract source information
            sources = []
            for doc in result.get("source_documents", []):
                source_info = {
                    "source": doc.metadata.get("source", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", 0),
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                sources.append(source_info)

            return {
                "success": True,
                "answer": result["result"],
                "sources": sources,
                "question": question,
                "retrieved_chunks": len(result.get("source_documents", []))
            }

        except Exception as e:
            return {
                "success": False,
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "question": question,
                "retrieved_chunks": 0
            }

    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents without generating an answer"""
        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)

            results = []
            for doc, score in docs_with_scores:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score),
                    "source": doc.metadata.get("source", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", 0)
                }
                results.append(result)

            return results

        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        return self.vector_store.get_collection_stats()

    def clear_knowledge_base(self):
        """Clear all documents from the knowledge base"""
        try:
            self.vector_store.delete_collection()
            # Reinitialize the vector store
            self.vector_store = VectorStore()
            self.qa_chain.retriever = self.vector_store.get_retriever({"k": 5})
            return {"success": True, "message": "Knowledge base cleared successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error clearing knowledge base: {str(e)}"}