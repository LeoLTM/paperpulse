"""
Paper summarisation agent built on the OpenAI Agents SDK.

Two Agent objects are used per run:
  summarizer  — generates a themed summary for each batch of papers
  combiner    — merges multiple batch summaries into one final post

The OPENAI_API_KEY environment variable is read automatically by the SDK.
The model is controlled via the OPENAI_MODEL env var (default: gpt-4o-mini).
"""
import logging

from agents import Agent as SDKAgent, Runner, ModelSettings

from api.settings import OPENAI_MODEL, build_summary_prompt, build_combine_prompt

logger = logging.getLogger(__name__)


class PaperpulseAgent:
    """Orchestrates batch summarisation of ArXiv papers via the OpenAI Agents SDK."""

    def __init__(self, config):
        self.summarizer = SDKAgent(
            name="Engineering Research Summariser",
            instructions=build_summary_prompt(config),
            model=OPENAI_MODEL,
            model_settings=ModelSettings(
                temperature=0.1,
                top_p=0.9,
            ),
        )
        self.combiner = SDKAgent(
            name="Summary Combiner",
            instructions=build_combine_prompt(config),
            model=OPENAI_MODEL,
            model_settings=ModelSettings(
                temperature=0.1,
                top_p=0.9,
            ),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _format_paper(self, paper):
        return (
            f"**Title:** {paper['title']}\n"
            f"**Authors:** {', '.join(paper['authors'])}\n"
            f"**Summary:** {paper['summary']}\n"
        )

    def _batch_papers(self, papers, max_chars):
        """Split papers into batches whose combined text stays under max_chars."""
        batches, current_batch, current_length = [], [], 0
        for paper in papers:
            chunk = self._format_paper(paper)
            if current_length + len(chunk) > max_chars and current_batch:
                batches.append(current_batch)
                current_batch, current_length = [], 0
            current_batch.append(paper)
            current_length += len(chunk)
        if current_batch:
            batches.append(current_batch)
        logger.info("Split %d papers into %d batches", len(papers), len(batches))
        return batches

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def identify_important_papers(self, papers):
        """Summarise all papers in batches, then merge into a single post."""
        if not papers:
            raise ValueError("No papers provided to summarise")

        # ~4 chars per token; keep well under the model's context window
        MAX_CHARS = 122_000 * 4

        batches = self._batch_papers(papers, MAX_CHARS)
        intermediate = []

        for i, batch in enumerate(batches, 1):
            logger.info("Processing batch %d / %d", i, len(batches))
            batch_text = "\n".join(self._format_paper(p) for p in batch)
            try:
                result = Runner.run_sync(self.summarizer, batch_text)
                intermediate.append(result.final_output)
                logger.info("Batch %d done", i)
            except Exception as exc:
                logger.error("Batch %d failed: %s", i, exc)

        if not intermediate:
            return ""

        if len(intermediate) == 1:
            return intermediate[0]

        # Merge batch summaries into one coherent post
        combined_text = "\n\n".join(intermediate)
        try:
            result = Runner.run_sync(self.combiner, combined_text)
            return result.final_output
        except Exception as exc:
            logger.error("Combine step failed: %s", exc)
            return combined_text
