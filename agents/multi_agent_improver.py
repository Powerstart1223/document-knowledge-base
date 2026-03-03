"""Multi-agent improvement loop for model quality using EDGAR + uploaded files."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api_clients import SECEdgarClient
from llm_backend import LLMBackend

try:
    import PyPDF2
except Exception:  # pragma: no cover
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except Exception:  # pragma: no cover
    DocxDocument = None


@dataclass
class CorpusDoc:
    doc_id: str
    source: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalCase:
    case_id: str
    source_doc_id: str
    source: str
    question: str
    reference_answer: str
    must_include: list[str]
    context: str


@dataclass
class CandidateConfig:
    candidate_id: str
    system_prompt: str
    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 50
    notes: str = ""


@dataclass
class CandidateScore:
    candidate: CandidateConfig
    avg_score: float
    case_scores: list[float]
    notes: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_json_extract(text: str, fallback: Any) -> Any:
    if not text:
        return fallback
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass

    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass

    return fallback


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def extract_file_text(path: Path, max_chars: int) -> str:
    ext = path.suffix.lower()

    if ext in {".txt", ".md", ".json", ".csv", ".log"}:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]

    if ext == ".pdf" and PyPDF2 is not None:
        with path.open("rb") as f:
            reader = PyPDF2.PdfReader(f)
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            return "\n".join(parts)[:max_chars]

    if ext in {".docx", ".docm", ".doc"} and DocxDocument is not None:
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)[:max_chars]

    return ""


class UploadIngestionAgent:
    def __init__(self, uploads_dir: Path, max_files: int, max_chars_per_doc: int):
        self.uploads_dir = uploads_dir
        self.max_files = max_files
        self.max_chars_per_doc = max_chars_per_doc

    def run(self) -> list[CorpusDoc]:
        if not self.uploads_dir.exists():
            return []

        files = [
            p
            for p in self.uploads_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in {".txt", ".md", ".pdf", ".docx", ".docm", ".doc"}
        ]
        files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[: self.max_files]

        docs: list[CorpusDoc] = []
        for path in files:
            try:
                text = clean_text(extract_file_text(path, self.max_chars_per_doc))
                if len(text) < 200:
                    continue
                doc_id = f"upload-{hash_text(str(path))}"
                docs.append(
                    CorpusDoc(
                        doc_id=doc_id,
                        source="upload",
                        title=path.name,
                        text=text,
                        metadata={"path": str(path), "size": path.stat().st_size},
                    )
                )
            except Exception:
                continue
        return docs


class EdgarIngestionAgent:
    def __init__(
        self,
        queries: list[str],
        max_results_per_query: int,
        max_chars_per_doc: int,
        user_agent: str | None = None,
    ):
        self.queries = [q.strip() for q in queries if q.strip()]
        self.max_results_per_query = max_results_per_query
        self.max_chars_per_doc = max_chars_per_doc
        self.client = SECEdgarClient(user_agent=user_agent)

    def run(self) -> list[CorpusDoc]:
        if not self.queries or not self.client.is_configured():
            return []

        docs: list[CorpusDoc] = []
        seen_urls: set[str] = set()

        for query in self.queries:
            try:
                filings = self.client.search_filings(query=query, max_results=self.max_results_per_query)
            except Exception:
                continue

            for filing in filings:
                url = filing.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                try:
                    text = clean_text(self.client.download_filing_text(url, max_chars=self.max_chars_per_doc))
                    if len(text) < 500:
                        continue
                    doc_id = f"edgar-{hash_text(url)}"
                    title = f"{filing.get('entity_name', 'Unknown')} {filing.get('form_type', '')} {filing.get('file_date', '')}".strip()
                    docs.append(
                        CorpusDoc(
                            doc_id=doc_id,
                            source="edgar",
                            title=title,
                            text=text,
                            metadata=filing,
                        )
                    )
                except Exception:
                    continue

        return docs


class DiscussionAgent:
    def __init__(self, llm: LLMBackend):
        self.llm = llm

    def propose_candidates(
        self,
        best_candidate: CandidateConfig,
        recent_scores: list[CandidateScore],
        max_candidates: int,
    ) -> list[CandidateConfig]:
        perf_snapshot = [
            {
                "candidate_id": x.candidate.candidate_id,
                "avg_score": x.avg_score,
                "temperature": x.candidate.temperature,
                "top_p": x.candidate.top_p,
                "top_k": x.candidate.top_k,
                "notes": x.candidate.notes,
            }
            for x in recent_scores[:8]
        ]

        prompt = (
            "You are an optimization strategist. Propose JSON array only. "
            "Return up to "
            f"{max_candidates} candidate configs improving factual legal extraction from EDGAR and uploaded docs. "
            "Each item must include: system_prompt, temperature (0-1), top_p (0.1-1), top_k (0-200), notes. "
            "Avoid broad creativity; prioritize grounded answers from provided context. "
            f"Current best: {json.dumps(asdict(best_candidate))}. "
            f"Recent performance: {json.dumps(perf_snapshot)}"
        )

        messages = [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": prompt},
        ]

        try:
            raw = self.llm.chat(messages, temperature=0.2, max_tokens=1800)
            data = safe_json_extract(raw, fallback=[])
        except Exception:
            data = []

        proposals: list[CandidateConfig] = []
        for i, item in enumerate(data if isinstance(data, list) else []):
            if not isinstance(item, dict):
                continue
            system_prompt = str(item.get("system_prompt", "")).strip()
            if not system_prompt:
                continue
            proposals.append(
                CandidateConfig(
                    candidate_id=f"proposal-{i + 1}-{hash_text(system_prompt)}",
                    system_prompt=system_prompt,
                    temperature=float(item.get("temperature", best_candidate.temperature)),
                    top_p=float(item.get("top_p", best_candidate.top_p)),
                    top_k=int(item.get("top_k", best_candidate.top_k)),
                    notes=str(item.get("notes", "discussion proposal")),
                )
            )
            if len(proposals) >= max_candidates:
                break

        if not proposals:
            proposals = [
                CandidateConfig(
                    candidate_id=f"fallback-low-temp-{hash_text(best_candidate.system_prompt)}",
                    system_prompt=best_candidate.system_prompt,
                    temperature=max(0.0, best_candidate.temperature - 0.05),
                    top_p=min(1.0, best_candidate.top_p),
                    top_k=best_candidate.top_k,
                    notes="fallback: reduced temperature",
                ),
                CandidateConfig(
                    candidate_id=f"fallback-grounded-{hash_text(best_candidate.system_prompt + 'grounded')}",
                    system_prompt=(
                        best_candidate.system_prompt
                        + " Always quote exact facts from the context and state uncertainty if not found."
                    ),
                    temperature=best_candidate.temperature,
                    top_p=max(0.7, best_candidate.top_p - 0.05),
                    top_k=best_candidate.top_k,
                    notes="fallback: stronger grounding",
                ),
            ]

        return proposals[:max_candidates]


class CaseBuilderAgent:
    def __init__(self, llm: LLMBackend):
        self.llm = llm

    def build_cases(self, docs: list[CorpusDoc], max_cases: int) -> list[EvalCase]:
        cases: list[EvalCase] = []
        for doc in docs:
            if len(cases) >= max_cases:
                break
            generated = self._build_cases_for_doc(doc, per_doc=2)
            for case in generated:
                cases.append(case)
                if len(cases) >= max_cases:
                    break
        return cases

    def _build_cases_for_doc(self, doc: CorpusDoc, per_doc: int) -> list[EvalCase]:
        context = doc.text[:6000]
        prompt = (
            "Create "
            f"{per_doc} factual Q/A evaluation items from this legal context. "
            "Return JSON array only. Each item: question, reference_answer, must_include(list max 4 short exact phrases). "
            "Questions must be answerable from context only."
            f"\nContext:\n{context}"
        )

        messages = [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": prompt},
        ]

        try:
            raw = self.llm.chat(messages, temperature=0.1, max_tokens=1800)
            data = safe_json_extract(raw, fallback=[])
        except Exception:
            data = []

        out: list[EvalCase] = []
        for i, item in enumerate(data if isinstance(data, list) else []):
            if not isinstance(item, dict):
                continue
            q = clean_text(str(item.get("question", "")))
            a = clean_text(str(item.get("reference_answer", "")))
            must = item.get("must_include", [])
            must_include = [clean_text(str(x)) for x in must if str(x).strip()][:4]
            if not q or not a:
                continue
            out.append(
                EvalCase(
                    case_id=f"{doc.doc_id}-case-{i + 1}",
                    source_doc_id=doc.doc_id,
                    source=doc.source,
                    question=q,
                    reference_answer=a,
                    must_include=must_include,
                    context=context,
                )
            )

        if out:
            return out[:per_doc]

        return [
            EvalCase(
                case_id=f"{doc.doc_id}-fallback-1",
                source_doc_id=doc.doc_id,
                source=doc.source,
                question="What are the most material obligations and dates stated in the context?",
                reference_answer=context[:800],
                must_include=[],
                context=context,
            )
        ]


class ResponseAgent:
    def __init__(self, llm: LLMBackend):
        self.llm = llm

    def answer(self, candidate: CandidateConfig, case: EvalCase) -> str:
        messages = [
            {"role": "system", "content": candidate.system_prompt},
            {
                "role": "user",
                "content": (
                    "Use only this context to answer the question. "
                    "If unknown, say so explicitly."
                    f"\n\nContext:\n{case.context}\n\nQuestion: {case.question}"
                ),
            },
        ]
        try:
            return self.llm.chat(
                messages,
                temperature=max(0.0, min(1.0, candidate.temperature)),
                top_p=max(0.1, min(1.0, candidate.top_p)),
                top_k=max(0, candidate.top_k),
                max_tokens=700,
            )
        except Exception as exc:
            return f"ERROR: {exc}"


class JudgeAgent:
    def __init__(self, llm: LLMBackend):
        self.llm = llm

    def score(self, case: EvalCase, answer: str) -> float:
        if answer.startswith("ERROR:"):
            return 0.0

        judge_prompt = (
            "Score this model answer for factual alignment with reference and required phrases. "
            "Return JSON only: {\"score\": 0..1}."
            f"\nQuestion: {case.question}"
            f"\nReference: {case.reference_answer}"
            f"\nMust include: {case.must_include}"
            f"\nModel answer: {answer}"
        )
        messages = [
            {"role": "system", "content": "You are a strict evaluator. Return strict JSON only."},
            {"role": "user", "content": judge_prompt},
        ]

        try:
            raw = self.llm.chat(messages, temperature=0.0, max_tokens=200)
            data = safe_json_extract(raw, fallback={})
            if isinstance(data, dict) and "score" in data:
                return float(max(0.0, min(1.0, float(data["score"]))))
        except Exception:
            pass

        ref = set(clean_text(case.reference_answer).lower().split())
        ans = set(clean_text(answer).lower().split())
        if not ref:
            return 0.0
        overlap = len(ref.intersection(ans)) / max(1, len(ref))
        must_hits = 0
        if case.must_include:
            for phrase in case.must_include:
                if phrase and phrase.lower() in answer.lower():
                    must_hits += 1
            must_score = must_hits / len(case.must_include)
        else:
            must_score = overlap
        return max(0.0, min(1.0, 0.7 * overlap + 0.3 * must_score))


class EvaluatorAgent:
    def __init__(self, responder: ResponseAgent, judge: JudgeAgent, workers: int):
        self.responder = responder
        self.judge = judge
        self.workers = workers

    def evaluate(self, candidate: CandidateConfig, cases: list[EvalCase]) -> CandidateScore:
        if not cases:
            return CandidateScore(candidate=candidate, avg_score=0.0, case_scores=[])

        scores: list[float] = []

        def eval_one(case: EvalCase) -> float:
            answer = self.responder.answer(candidate, case)
            return self.judge.score(case, answer)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            futures = [ex.submit(eval_one, case) for case in cases]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    scores.append(float(fut.result()))
                except Exception:
                    scores.append(0.0)

        avg = sum(scores) / len(scores)
        return CandidateScore(candidate=candidate, avg_score=avg, case_scores=scores)


class ImprovementOrchestrator:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.llm = LLMBackend(
            provider=args.provider,
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
        )

        self.case_builder = CaseBuilderAgent(self.llm)
        self.discussion = DiscussionAgent(self.llm)
        self.evaluator = EvaluatorAgent(
            responder=ResponseAgent(self.llm),
            judge=JudgeAgent(self.llm),
            workers=args.case_workers,
        )

        self.run_dir = Path(args.output_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def ingest(self) -> list[CorpusDoc]:
        upload_agent = UploadIngestionAgent(
            uploads_dir=Path(self.args.uploads_dir),
            max_files=self.args.max_upload_files,
            max_chars_per_doc=self.args.max_chars_per_doc,
        )
        edgar_agent = EdgarIngestionAgent(
            queries=[q.strip() for q in self.args.edgar_queries.split(",") if q.strip()],
            max_results_per_query=self.args.max_filings_per_query,
            max_chars_per_doc=self.args.max_chars_per_doc,
            user_agent=self.args.sec_user_agent or os.getenv("SEC_EDGAR_USER_AGENT", ""),
        )

        docs: list[CorpusDoc] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            futures = []
            if self.args.mode in {"hybrid", "uploads"}:
                futures.append(ex.submit(upload_agent.run))
            if self.args.mode in {"hybrid", "edgar"}:
                futures.append(ex.submit(edgar_agent.run))
            for fut in concurrent.futures.as_completed(futures):
                try:
                    docs.extend(fut.result())
                except Exception:
                    continue

        dedup: dict[str, CorpusDoc] = {}
        for doc in docs:
            key = hash_text(doc.text)
            dedup[key] = doc
        return list(dedup.values())

    def run(self) -> dict[str, Any]:
        docs = self.ingest()
        cases = self.case_builder.build_cases(docs=docs, max_cases=self.args.max_cases)

        best = CandidateConfig(
            candidate_id="baseline",
            system_prompt=self.args.base_system_prompt,
            temperature=self.args.base_temperature,
            top_p=self.args.base_top_p,
            top_k=self.args.base_top_k,
            notes="baseline",
        )

        history: list[CandidateScore] = []

        for iteration in range(1, self.args.iterations + 1):
            candidates = [best]
            proposals = self.discussion.propose_candidates(
                best_candidate=best,
                recent_scores=sorted(history, key=lambda x: x.avg_score, reverse=True),
                max_candidates=max(1, self.args.candidates_per_iteration - 1),
            )
            candidates.extend(proposals)

            eval_results: list[CandidateScore] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.candidate_workers) as ex:
                futures = [ex.submit(self.evaluator.evaluate, c, cases) for c in candidates]
                for fut in concurrent.futures.as_completed(futures):
                    try:
                        eval_results.append(fut.result())
                    except Exception:
                        continue

            eval_results = sorted(eval_results, key=lambda x: x.avg_score, reverse=True)
            if eval_results and eval_results[0].avg_score >= best_score(history):
                best = eval_results[0].candidate

            history.extend(eval_results)
            self._write_iteration(iteration, docs, cases, best, eval_results)

        final = {
            "timestamp": utc_now(),
            "mode": self.args.mode,
            "docs_count": len(docs),
            "cases_count": len(cases),
            "best_candidate": asdict(best),
            "best_score": best_score(history),
            "top_results": [
                {
                    "candidate": asdict(x.candidate),
                    "avg_score": x.avg_score,
                }
                for x in sorted(history, key=lambda y: y.avg_score, reverse=True)[:10]
            ],
            "run_dir": str(self.run_dir),
        }

        latest_file = Path(self.args.output_dir) / "latest.json"
        latest_file.write_text(json.dumps(final, indent=2), encoding="utf-8")
        return final

    def _write_iteration(
        self,
        iteration: int,
        docs: list[CorpusDoc],
        cases: list[EvalCase],
        best: CandidateConfig,
        results: list[CandidateScore],
    ):
        payload = {
            "timestamp": utc_now(),
            "iteration": iteration,
            "best": asdict(best),
            "docs": [asdict(d) for d in docs[:30]],
            "cases": [asdict(c) for c in cases[:80]],
            "results": [
                {
                    "candidate": asdict(r.candidate),
                    "avg_score": r.avg_score,
                    "case_scores": r.case_scores,
                }
                for r in results
            ],
        }
        path = self.run_dir / f"iteration_{iteration:03d}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def best_score(history: list[CandidateScore]) -> float:
    if not history:
        return 0.0
    return max(x.avg_score for x in history)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run parallel multi-agent model improvement loop")
    parser.add_argument("--mode", choices=["hybrid", "edgar", "uploads"], default="hybrid")
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--candidates-per-iteration", type=int, default=5)
    parser.add_argument("--candidate-workers", type=int, default=4)
    parser.add_argument("--case-workers", type=int, default=6)

    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "ollama"))
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", os.getenv("OPENAI_MODEL", "llama3.1:8b")))
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", "ollama"))

    parser.add_argument("--uploads-dir", default="uploads")
    parser.add_argument("--max-upload-files", type=int, default=120)
    parser.add_argument("--edgar-queries", default="material agreement,credit agreement,merger agreement,risk factors")
    parser.add_argument("--max-filings-per-query", type=int, default=6)
    parser.add_argument("--sec-user-agent", default=os.getenv("SEC_EDGAR_USER_AGENT", ""))
    parser.add_argument("--max-chars-per-doc", type=int, default=16000)
    parser.add_argument("--max-cases", type=int, default=80)

    parser.add_argument("--base-temperature", type=float, default=0.2)
    parser.add_argument("--base-top-p", type=float, default=0.95)
    parser.add_argument("--base-top-k", type=int, default=50)
    parser.add_argument(
        "--base-system-prompt",
        default=(
            "You are a legal analysis assistant. Use only provided context, cite concrete facts, "
            "and do not invent missing information."
        ),
    )

    parser.add_argument("--output-dir", default="artifacts/agent_improvement")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    orchestrator = ImprovementOrchestrator(args)
    result = orchestrator.run()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
