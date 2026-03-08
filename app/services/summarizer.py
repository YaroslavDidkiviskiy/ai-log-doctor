"""AI-powered incident summarization.

Provides an LLM-based summarizer when OPENAI_API_KEY is set,
and a rule-based fallback otherwise.
"""

import json
import logging
from abc import ABC, abstractmethod

from app.config import settings
from app.schemas.incident import AISummary

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an incident analysis assistant.

Your task is to analyze a grouped software incident from application logs.

You will receive:
- normalized error message
- several raw examples
- optional traceback
- number of occurrences
- service/module name
- first_seen and last_seen timestamps

Return strict JSON with the following fields:
- title: short incident title
- summary: concise explanation in 2-4 sentences
- possible_causes: array of 2-4 likely causes
- next_steps: array of 3-5 concrete debugging actions
- severity: one of ["low", "medium", "high", "critical"]

Rules:
- Do not invent infrastructure details that are not supported by the input
- Be cautious and practical
- Focus on debugging usefulness
- Keep wording clear and technical"""


class BaseSummarizer(ABC):
    @abstractmethod
    def summarize(
        self,
        *,
        normalized_message: str,
        sample_messages: list[str],
        sample_traceback: str | None,
        count: int,
        service: str | None,
        first_seen: str | None,
        last_seen: str | None,
    ) -> AISummary:
        ...


class LLMSummarizer(BaseSummarizer):
    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def summarize(
        self,
        *,
        normalized_message: str,
        sample_messages: list[str],
        sample_traceback: str | None,
        count: int,
        service: str | None,
        first_seen: str | None,
        last_seen: str | None,
    ) -> AISummary:
        user_content = json.dumps(
            {
                "normalized_message": normalized_message,
                "sample_raw_messages": sample_messages[:3],
                "traceback": sample_traceback,
                "occurrences": count,
                "service": service,
                "first_seen": first_seen,
                "last_seen": last_seen,
            },
            indent=2,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=600,
        )

        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return AISummary(**data)


class FallbackSummarizer(BaseSummarizer):
    """Rule-based summarizer used when no API key is configured."""

    def summarize(
        self,
        *,
        normalized_message: str,
        sample_messages: list[str],
        sample_traceback: str | None,
        count: int,
        service: str | None,
        first_seen: str | None,
        last_seen: str | None,
    ) -> AISummary:
        svc = service or "unknown service"
        title = f"Recurring issue in {svc}"

        summary = (
            f"This incident occurred {count} time(s) "
            f"between {first_seen or 'N/A'} and {last_seen or 'N/A'}. "
            f"Pattern: {normalized_message[:120]}"
        )

        causes = ["Application-level error (inspect stack trace and recent deployments)"]
        steps = [
            "Check application logs around the timestamps",
            "Review recent code changes or deployments",
            "Inspect related service dependencies",
        ]

        if sample_traceback:
            causes.append("Unhandled exception in code path")
            steps.append("Examine traceback for root cause")

        if "timeout" in normalized_message:
            causes.append("Downstream service or database timeout")
            steps.append("Check network latency and dependent service health")

        if "refused" in normalized_message:
            causes.append("Target service is down or rejecting connections")
            steps.append("Verify target service availability and firewall rules")

        severity = "medium"
        if count >= 10 or "fatal" in normalized_message:
            severity = "high"
        if "database" in normalized_message and "down" in normalized_message:
            severity = "critical"

        return AISummary(
            title=title,
            summary=summary,
            possible_causes=causes,
            next_steps=steps,
            severity=severity,
        )


def get_summarizer() -> BaseSummarizer:
    if settings.OPENAI_API_KEY:
        logger.info("Using LLM summarizer (OpenAI)")
        return LLMSummarizer()
    logger.info("No OPENAI_API_KEY set — using fallback summarizer")
    return FallbackSummarizer()
