"""
Document Generation Pipeline for the Corporate Law Document Generator.

Each document type is defined as a dict with:
  label, description, fields (list of form field defs), system_prompt.

The pipeline:
  1. Retrieve style examples from ChromaDB (where document_type = type)
  2. Optionally fetch reference data from SEC EDGAR / NetDocuments
  3. Build system + user prompts
  4. Call LLMBackend.generate_document()
  5. Convert result to .docx bytes
"""

import io
import re
from datetime import date

from docx import Document as DocxDocument
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from llm_backend import LLMBackend


# ======================================================================
# Document type definitions
# ======================================================================

DOCUMENT_TYPES: dict[str, dict] = {
    "contract": {
        "label": "Contract / Agreement",
        "description": "Generate a contract or agreement between parties.",
        "fields": [
            {"key": "party_a", "label": "Party A (Full Legal Name)", "type": "text"},
            {"key": "party_b", "label": "Party B (Full Legal Name)", "type": "text"},
            {"key": "effective_date", "label": "Effective Date", "type": "date"},
            {"key": "term", "label": "Term / Duration", "type": "text",
             "placeholder": "e.g. 12 months, perpetual"},
            {"key": "subject_matter", "label": "Subject Matter", "type": "textarea",
             "placeholder": "Describe the purpose and scope of the agreement"},
            {"key": "key_terms", "label": "Key Terms & Conditions", "type": "textarea",
             "placeholder": "Payment terms, deliverables, obligations, etc."},
            {"key": "governing_law", "label": "Governing Law (State/Jurisdiction)", "type": "text",
             "placeholder": "e.g. State of Delaware"},
            {"key": "special_provisions", "label": "Special Provisions (optional)", "type": "textarea"},
        ],
        "system_prompt": (
            "You are a corporate law document drafting assistant. "
            "Generate a professional, well-structured contract/agreement. "
            "Use formal legal language with numbered sections and sub-sections. "
            "Include standard boilerplate clauses (entire agreement, severability, "
            "notices, counterparts) unless the user specifies otherwise. "
            "Do NOT provide legal advice — this is a draft for attorney review."
        ),
    },
    "memo": {
        "label": "Legal Memorandum",
        "description": "Generate an internal legal memorandum.",
        "fields": [
            {"key": "to", "label": "To", "type": "text"},
            {"key": "from_field", "label": "From", "type": "text"},
            {"key": "date_field", "label": "Date", "type": "date"},
            {"key": "re", "label": "Re (Subject)", "type": "text"},
            {"key": "questions_presented", "label": "Questions Presented", "type": "textarea",
             "placeholder": "List the legal questions to be addressed"},
            {"key": "facts", "label": "Relevant Facts", "type": "textarea"},
            {"key": "jurisdiction", "label": "Jurisdiction", "type": "text",
             "placeholder": "e.g. Federal, State of New York"},
        ],
        "system_prompt": (
            "You are a corporate law document drafting assistant. "
            "Generate a professional internal legal memorandum. "
            "Follow the standard memo format: Header block (TO/FROM/DATE/RE), "
            "Questions Presented, Brief Answer, Discussion, Conclusion. "
            "Cite relevant legal principles where appropriate. "
            "Do NOT provide legal advice — this is a draft for attorney review."
        ),
    },
    "brief": {
        "label": "Legal Brief",
        "description": "Generate a legal brief or motion.",
        "fields": [
            {"key": "court", "label": "Court", "type": "text",
             "placeholder": "e.g. United States District Court, Southern District of New York"},
            {"key": "case_caption", "label": "Case Caption", "type": "text",
             "placeholder": "e.g. Smith v. Jones Corp."},
            {"key": "case_number", "label": "Case Number", "type": "text"},
            {"key": "brief_type", "label": "Brief Type", "type": "text",
             "placeholder": "e.g. Motion to Dismiss, Summary Judgment, Opposition"},
            {"key": "argument_summary", "label": "Argument Summary", "type": "textarea",
             "placeholder": "Summarize the key arguments to be made"},
            {"key": "facts", "label": "Statement of Facts", "type": "textarea"},
            {"key": "legal_standard", "label": "Legal Standard", "type": "textarea",
             "placeholder": "Applicable legal standard or rule"},
        ],
        "system_prompt": (
            "You are a corporate law document drafting assistant. "
            "Generate a professional legal brief or motion. "
            "Follow standard brief format: Caption, Introduction, Statement of Facts, "
            "Argument (with numbered points and sub-points), Conclusion, Signature Block. "
            "Use formal legal writing style with proper citations (Bluebook format). "
            "Do NOT provide legal advice — this is a draft for attorney review."
        ),
    },
    "filing": {
        "label": "Corporate Filing",
        "description": "Generate a corporate filing document (articles, annual report, etc.).",
        "fields": [
            {"key": "filing_type", "label": "Filing Type", "type": "text",
             "placeholder": "e.g. Articles of Incorporation, Annual Report, Certificate of Amendment"},
            {"key": "entity_name", "label": "Entity Name", "type": "text"},
            {"key": "state", "label": "State of Formation / Filing", "type": "text"},
            {"key": "details", "label": "Filing Details", "type": "textarea",
             "placeholder": "Purpose, authorized shares, registered agent, amendments, etc."},
            {"key": "sec_cik", "label": "SEC CIK (optional, for reference data)", "type": "text",
             "placeholder": "10-digit CIK number for SEC EDGAR lookup"},
        ],
        "system_prompt": (
            "You are a corporate law document drafting assistant. "
            "Generate a professional corporate filing document. "
            "Use the correct format for the specified filing type and jurisdiction. "
            "Include all required statutory sections and language. "
            "Do NOT provide legal advice — this is a draft for attorney review."
        ),
    },
}


# ======================================================================
# Generator
# ======================================================================


class DocumentGenerator:
    """End-to-end generation pipeline: examples -> ref data -> prompt -> LLM -> text."""

    def __init__(self, llm: LLMBackend, chroma_collection=None):
        self.llm = llm
        self.collection = chroma_collection

    # -- Style examples from ChromaDB ------------------------------------

    def get_style_examples(
        self, document_type: str, n_examples: int = 3
    ) -> list[str]:
        """Retrieve example chunks from ChromaDB filtered by document_type."""
        if self.collection is None or self.collection.count() == 0:
            return []
        try:
            results = self.collection.query(
                query_texts=[f"{document_type} document example"],
                n_results=min(n_examples, self.collection.count()),
                where={"document_type": document_type},
            )
            return results["documents"][0] if results["documents"] else []
        except Exception:
            # If where-filter fails (no matching docs), fall back to empty
            return []

    # -- Reference data --------------------------------------------------

    def fetch_reference_data(
        self,
        document_type: str,
        params: dict,
        sec_client=None,
        netdocs_client=None,
    ) -> str:
        """Optionally pull reference data from SEC EDGAR or NetDocuments."""
        parts: list[str] = []

        # SEC EDGAR — useful for filings & contracts mentioning public companies
        if sec_client and sec_client.is_configured():
            try:
                cik = params.get("sec_cik", "").strip()
                if cik:
                    filings = sec_client.get_company_filings(cik)
                    name = filings.get("name", "")
                    recent = filings.get("filings", {}).get("recent", {})
                    forms = recent.get("form", [])[:5]
                    dates = recent.get("filingDate", [])[:5]
                    lines = [f"Company: {name}"]
                    for f, d in zip(forms, dates):
                        lines.append(f"  - {f} filed {d}")
                    parts.append(
                        "SEC EDGAR reference data:\n" + "\n".join(lines)
                    )
                else:
                    # Try a keyword search based on entity name
                    entity = params.get("entity_name", "") or params.get("party_a", "")
                    if entity:
                        hits = sec_client.search_filings(entity, max_results=3)
                        if hits:
                            lines = [
                                f"  - {h['entity_name']}: {h['form_type']} ({h['file_date']})"
                                for h in hits
                            ]
                            parts.append(
                                "SEC EDGAR search results:\n" + "\n".join(lines)
                            )
            except Exception as e:
                parts.append(f"(SEC EDGAR lookup failed: {e})")

        # NetDocuments — pull related docs
        if (
            netdocs_client
            and netdocs_client.is_configured()
            and netdocs_client.is_authenticated()
        ):
            try:
                query = params.get("subject_matter", "") or params.get("re", "") or document_type
                docs = netdocs_client.search_documents(query, max_results=3)
                if docs:
                    lines = [f"  - {d.get('name', 'Untitled')}" for d in docs]
                    parts.append(
                        "Related NetDocuments:\n" + "\n".join(lines)
                    )
            except Exception as e:
                parts.append(f"(NetDocuments lookup failed: {e})")

        return "\n\n".join(parts)

    # -- Prompt construction ---------------------------------------------

    def build_prompt(
        self,
        document_type: str,
        params: dict,
        style_examples: list[str],
        reference_data: str,
    ) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) for the LLM."""
        doc_def = DOCUMENT_TYPES[document_type]
        system_prompt = doc_def["system_prompt"]

        # -- Build user prompt -------------------------------------------
        sections: list[str] = []

        # Style examples
        if style_examples:
            examples_text = "\n---\n".join(style_examples[:3])
            sections.append(
                "STYLE REFERENCE — follow the tone, structure, and formatting "
                "of these example excerpts:\n\n" + examples_text
            )

        # Reference data
        if reference_data:
            sections.append("REFERENCE DATA:\n" + reference_data)

        # User parameters
        param_lines: list[str] = []
        for field in doc_def["fields"]:
            key = field["key"]
            value = params.get(key, "")
            if value:
                # Format dates nicely
                if hasattr(value, "strftime"):
                    value = value.strftime("%B %d, %Y")
                param_lines.append(f"{field['label']}: {value}")

        sections.append(
            f"Generate a {doc_def['label']} with the following parameters:\n\n"
            + "\n".join(param_lines)
        )

        user_prompt = "\n\n".join(sections)
        return system_prompt, user_prompt

    # -- Full pipeline ---------------------------------------------------

    def generate(
        self,
        document_type: str,
        params: dict,
        sec_client=None,
        netdocs_client=None,
        use_sec: bool = False,
        use_netdocs: bool = False,
    ) -> str:
        """Run the full generation pipeline and return the document text."""
        # 1. Style examples
        style_examples = self.get_style_examples(document_type)

        # 2. Reference data
        reference_data = ""
        if use_sec or use_netdocs:
            reference_data = self.fetch_reference_data(
                document_type,
                params,
                sec_client=sec_client if use_sec else None,
                netdocs_client=netdocs_client if use_netdocs else None,
            )

        # 3. Build prompt
        system_prompt, user_prompt = self.build_prompt(
            document_type, params, style_examples, reference_data
        )

        # 4. Generate
        return self.llm.generate_document(system_prompt, user_prompt)

    # -- DOCX conversion -------------------------------------------------

    @staticmethod
    def text_to_docx(text: str, title: str = "Generated Document") -> bytes:
        """Convert plain text to a formatted .docx and return the bytes."""
        doc = DocxDocument()

        # Page setup
        section = doc.sections[0]
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.25)

        # Title
        title_para = doc.add_heading(title, level=0)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Disclaimer
        disclaimer = doc.add_paragraph()
        disclaimer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = disclaimer.add_run(
            "DRAFT — FOR ATTORNEY REVIEW ONLY — NOT LEGAL ADVICE"
        )
        run.bold = True
        run.font.size = Pt(9)

        doc.add_paragraph("")  # spacer

        # Body text — preserve paragraphs and basic structure
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                doc.add_paragraph("")
                continue

            # Detect heading-like lines (ALL CAPS or starts with a number + period)
            if (
                stripped.isupper() and len(stripped) < 120
            ) or re.match(r"^(ARTICLE|SECTION|RECITAL)\s", stripped, re.IGNORECASE):
                doc.add_heading(stripped, level=1)
            elif re.match(r"^\d+\.\s+[A-Z]", stripped):
                doc.add_heading(stripped, level=2)
            else:
                p = doc.add_paragraph(stripped)
                p.paragraph_format.space_after = Pt(6)
                for run in p.runs:
                    run.font.size = Pt(11)

        # Write to bytes
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
