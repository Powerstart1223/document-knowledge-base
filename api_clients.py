"""
External data-source clients for the Corporate Law Document Generator.

- SECEdgarClient  — free, public SEC EDGAR full-text search API
- LegalDatabaseClient — stub for Westlaw / LexisNexis (requires commercial API)
"""

import os
import re
import requests


# ======================================================================
# SEC EDGAR (public, free — only needs a User-Agent with contact email)
# ======================================================================


class SECEdgarClient:
    """Client for the SEC EDGAR full-text search and company filings APIs."""

    EFTS_BASE = "https://efts.sec.gov/LATEST"
    SUBMISSIONS_BASE = "https://data.sec.gov/submissions"

    def __init__(self, user_agent: str | None = None):
        self.user_agent = user_agent or os.getenv(
            "SEC_EDGAR_USER_AGENT", ""
        )
        self._session = requests.Session()
        if self.user_agent:
            self._session.headers["User-Agent"] = self.user_agent

    def is_configured(self) -> bool:
        return bool(self.user_agent)

    # -- Full-text search ------------------------------------------------

    def search_filings(
        self,
        query: str,
        form_types: list[str] | None = None,
        max_results: int = 10,
    ) -> list[dict]:
        """Search EDGAR full-text search (EFTS) for filings matching *query*."""
        params: dict = {"q": query, "from": 0, "size": max_results}
        if form_types:
            params["forms"] = ",".join(form_types)

        r = self._session.get(
            f"{self.EFTS_BASE}/search-index",
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        results = []
        for h in hits:
            src = h.get("_source", {})
            display_names = src.get("display_names", [])
            entity_name = display_names[0] if display_names else ""
            file_nums = src.get("file_num", [])
            ciks = src.get("ciks", [])
            adsh = src.get("adsh", "")
            # Construct filing URL from accession number
            url = ""
            if adsh and ciks:
                cik = ciks[0].lstrip("0")
                adsh_nodash = adsh.replace("-", "")
                url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh_nodash}/{adsh}-index.htm"
            results.append(
                {
                    "file_date": src.get("file_date"),
                    "entity_name": entity_name,
                    "form_type": src.get("form"),
                    "file_number": file_nums[0] if file_nums else "",
                    "cik": ciks[0] if ciks else "",
                    "url": url,
                }
            )
        return results

    # -- Company filings by CIK -----------------------------------------

    def lookup_cik(self, company_name: str) -> list[dict]:
        """Look up CIK numbers for a company name."""
        r = self._session.get(
            f"{self.EFTS_BASE}/search-index",
            params={"q": company_name, "size": 5},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        seen = {}
        for h in data.get("hits", {}).get("hits", []):
            src = h.get("_source", {})
            ciks = src.get("ciks", [])
            display_names = src.get("display_names", [])
            for cik in ciks:
                if cik and cik not in seen:
                    name = display_names[0] if display_names else ""
                    seen[cik] = {"cik": cik, "entity_name": name}
        return list(seen.values())

    def get_company_filings(self, cik: str | int) -> dict:
        """Return recent filing metadata for a given CIK number."""
        cik_str = str(cik).zfill(10)
        r = self._session.get(
            f"{self.SUBMISSIONS_BASE}/CIK{cik_str}.json",
            timeout=15,
        )
        r.raise_for_status()
        return r.json()

    def download_filing_text(self, filing_url: str, max_chars: int = 20_000) -> str:
        """Download the raw text of a filing (truncated to *max_chars*)."""
        if not filing_url.startswith("http"):
            filing_url = f"https://www.sec.gov/Archives/{filing_url}"
        r = self._session.get(filing_url, timeout=30)
        r.raise_for_status()
        text = r.text[:max_chars]
        # Strip HTML tags for a rough plaintext conversion
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text


# ======================================================================
# Westlaw / LexisNexis (stub — requires commercial API subscription)
# ======================================================================


class NotConfiguredError(Exception):
    """Raised when a service requires credentials that are not set."""


class LegalDatabaseClient:
    """Stub for Westlaw / LexisNexis commercial APIs."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("LEGAL_DB_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _require_key(self):
        if not self.api_key:
            raise NotConfiguredError(
                "Westlaw / LexisNexis API key not configured. "
                "These services require a commercial subscription. "
                "Set LEGAL_DB_API_KEY in your .env file once you have one."
            )

    def search_cases(self, query: str) -> list[dict]:
        self._require_key()
        # Placeholder — implement when credentials are available
        return []

    def search_statutes(self, query: str) -> list[dict]:
        self._require_key()
        return []
