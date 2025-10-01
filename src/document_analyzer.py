"""
Document Analysis Module
Analyzes documents to extract style, formatting patterns, and templates
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from langchain.schema import Document
import statistics

class DocumentStyleAnalyzer:
    """Analyzes document style and formatting patterns"""

    def __init__(self):
        self.style_patterns = {}
        self.document_templates = {}

    def analyze_document_structure(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure and style of a document"""

        analysis = {
            "document_type": self._detect_document_type(text, metadata),
            "structure": self._analyze_structure(text),
            "language_style": self._analyze_language_style(text),
            "formatting_patterns": self._analyze_formatting(text),
            "common_sections": self._extract_sections(text),
            "metadata": metadata
        }

        return analysis

    def _detect_document_type(self, text: str, metadata: Dict[str, Any]) -> str:
        """Detect the type of document based on content and metadata"""
        filename = metadata.get("source", "").lower()

        # Legal document patterns
        legal_indicators = [
            r'\b(agreement|contract|terms|whereas|party|parties)\b',
            r'\b(plaintiff|defendant|court|jurisdiction)\b',
            r'\b(shall|hereby|heretofore|notwithstanding)\b'
        ]

        # Business document patterns
        business_indicators = [
            r'\b(proposal|executive summary|recommendations)\b',
            r'\b(quarterly|annual|budget|revenue)\b',
            r'\b(dear|sincerely|regards)\b'
        ]

        # Technical document patterns
        technical_indicators = [
            r'\b(specification|requirements|implementation)\b',
            r'\b(algorithm|system|architecture)\b',
            r'\b(version|documentation|api)\b'
        ]

        # Count matches for each type
        legal_score = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in legal_indicators)
        business_score = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in business_indicators)
        technical_score = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in technical_indicators)

        # Determine type based on filename and content
        if any(term in filename for term in ['contract', 'agreement', 'legal']):
            return "legal"
        elif any(term in filename for term in ['proposal', 'business', 'letter']):
            return "business"
        elif any(term in filename for term in ['spec', 'technical', 'manual', 'guide']):
            return "technical"
        elif legal_score > business_score and legal_score > technical_score:
            return "legal"
        elif business_score > technical_score:
            return "business"
        elif technical_score > 0:
            return "technical"
        else:
            return "general"

    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure patterns"""
        lines = text.split('\n')

        # Count different line types
        headers = []
        bullet_points = []
        numbered_lists = []
        paragraphs = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Headers (short lines, often in caps or title case)
            if len(line) < 100 and (line.isupper() or line.istitle()) and not line.endswith('.'):
                headers.append(line)
            # Bullet points
            elif re.match(r'^[•\-\*]\s+', line):
                bullet_points.append(line)
            # Numbered lists
            elif re.match(r'^\d+[\.\)]\s+', line):
                numbered_lists.append(line)
            # Regular paragraphs
            elif len(line) > 20:
                paragraphs.append(line)

        return {
            "total_lines": len(lines),
            "header_count": len(headers),
            "bullet_point_count": len(bullet_points),
            "numbered_list_count": len(numbered_lists),
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": statistics.mean([len(p) for p in paragraphs]) if paragraphs else 0,
            "has_structured_lists": len(bullet_points) > 0 or len(numbered_lists) > 0
        }

    def _analyze_language_style(self, text: str) -> Dict[str, Any]:
        """Analyze language style and tone"""
        words = re.findall(r'\b\w+\b', text.lower())
        sentences = re.split(r'[.!?]+', text)

        # Formal language indicators
        formal_words = [
            'pursuant', 'heretofore', 'whereas', 'therefore', 'furthermore',
            'moreover', 'nevertheless', 'notwithstanding', 'accordingly'
        ]

        # Technical language indicators
        technical_words = [
            'implement', 'configure', 'execute', 'process', 'system',
            'framework', 'methodology', 'specification', 'parameter'
        ]

        # Casual language indicators
        casual_words = [
            'really', 'pretty', 'quite', 'basically', 'actually',
            'honestly', 'obviously', 'definitely'
        ]

        formal_count = sum(words.count(word) for word in formal_words)
        technical_count = sum(words.count(word) for word in technical_words)
        casual_count = sum(words.count(word) for word in casual_words)

        # Calculate averages
        avg_sentence_length = statistics.mean([len(s.split()) for s in sentences if s.strip()]) if sentences else 0
        avg_word_length = statistics.mean([len(word) for word in words]) if words else 0

        return {
            "formality_score": formal_count / len(words) * 1000 if words else 0,
            "technical_score": technical_count / len(words) * 1000 if words else 0,
            "casual_score": casual_count / len(words) * 1000 if words else 0,
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "total_words": len(words),
            "unique_words": len(set(words))
        }

    def _analyze_formatting(self, text: str) -> Dict[str, Any]:
        """Analyze formatting patterns in the document"""
        patterns = {
            "date_formats": re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+ \d{1,2},? \d{4}\b', text),
            "phone_numbers": re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text),
            "email_addresses": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
            "monetary_amounts": re.findall(r'\$[\d,]+\.?\d*', text),
            "percentages": re.findall(r'\b\d+\.?\d*%\b', text),
            "section_numbers": re.findall(r'\b\d+\.\d+(?:\.\d+)*\b', text),
            "all_caps_text": re.findall(r'\b[A-Z]{3,}\b', text),
            "parenthetical_refs": re.findall(r'\([^)]{1,50}\)', text)
        }

        return {
            "has_dates": len(patterns["date_formats"]) > 0,
            "has_contact_info": len(patterns["phone_numbers"]) > 0 or len(patterns["email_addresses"]) > 0,
            "has_financial_data": len(patterns["monetary_amounts"]) > 0 or len(patterns["percentages"]) > 0,
            "has_section_numbering": len(patterns["section_numbers"]) > 0,
            "uses_caps_emphasis": len(patterns["all_caps_text"]) > 0,
            "formatting_complexity": sum(len(v) for v in patterns.values())
        }

    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract common section patterns from the document"""
        lines = text.split('\n')
        sections = []
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Potential section headers (short, title case, or numbered)
            is_header = (
                len(line) < 100 and
                (line.isupper() or line.istitle() or re.match(r'^\d+\.', line)) and
                not line.endswith('.')
            )

            if is_header:
                if current_section:
                    sections.append(current_section)

                current_section = {
                    "title": line,
                    "content": [],
                    "type": "section"
                }
            elif current_section:
                current_section["content"].append(line)

        # Add the last section
        if current_section:
            sections.append(current_section)

        return sections

class DocumentTemplateExtractor:
    """Extracts reusable templates from analyzed documents"""

    def __init__(self):
        self.templates = {}

    def extract_template(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a reusable template from document analysis"""
        doc_type = analysis["document_type"]

        template = {
            "type": doc_type,
            "structure_pattern": self._create_structure_pattern(analysis),
            "style_guide": self._create_style_guide(analysis),
            "common_sections": self._extract_section_templates(analysis["common_sections"]),
            "formatting_rules": self._extract_formatting_rules(analysis["formatting_patterns"]),
            "language_characteristics": analysis["language_style"]
        }

        return template

    def _create_structure_pattern(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structure pattern from analysis"""
        structure = analysis["structure"]

        return {
            "recommended_sections": max(3, structure["header_count"]),
            "use_bullet_points": structure["bullet_point_count"] > 0,
            "use_numbered_lists": structure["numbered_list_count"] > 0,
            "target_paragraph_length": max(50, structure["avg_paragraph_length"]),
            "structured_format": structure["has_structured_lists"]
        }

    def _create_style_guide(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a style guide from language analysis"""
        style = analysis["language_style"]

        # Determine dominant style
        if style["formality_score"] > style["casual_score"]:
            tone = "formal"
        elif style["technical_score"] > 5:
            tone = "technical"
        else:
            tone = "conversational"

        return {
            "tone": tone,
            "avg_sentence_length": style["avg_sentence_length"],
            "complexity_level": "high" if style["avg_word_length"] > 5 else "medium",
            "vocabulary_richness": style["unique_words"] / style["total_words"] if style["total_words"] > 0 else 0
        }

    def _extract_section_templates(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract common section templates"""
        templates = []

        for section in sections:
            template = {
                "title_pattern": self._generalize_title(section["title"]),
                "content_structure": self._analyze_content_structure(section["content"]),
                "estimated_length": len(' '.join(section["content"]))
            }
            templates.append(template)

        return templates

    def _generalize_title(self, title: str) -> str:
        """Generalize section titles for template use"""
        # Replace specific names/dates with placeholders
        generalized = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', title)
        generalized = re.sub(r'\b\d{4}\b', '[YEAR]', generalized)
        generalized = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]', generalized)

        return generalized

    def _analyze_content_structure(self, content: List[str]) -> Dict[str, Any]:
        """Analyze the structure of section content"""
        if not content:
            return {"type": "empty"}

        # Check for lists
        bullet_lines = sum(1 for line in content if re.match(r'^[•\-\*]\s+', line))
        numbered_lines = sum(1 for line in content if re.match(r'^\d+[\.\)]\s+', line))

        if bullet_lines > len(content) * 0.5:
            return {"type": "bullet_list", "items": bullet_lines}
        elif numbered_lines > len(content) * 0.5:
            return {"type": "numbered_list", "items": numbered_lines}
        else:
            return {"type": "paragraph", "paragraph_count": len(content)}

    def _extract_formatting_rules(self, formatting: Dict[str, Any]) -> Dict[str, Any]:
        """Extract formatting rules for template"""
        return {
            "include_dates": formatting["has_dates"],
            "include_contact_info": formatting["has_contact_info"],
            "include_financial_data": formatting["has_financial_data"],
            "use_section_numbering": formatting["has_section_numbering"],
            "use_caps_emphasis": formatting["uses_caps_emphasis"]
        }

class DocumentStyleLearner:
    """Learns document styles from multiple examples"""

    def __init__(self):
        self.analyzer = DocumentStyleAnalyzer()
        self.template_extractor = DocumentTemplateExtractor()
        self.learned_styles = defaultdict(list)

    def learn_from_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Learn styles from a collection of documents"""
        analyses = []

        for doc in documents:
            analysis = self.analyzer.analyze_document_structure(
                doc.page_content,
                doc.metadata
            )
            analyses.append(analysis)

            # Group by document type
            doc_type = analysis["document_type"]
            self.learned_styles[doc_type].append(analysis)

        # Create consolidated templates for each document type
        templates = {}
        for doc_type, type_analyses in self.learned_styles.items():
            templates[doc_type] = self._consolidate_style(type_analyses)

        return {
            "document_analyses": analyses,
            "style_templates": templates,
            "summary": self._create_learning_summary(analyses)
        }

    def _consolidate_style(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate multiple analyses into a single style template"""
        if not analyses:
            return {}

        # Average numerical values
        avg_structure = self._average_structure_metrics(analyses)
        avg_language = self._average_language_metrics(analyses)

        # Find most common patterns
        common_sections = self._find_common_section_patterns(analyses)
        formatting_preferences = self._consolidate_formatting_preferences(analyses)

        return {
            "document_type": analyses[0]["document_type"],
            "structure_template": avg_structure,
            "language_template": avg_language,
            "section_templates": common_sections,
            "formatting_template": formatting_preferences,
            "sample_count": len(analyses)
        }

    def _average_structure_metrics(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Average structure metrics across analyses"""
        structures = [a["structure"] for a in analyses]

        return {
            "avg_header_count": statistics.mean([s["header_count"] for s in structures]),
            "avg_paragraph_length": statistics.mean([s["avg_paragraph_length"] for s in structures]),
            "uses_bullets": sum(s["bullet_point_count"] > 0 for s in structures) / len(structures),
            "uses_numbering": sum(s["numbered_list_count"] > 0 for s in structures) / len(structures)
        }

    def _average_language_metrics(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Average language metrics across analyses"""
        styles = [a["language_style"] for a in analyses]

        return {
            "avg_formality": statistics.mean([s["formality_score"] for s in styles]),
            "avg_technical": statistics.mean([s["technical_score"] for s in styles]),
            "avg_sentence_length": statistics.mean([s["avg_sentence_length"] for s in styles]),
            "avg_word_length": statistics.mean([s["avg_word_length"] for s in styles])
        }

    def _find_common_section_patterns(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find common section patterns across documents"""
        all_sections = []
        for analysis in analyses:
            all_sections.extend(analysis["common_sections"])

        # Group similar section titles
        title_groups = defaultdict(list)
        for section in all_sections:
            generalized_title = self.template_extractor._generalize_title(section["title"])
            title_groups[generalized_title].append(section)

        # Return common patterns (appearing in multiple documents)
        common_patterns = []
        for title, sections in title_groups.items():
            if len(sections) >= 2:  # Appears in at least 2 documents
                pattern = {
                    "title_template": title,
                    "frequency": len(sections),
                    "avg_content_length": statistics.mean([len(' '.join(s["content"])) for s in sections])
                }
                common_patterns.append(pattern)

        return sorted(common_patterns, key=lambda x: x["frequency"], reverse=True)

    def _consolidate_formatting_preferences(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate formatting preferences across documents"""
        formatting_data = [a["formatting_patterns"] for a in analyses]

        return {
            "date_frequency": sum(f["has_dates"] for f in formatting_data) / len(formatting_data),
            "contact_frequency": sum(f["has_contact_info"] for f in formatting_data) / len(formatting_data),
            "financial_frequency": sum(f["has_financial_data"] for f in formatting_data) / len(formatting_data),
            "numbering_frequency": sum(f["has_section_numbering"] for f in formatting_data) / len(formatting_data),
            "caps_frequency": sum(f["uses_caps_emphasis"] for f in formatting_data) / len(formatting_data)
        }

    def _create_learning_summary(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of what was learned"""
        doc_types = Counter(a["document_type"] for a in analyses)

        return {
            "total_documents": len(analyses),
            "document_types": dict(doc_types),
            "most_common_type": doc_types.most_common(1)[0] if doc_types else None,
            "avg_complexity": statistics.mean([
                a["language_style"]["avg_word_length"] for a in analyses
            ]) if analyses else 0
        }

    def get_style_template(self, document_type: str) -> Optional[Dict[str, Any]]:
        """Get the learned style template for a specific document type"""
        return self.learned_styles.get(document_type)