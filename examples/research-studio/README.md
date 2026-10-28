# Synthetic research studio walkthrough

These five rows are invented interface fixtures, **not experimental results**. They are unrelated to the real-paper conformal-prediction example. One reading is deliberately missing. No scientific interpretation, model call or human approval accompanies these files.

## Import in the browser

Create a separate record with a title such as “Synthetic studio practice”. Open **Data & figures**, choose CSV, and select [observations.csv](observations.csv).

Use the title and protocol from [metadata.json](metadata.json), leave the declared statistical method blank, and enter these **Columns and units** in this order:

```text
elapsed_minutes=min
reading=arbitrary units
```

Import the observations and inspect the rows. The empty reading must appear as missing rather than zero.

Create a figure titled “Synthetic readings — demonstration only”, choose `reading` for Y, `elapsed_minutes` for X and the line chart type. Preview and inspect the missing-observation warning, then save. Reopen the saved figure after reload and download SVG or CSV. A table using both columns exercises the table workflow.

Create a researcher note explicitly stating that the data is synthetic. Open **Writing**, inspect the source panel and insert the saved figure into a chapter. Save a manuscript revision. Export remains subject to the normal exact-revision review/approval gates; this walkthrough does not supply or automate approval.

## Optional CLI import

From the repository root, substitute the ID of your separate practice record:

```text
python research_cli.py import-experiment-csv RUN_ID examples/research-studio/observations.csv --metadata examples/research-studio/metadata.json
```

The metadata file is accepted by the CSV importer; the browser form requires entering its fields rather than uploading that metadata file separately. See the [studio guide](../../docs/research-studio.md) for workflow boundaries and design references.
