import os
import yaml

# ---------------------------------------------------------------------------
# OpenAI settings (read from environment — OPENAI_API_KEY is read by the SDK)
# ---------------------------------------------------------------------------
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ArXiv sort parameters (rarely need changing)
ARXIV_SORT_BY = 'lastUpdatedDate'
ARXIV_SORT_ORDER = 'descending'

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(config_path=None):
    """
    Load paperpulse configuration from config.yaml.

    Searches (in order):
      1. The explicit ``config_path`` argument
      2. ``$PROJECT_DIR/config.yaml``
      3. The repository root (two directories above this file)
    """
    if config_path is None:
        project_dir = os.getenv("PROJECT_DIR", "")
        repo_root = os.path.join(os.path.dirname(__file__), "..")
        candidates = [
            os.path.join(project_dir, "config.yaml"),
            os.path.join(repo_root, "config.yaml"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                config_path = path
                break

    if not config_path or not os.path.isfile(config_path):
        raise FileNotFoundError(
            "config.yaml not found. Set PROJECT_DIR or place config.yaml at the repo root."
        )

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# ArXiv query builder
# ---------------------------------------------------------------------------

def build_arxiv_query(config):
    """
    Construct an ArXiv API ``search_query`` string from *config*.

    The query format uses URL-encoded Boolean syntax:
    - Categories joined with ``+OR+`` (e.g. ``cat:cs.SE+OR+cat:cs.RO``)
    - Keywords mapped to ``all:`` prefix; multi-word terms are quoted
    - Both sides wrapped in parentheses and joined with ``+AND+`` when
      ``search.mode`` is ``categories_and_keywords`` (the default)
    """
    search = config.get("search", {})
    categories = search.get("categories", [])
    keywords = search.get("keywords", [])
    mode = search.get("mode", "categories_and_keywords")

    def _encode_keyword(kw):
        parts = kw.strip().split()
        if len(parts) > 1:
            return "all:%22" + "+".join(parts) + "%22"
        return f"all:{parts[0]}"

    cat_query = "+OR+".join(f"cat:{c}" for c in categories) if categories else ""
    kw_query = "+OR+".join(_encode_keyword(kw) for kw in keywords) if keywords else ""

    if mode == "categories_only" or not kw_query:
        return cat_query or "cat:cs.AI"
    if mode == "keywords_only" or not cat_query:
        return kw_query or "cat:cs.AI"
    # categories_and_keywords (default)
    return f"%28{cat_query}%29+AND+%28{kw_query}%29"


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_summary_prompt(config):
    """Return the system prompt used for per-batch summarisation."""
    summarization = config.get("summarization", {})
    persona = summarization.get("persona", "You are a research scientist.")
    style = summarization.get("style", "Explain concepts clearly and precisely.")
    return f"""{persona}
{style}

You are provided with a collection of academic papers and their abstracts.
Your goal is to write a single, coherent blogpost-style summary (under 5000 words) \
that summarises key developments and groups these into major themes.

For each theme:
1. Use a clear, descriptive heading (e.g., "Theme 1: Agentic Design Pipelines")
2. Highlight the most important developments and insights within that theme
3. Mention specific papers when relevant to illustrate points
4. If you mention specific papers, make sure to mention the complete title
5. Show how papers within the theme connect to each other

Write about each theme starting directly with "Theme 1:". Do not include any introductory text before Theme 1.

Format:
## Theme 1: [Theme Name]
[Content about theme 1 papers]

## Theme 2: [Theme Name]
[Content about theme 2 papers]

And so on...

List of Papers and Abstracts:
"""


def build_combine_prompt(config):
    """Return the prompt used to merge multiple batch summaries into one."""
    summarization = config.get("summarization", {})
    persona = summarization.get("persona", "You are a research scientist.")
    style = summarization.get("style", "Explain concepts clearly and precisely.")
    return f"""{persona}
{style}

You are tasked with combining multiple research summaries into a single coherent summary.
Please combine the following summaries, maintaining the thematic organisation and removing any redundancy.
Write about each theme starting directly with "Theme 1:". Do not include any introductory text before Theme 1.

"""