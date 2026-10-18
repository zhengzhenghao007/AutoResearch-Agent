# P3 user observations and reproducible statistics

P3 supports offline JSON/CSV ingestion, metadata and unit declarations, missingness
checks, descriptive statistics and cell-level references through the workspace,
API and CLI. Existing paper evidence and its review are unchanged. Experiment
prose and manuscript writing belong to P4; P3 never fabricates experimental claims.

Create an offline record in the workspace (enter a topic and choose Create offline
record) or run `python research_cli.py create "My experiment"`. Use the returned
run ID. Save the following **synthetic format example**
as UTF-8 JSON; replace it with your own observations before actual research use:

```json
{
  "title": "Example measurements",
  "protocol": null,
  "statistical_method": null,
  "columns": [
    {"name": "temperature", "unit": "C"},
    {"name": "score", "unit": null}
  ],
  "rows": [
    {"sample_id": "s1", "values": {"temperature": 0, "score": null}},
    {"sample_id": "s2", "values": {"temperature": 23.5, "score": 2}}
  ]
}
```

```text
python research_cli.py import-experiment RUN_ID measurements.json
python research_cli.py experiments RUN_ID
python research_cli.py experiment-statistics RUN_ID
```

HTTP: multipart POST `/api/research/runs/{run_id}/experiments`, file field `file`.
It accepts content, never a server-side path, and returns the updated ResearchRun.
GET at the same path returns the read-only completeness report. The existing
run detail endpoint includes original data and import provenance.

### CSV and metadata

For CSV, provide metadata with the JSON example's title, protocol,
statistical_method and columns, omitting rows. Metadata JSON is limited to 64 KiB.
CSV must be comma-delimited UTF-8 (optional BOM), with the exact header
`sample_id,temperature,score` for this example. Header order must match declared
columns. Quoted cells follow standard CSV rules. Empty numeric cells mean missing.
Ragged rows, blank rows, duplicate sample IDs or columns, formulas, NaN/Infinity,
numeric whitespace, and extra undeclared fields are rejected. The name sample_id
is reserved for the sample identifier in CSV.

```csv
sample_id,temperature,score
s1,0,
s2,23.5,2
```

```text
python research_cli.py import-experiment-csv RUN_ID measurements.csv --metadata metadata.json
```

HTTP: multipart POST `/api/research/runs/{run_id}/experiments/csv` with file field
`file` and text field `metadata` containing that JSON. The workspace accepts the
same CSV plus title, protocol, declared method and ordered `name=unit` lines.
Leaving the right side empty means unknown unit. Fields are preserved after a
failed save; completed writes update the record without clearing other drafts.

Inputs are limited to 1 MiB, 1–50 numeric columns, 1–1000 rows and 20 datasets per
run. Column names use an ASCII letter followed by letters, digits or underscores
(64 characters maximum). Each row has a unique, nonblank sample ID and exactly
the declared columns. Numbers must be finite JSON numbers; strings and booleans
are rejected. Use null for missing values; zero is counted as observed. No unit
conversion or metadata inference occurs. Metadata may be unknown (null), but
explicit blank strings are rejected. One row represents one user-declared sample;
independence, repeat measurements and effective statistical sample size are not
inferred or verified.

Exact original UTF-8 text (including optional BOM) and its byte SHA-256 are retained
alongside parsed data. JSON dataset IDs equal the original byte hash. For CSV,
`source_sha256` hashes the original CSV, while dataset ID/sha256 hash a canonical
JSON envelope containing format, exact csv_text and validated metadata. This
binds units and protocol to the same measurements. The envelope is limited to
2 MiB. Identical input plus metadata cannot be imported twice into a run.
Re-import the CSV envelope using the JSON option/endpoint/CLI command; these accept
up to 2 MiB for an envelope while ordinary JSON input remains limited to 1 MiB.
Semantically equivalent files with different bytes are
separate imports and are not automatically merged. Corrections are new datasets;
there is no replacement/deletion UI in this increment. Identifiers reference the
dataset hash plus sample ID and column name, not paper page quotations.

Load/save validation recomputes the hash and checks parsed equivalence. This
detects inconsistencies, not malicious rewriting of both data and hash, and does
not establish experimental authenticity. Old records load with no datasets.
Reports list sample counts, missing/observed values and unknown metadata; they
always mark scientific_validation=not_assessed. Report reads do not rewrite files.

### Statistics and input references

GET `/api/research/runs/{run_id}/experiment-statistics` (or the CLI command above)
returns `descriptive-v1`: observed/missing counts, minimum, maximum, mean and sample
standard deviation with denominator n-1. All-missing columns have null statistics;
a single observation has no sample SD. Missing observations are excluded without
imputation; groups, repeated-measure designs, independent-sample assumptions,
outlier deletion, unit conversions and significance testing are not inferred.

Integer inputs are exact. Fractional/exponent inputs follow Python JSON float
parsing, and calculation uses each float's shortest round-trip decimal value.
This is not arbitrary precision decimal input: original lexical decimals can be
rounded at parsing. Original input bytes remain available to audit this behavior.
Exact rational arithmetic computes sums and variance; mean/SD are rounded to
28 significant digits with ties-to-even. Output numbers are decimal strings so
browser JSON parsing cannot further round them. Each nonmissing input has a
sample_id, column and decimal value reference under its dataset hash. No synthetic
paper-style quotation or result Claim is generated from these values.

The workspace displays saved originals and metadata, and explicitly loads data
checks/statistics. JSON downloads retain complete references; the inline view
shows at most 100 references per column. Original-input download writes preserved
text directly, avoiding numeric parse/serialize changes. CSV also offers a metadata
envelope download. New record/revision changes discard outdated report responses.

No model or external service is called. Inputs remain in the local run snapshot.
The existing trusted, single-user JSON store has no multi-process transaction
isolation. HTTP multipart may be spooled before the application-level size check;
public deployment still needs request limits and authentication. No statistical
inference, imputation, generated experiment claims or scientific approval is added.
