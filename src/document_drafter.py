"""
Document Drafting Module
AI-powered document generation based on learned styles and templates
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from rag_pipeline import RAGPipeline
from document_analyzer import DocumentStyleLearner
from config import Config

class DocumentDrafter:
    """AI-powered document drafting system"""

    def __init__(self, rag_pipeline: RAGPipeline):
        self.rag_pipeline = rag_pipeline
        self.style_learner = DocumentStyleLearner()
        self.document_templates = {}
        self.learned_styles = {}

        # Initialize LLM for drafting
        if Config.USE_LOCAL_MODEL:
            raise NotImplementedError(
                "Local LLM integration for document drafting not implemented. "
                "Set USE_LOCAL_MODEL=false and provide OPENAI_API_KEY"
            )
        else:
            from langchain.chat_models import ChatOpenAI
            self.llm = ChatOpenAI(
                openai_api_key=Config.OPENAI_API_KEY,
                model_name="gpt-4",  # Use GPT-4 for better document generation
                temperature=0.7  # Slightly higher temperature for creativity
            )

    def learn_styles_from_knowledge_base(self) -> Dict[str, Any]:
        """Learn document styles from all documents in the knowledge base"""
        # Get all documents from the vector store
        try:
            # Search with a broad query to get representative documents
            search_results = self.rag_pipeline.search_documents("*", k=50)

            if not search_results:
                return {
                    "success": False,
                    "message": "No documents found in knowledge base to learn from"
                }

            # Convert search results to Document objects
            documents = []
            for result in search_results:
                doc = Document(
                    page_content=result["content"],
                    metadata=result["metadata"]
                )
                documents.append(doc)

            # Learn styles
            learning_results = self.style_learner.learn_from_documents(documents)
            self.learned_styles = learning_results["style_templates"]

            return {
                "success": True,
                "message": f"Learned styles from {len(documents)} document chunks",
                "learned_styles": learning_results["summary"],
                "templates": list(self.learned_styles.keys())
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error learning styles: {str(e)}"
            }

    def create_drafting_prompt(self, document_type: str, request: str,
                              style_template: Optional[Dict[str, Any]] = None) -> str:
        """Create a specialized prompt for document drafting"""

        base_prompt = f"""You are an expert document writer specializing in {document_type} documents.
Your task is to draft a professional document based on the user's request and learned style patterns.

USER REQUEST:
{request}

"""

        if style_template:
            style_info = self._format_style_template(style_template)
            base_prompt += f"""
LEARNED STYLE GUIDELINES:
{style_info}

Please follow these style guidelines closely to match the established patterns from similar documents.
"""

        base_prompt += """
DRAFTING INSTRUCTIONS:
1. Create a complete, professional document that addresses the user's request
2. Follow the learned style patterns and formatting preferences
3. Use appropriate section headers and structure
4. Include placeholder text like [COMPANY NAME], [DATE], [NAME] where specific information is needed
5. Ensure the tone and complexity match the learned style
6. Include all necessary sections typical for this document type

Please draft the document now:"""

        return base_prompt

    def _format_style_template(self, template: Dict[str, Any]) -> str:
        """Format style template information for the prompt"""
        style_info = []

        # Document structure
        if "structure_template" in template:
            structure = template["structure_template"]
            style_info.append(f"STRUCTURE:")
            style_info.append(f"- Use approximately {structure.get('avg_header_count', 3):.0f} main sections")
            style_info.append(f"- Target paragraph length: {structure.get('avg_paragraph_length', 100):.0f} characters")

            if structure.get("uses_bullets", 0) > 0.5:
                style_info.append("- Include bullet points for lists")
            if structure.get("uses_numbering", 0) > 0.5:
                style_info.append("- Use numbered lists where appropriate")

        # Language style
        if "language_template" in template:
            language = template["language_template"]
            formality = language.get("avg_formality", 0)
            technical = language.get("avg_technical", 0)

            style_info.append(f"\nLANGUAGE STYLE:")
            if formality > 5:
                style_info.append("- Use formal, professional language")
            elif technical > 5:
                style_info.append("- Use technical, precise terminology")
            else:
                style_info.append("- Use clear, accessible language")

            avg_sentence = language.get("avg_sentence_length", 15)
            if avg_sentence > 20:
                style_info.append("- Use longer, complex sentences")
            else:
                style_info.append("- Use concise, clear sentences")

        # Common sections
        if "section_templates" in template:
            sections = template["section_templates"]
            if sections:
                style_info.append(f"\nCOMMON SECTIONS:")
                for section in sections[:5]:  # Top 5 most common
                    title = section.get("title_template", "").replace("[NAME]", "[PARTY NAME]").replace("[YEAR]", "[CURRENT YEAR]")
                    style_info.append(f"- {title}")

        # Formatting preferences
        if "formatting_template" in template:
            formatting = template["formatting_template"]
            style_info.append(f"\nFORMATTING:")

            if formatting.get("date_frequency", 0) > 0.5:
                style_info.append("- Include dates where relevant")
            if formatting.get("numbering_frequency", 0) > 0.5:
                style_info.append("- Use section numbering (1.1, 1.2, etc.)")
            if formatting.get("caps_frequency", 0) > 0.5:
                style_info.append("- Use ALL CAPS for emphasis on key terms")

        return "\n".join(style_info)

    def draft_document(self, request: str, document_type: Optional[str] = None,
                      use_knowledge_base: bool = True) -> Dict[str, Any]:
        """Draft a document based on user request and learned styles"""

        try:
            # Auto-detect document type if not specified
            if not document_type:
                document_type = self._detect_requested_document_type(request)

            # Get relevant context from knowledge base if requested
            context = ""
            if use_knowledge_base:
                context_result = self.rag_pipeline.query(
                    f"Find examples and information relevant to: {request}",
                    k=3
                )
                if context_result["success"]:
                    context = f"\nRELEVANT CONTEXT FROM KNOWLEDGE BASE:\n{context_result['answer']}\n"

            # Get learned style template
            style_template = self.learned_styles.get(document_type)

            # Create drafting prompt
            prompt_text = self.create_drafting_prompt(document_type, request, style_template)

            if context:
                prompt_text = prompt_text.replace("USER REQUEST:", f"USER REQUEST:\n{context}")

            # Generate document
            response = self.llm.predict(prompt_text)

            # Post-process the generated document
            processed_document = self._post_process_document(response, document_type)

            return {
                "success": True,
                "document": processed_document,
                "document_type": document_type,
                "style_template_used": style_template is not None,
                "knowledge_base_used": use_knowledge_base and bool(context),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "request": request,
                    "word_count": len(processed_document.split()),
                    "character_count": len(processed_document)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error drafting document: {str(e)}",
                "document": "",
                "document_type": document_type or "unknown"
            }

    def _detect_requested_document_type(self, request: str) -> str:
        """Detect what type of document is being requested"""
        request_lower = request.lower()

        # Legal documents
        if any(term in request_lower for term in ['contract', 'agreement', 'terms', 'legal', 'clause']):
            return "legal"

        # Business documents
        elif any(term in request_lower for term in ['proposal', 'letter', 'memo', 'business plan', 'executive summary']):
            return "business"

        # Technical documents
        elif any(term in request_lower for term in ['specification', 'manual', 'guide', 'documentation', 'requirements']):
            return "technical"

        # Default to the most common learned type or general
        if self.learned_styles:
            # Return the type with the most samples
            return max(self.learned_styles.keys(),
                      key=lambda k: self.learned_styles[k].get("sample_count", 0))

        return "general"

    def _post_process_document(self, document: str, document_type: str) -> str:
        """Post-process the generated document for consistency"""

        # Clean up extra whitespace
        document = re.sub(r'\n\s*\n\s*\n', '\n\n', document)
        document = document.strip()

        # Add standard placeholders if missing
        placeholders = {
            "[DATE]": f"[DATE: {datetime.now().strftime('%B %d, %Y')}]",
            "[CURRENT DATE]": f"[DATE: {datetime.now().strftime('%B %d, %Y')}]",
            "[TODAY]": f"[DATE: {datetime.now().strftime('%B %d, %Y')}]"
        }

        for placeholder, replacement in placeholders.items():
            if placeholder in document:
                document = document.replace(placeholder, replacement)

        # Ensure consistent formatting for different document types
        if document_type == "legal":
            document = self._format_legal_document(document)
        elif document_type == "business":
            document = self._format_business_document(document)

        return document

    def _format_legal_document(self, document: str) -> str:
        """Apply legal document formatting conventions"""

        # Ensure key legal terms are properly formatted
        legal_terms = [
            ("whereas", "WHEREAS"),
            ("therefore", "THEREFORE"),
            ("heretofore", "HERETOFORE"),
            ("party", "Party"),
            ("parties", "Parties")
        ]

        for old_term, new_term in legal_terms:
            # Only replace at word boundaries and at start of sentences
            pattern = r'\b' + re.escape(old_term) + r'\b'
            document = re.sub(pattern, new_term, document, flags=re.IGNORECASE)

        return document

    def _format_business_document(self, document: str) -> str:
        """Apply business document formatting conventions"""

        # Ensure proper business letter formatting if it's a letter
        if any(greeting in document.lower() for greeting in ['dear', 'to whom it may concern']):
            # Add signature block if missing
            if not any(closing in document.lower() for closing in ['sincerely', 'regards', 'best']):
                document += "\n\nSincerely,\n\n[YOUR NAME]\n[YOUR TITLE]\n[COMPANY]"

        return document

    def refine_document(self, document: str, refinement_request: str) -> Dict[str, Any]:
        """Refine an existing document based on user feedback"""

        try:
            refinement_prompt = f"""Please refine the following document based on the user's request:

USER'S REFINEMENT REQUEST:
{refinement_request}

CURRENT DOCUMENT:
{document}

Please provide the refined version of the document, incorporating the requested changes while maintaining the overall style and structure:"""

            refined_document = self.llm.predict(refinement_prompt)

            return {
                "success": True,
                "refined_document": refined_document,
                "refinement_applied": refinement_request,
                "metadata": {
                    "refined_at": datetime.now().isoformat(),
                    "original_length": len(document),
                    "refined_length": len(refined_document)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error refining document: {str(e)}",
                "refined_document": document
            }

    def suggest_improvements(self, document: str, document_type: str) -> List[str]:
        """Suggest improvements for a drafted document"""

        suggestions = []

        # Check for common issues
        word_count = len(document.split())

        if word_count < 100:
            suggestions.append("Consider expanding the document with more detail and supporting information")

        if "[" in document and "]" in document:
            placeholder_count = len(re.findall(r'\[([^\]]+)\]', document))
            suggestions.append(f"Replace {placeholder_count} placeholders with actual information")

        # Check for document-type specific improvements
        if document_type == "legal":
            if "whereas" not in document.lower():
                suggestions.append("Consider adding 'WHEREAS' clauses to establish context")
            if "therefore" not in document.lower():
                suggestions.append("Consider adding 'THEREFORE' clauses for conclusions")

        elif document_type == "business":
            if not any(greeting in document.lower() for greeting in ['dear', 'to whom']):
                suggestions.append("Consider adding a proper greeting")
            if not any(closing in document.lower() for closing in ['sincerely', 'regards']):
                suggestions.append("Consider adding a professional closing")

        # Check structure
        sections = len(re.findall(r'^[A-Z][A-Za-z\s]+:?\s*$', document, re.MULTILINE))
        if sections < 2:
            suggestions.append("Consider organizing content into clear sections with headers")

        return suggestions

    def get_available_templates(self) -> Dict[str, Any]:
        """Get information about available document templates"""

        if not self.learned_styles:
            return {
                "templates": {},
                "message": "No styles learned yet. Upload documents and run style learning first."
            }

        template_info = {}
        for doc_type, template in self.learned_styles.items():
            template_info[doc_type] = {
                "sample_count": template.get("sample_count", 0),
                "common_sections": len(template.get("section_templates", [])),
                "has_structure_template": "structure_template" in template,
                "has_language_template": "language_template" in template
            }

        return {
            "templates": template_info,
            "total_types": len(self.learned_styles),
            "most_samples": max(template_info.values(), key=lambda x: x["sample_count"]) if template_info else None
        }