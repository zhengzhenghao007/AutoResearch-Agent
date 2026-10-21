# P5 deployment and operating boundaries

P5 supplies a single-host deployment mode: per-user SQLite storage, server-managed
bearer credentials, writer/reader permissions, durable search/analysis jobs and
bounded request/PDF processing. Scientific validity remains **not assessed**.
Model reviews remain explicit, synchronous opt-in operations; no job calls a model.

## Local use

The default remains the existing JSON store, with API access restricted to loopback
clients and local Host names. Bind Uvicorn to `127.0.0.1`. To use SQLite and background
jobs locally, set `AUTORESEARCH_STORAGE=sqlite` and `AUTORESEARCH_DATA_ROOT` to a
private directory before starting the API. Records live under `users/local`.
Windows local mode retains parser wall-clock limits; Linux supplies OS resource limits.
Do not expose local mode through a reverse proxy.

## Linux deployment

Use a dedicated unprivileged Linux service account and a private persistent data
directory. Install the tested dependencies from `requirements-ci.txt` in a Python
3.11/3.12 virtual environment. This version supports **one host and one API worker**;
SQLite must be on a local filesystem, not NFS or a shared multi-host volume.

Create a private users file outside the checkout (permissions `0600`). Generate a
different random token for each user with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
The format is:

```json
{
  "alice": {"token": "<replace with a random token>", "role": "writer"},
  "auditor": {"token": "<replace with another random token>", "role": "reader"}
}
```

Replace both placeholders. Tokens must contain 32–256 printable ASCII characters
without whitespace; IDs allow letters, digits, `_` and `-`, up to 64 characters.
There are at most 100 users. Each ID owns a separate namespace, including readers.
A reader can inspect data migrated into their namespace, but cannot mutate it.
This release does not implement shared projects, user registration or password recovery.

Example service environment and command, run from the repository root:

```sh
export AUTORESEARCH_DEPLOYMENT=1
export AUTORESEARCH_DATA_ROOT=/var/lib/autoresearch
export AUTORESEARCH_USERS_FILE=/etc/autoresearch/users.json
export AUTORESEARCH_ALLOWED_ORIGINS=https://research.example.org
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers --no-access-log
```

Run behind a TLS reverse proxy with an upstream body limit of 22 MiB, upload/request
timeouts and connection/rate limits. Keep port 8000 private; the application does not
terminate TLS. Configure the frontend build's `NEXT_PUBLIC_API_BASE_URL` to the HTTPS
API URL (or same-origin proxy), run `npm ci`, `npm run build`, then `npm start` behind
the proxy. Only the API URL is public configuration; never put tokens/users files in
`NEXT_PUBLIC_*`. Origins are explicit; do not configure wildcard access.

The UI requests an access token, keeps it in tab memory, and clears the workspace on
disconnect/account change. Reloading requires reconnecting. Tokens are sent only as
Authorization headers to the configured research API. Rotate/revoke credentials by
editing the server users file and restarting the API. Configure proxy logging to
exclude Authorization headers and sensitive payloads. `/api/health` is public and
returns no user information. All other API/docs routes require credentials.
Legacy `/api/papers` routes are disabled in deployment. Search and analysis must use
the bounded job API; synchronous equivalents are disabled in deployment.

## Migration, backup and recovery

Stop writers before migrating. Existing JSON data is not automatically moved:

```sh
.venv/bin/python -m services.sqlite_store /path/to/research_runs /var/lib/autoresearch/users/alice
```

This validates records and manuscript histories, imports all in one transaction and
refuses to overwrite any existing ID. Keep the original directory until verification.
Migration preserves manuscript revisions/reviews/approvals; it does not approve them.
Use an existing source directory; an empty directory imports zero records.
For backups, stop the service and copy the entire private data directory plus the
separately protected credential configuration. Restore to the same user IDs and
restart. Do not copy a live SQLite file without SQLite's backup API.

Optimistic run revisions reject stale writes with HTTP 409. Manuscript source,
revision and approval checks run inside database transactions. On conflict, reopen
the latest record and reapply the intended edit. Records are limited to 64 MiB and
manuscript histories retain their existing 20 MiB and revision-count limits.

## Background jobs and limits

`POST /api/research/jobs` accepts either `{"kind":"search","topic":"..."}` or
`{"kind":"analyze","run_id":"...","selected_ids":["..."]}`. GET lists jobs;
GET `/{id}` reads status; POST `/{id}/cancel` and `/{id}/retry` control work;
DELETE `/{id}` removes terminal history. Removing a job does not remove its record.
Retries are new attempts and require an explicit request.

- At most two worker processes total and four active jobs per user.
- At most 200 job history entries per user and three attempts per retry chain.
- Each operation has a 300-second supervisor deadline. Linux workers also have
  1 GiB address-space and 120-second CPU limits, plus a 300-second alarm.
- Search returns at most 20 candidates; analysis selects at most 20 candidates.
- Workers operate in temporary staging directories. Only the supervisor commits
  a successful result. Cancellation, failure, stale source revisions or lost leases
  prevent that commit. A successful job is not scientific approval.
- Cancellation is observed by the supervisor, which terminates the worker process
  group/tree. State remains `cancel_requested` until this completes.
- Queued jobs resume at API startup. Running jobs with a heartbeat older than
  30 seconds become `interrupted`; they require explicit retry and are not replayed.
- Browser navigation does not cancel server jobs. The UI opens results only when
  explicitly requested, preserving the currently edited record.

HTTP bodies have a 22 MiB limit before multipart parsing, a total 30-second read
deadline and eight concurrent admitted requests. These are per-process limits.
Linux PDF children have 512 MiB address-space, 30-second CPU and 64-file-descriptor
limits, alongside the existing 45-second wall deadline, 20 MiB input, 50-page and
one-million-character output caps. Deployment startup refuses unsupported platforms.

These controls do not provide a VM/container sandbox or an unlimited-scale service.
Use OS/container aggregate memory, CPU, disk and process quotas, a read-only code
mount, private writable data/temp paths and proxy rate limits. Persistent data and
abandoned temp directories after a hard crash need monitored disk quotas/maintenance.
Do not delete active staging directories. Job results and database storage consume
disk until explicitly managed; no automatic scientific-record deletion is performed.
Paid model use needs operator-side provider budgets. P5 does not provision a public
host, certificates or cloud infrastructure.
