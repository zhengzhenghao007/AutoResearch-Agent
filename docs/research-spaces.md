# Research spaces and optional paper quick reads

A project is a collection of papers, data and writing. Its name and research goal are separate.

- Start with **Research** and rename the heading by clicking it. Changes save on leaving the field. New unnamed projects receive Research, Research 2, and so on.
- **Add research goal (optional)** describes what you want to investigate. A project name never becomes an Agent instruction. You can collect and read papers without a goal.
- Search adds candidates to the current project, including background searches. Uploading a paper preserves its own filename and does not rename the project.
- The five navigation links are workspaces, not required sequential steps. In Compare, choose a subset of papers or compare all. In Library, open **Research assistant** to plan and execute a question with checkpoints and budgets.
- Old filename-named records display Research without rewriting their source metadata or existing manuscript evidence hashes.

## Paper quick read

In Reading & evidence, select a paper and click **Summarize paper** only if you want an outline. Opening a paper does not call a model. Reading, comparing and writing remain available without this feature.

The outline starts with one sentence and up to five main points. Expand research problem, author-claimed innovations, methods/experiments, findings/applications and limitations. With a goal it also offers relevance analysis; without a goal it may suggest research directions for the user to select. These suggestions are hypotheses, not established discoveries.

Every point has a page button opening its exact supporting passage. The server checks that quoted text occurs in the supplied source page. This validates attribution, not the correctness of the paraphrase or scientific novelty. Missing sections remain explicitly missing. OCR and partial coverage warnings remain visible.

Generation uses the existing `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` and optional `OPENROUTER_BASE_URL` configuration. If you start with `PYTHON_DOTENV_DISABLED=1`, configure these environment variables explicitly or remove that setting before using model features. Never put keys in the browser or commit `.env`.

Each explicit generation uses one provider call, no automatic retries, a 60-second transport timeout, a 6,000-token output ceiling and at most 40,000 source characters spread across up to 40 pages. Page text may be shortened; coverage identifies omitted pages and shortened text. Responses are stored by document and goal hash, reused without calls and checked again on read. Changing the goal/source requires a new explicit generation; renaming a project does not. Per-report OS-managed SQLite locks prevent duplicate concurrent generation across workers and release if a worker exits.

Provider errors never become fabricated outlines. A 429 response means the configured provider is rate-limited: wait for the quota to reset or configure another available model. It does not indicate a PDF import failure. No scientific quality guarantee is made for provider output.

## Verification scope

Automated tests cover metadata conflicts, source/goal bindings, malformed quotations, cache tampering, concurrent calls, read-only display, page navigation and retry behavior. Browser checks include the existing four-paper record, a selected comparison, writing navigation and mobile layout. A clearly marked synthetic fixture exercises saved outline display and reload. The live provider smoke test on a self-authored synthetic paper returned HTTP 429; a successful live model summary was not claimed. No private paper was sent during this smoke test.
