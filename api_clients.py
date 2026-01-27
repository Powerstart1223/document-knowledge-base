"""
External data-source clients for the Corporate Law Document Generator.

- SECEdgarClient  — free, public SEC EDGAR full-text search API
- NetDocumentsClient — wraps the existing NetDocuments OAuth API code
- LegalDatabaseClient — stub for Westlaw / LexisNexis (requires commercial API)
"""

import os
import re
import base64
import requests
from urllib.parse import urlencode


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
# NetDocuments (wraps existing netdocuments_direct_api.py)
# ======================================================================


class NetDocumentsClient:
    """Facade around the existing NetDocumentsDirectAPI for Streamlit use."""

    AUTH_URL = "https://vault.netvoyage.com/neWeb2/OAuth.aspx"
    TOKEN_URL = "https://api.vault.netvoyage.com/v1/oauth/access_token"
    DEFAULT_BASE = "https://api.vault.netvoyage.com"

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        redirect_uri: str = "https://localhost:3000/gettoken",
    ):
        self.client_id = client_id or os.getenv("NETDOCUMENTS_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv(
            "NETDOCUMENTS_CLIENT_SECRET", ""
        )
        self.redirect_uri = redirect_uri or os.getenv(
            "NETDOCUMENTS_REDIRECT_URI", "https://localhost:3000/gettoken"
        )
        self.access_token: str | None = None
        self.base_url: str = self.DEFAULT_BASE

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def is_authenticated(self) -> bool:
        return bool(self.access_token)

    # -- OAuth -----------------------------------------------------------

    def get_authorization_url(self) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read lookup",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def authenticate(self, auth_code: str) -> bool:
        """Exchange an authorization code for an access token."""
        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {creds}",
        }
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
        }
        r = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=15)
        r.raise_for_status()
        token_data = r.json()
        self.access_token = token_data["access_token"]
        self.base_url = token_data.get("base_uri", self.DEFAULT_BASE)
        return True

    # -- Document operations ---------------------------------------------

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        if not self.access_token:
            raise RuntimeError("Not authenticated — call authenticate() first.")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def search_documents(self, query: str, max_results: int = 10) -> list[dict]:
        params = {"q": query, "max": max_results, "searchType": "fulltext"}
        result = self._get("v1/search", params)
        return result.get("items", [])

    def download_document_text(self, doc_id: str, max_chars: int = 20_000) -> str:
        """Download a document and return its text (best-effort)."""
        if not self.access_token:
            raise RuntimeError("Not authenticated.")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.base_url}/v1/documents/{doc_id}/content"
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        # Return raw text (works for .txt; binary formats won't be useful)
        return r.text[:max_chars]


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
