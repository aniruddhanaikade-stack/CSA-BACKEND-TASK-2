# Design Notes

**Structure.** One Django project (`config`) with one app (`links`). A browser sends a request to Gunicorn, which runs Django. `urls.py` picks a view: `home` (form, creates links), `go` (redirects), `stats` (shows visits and creation time). Views use the `Link` model, which reads and writes the database. HTML pages are templates in `links/templates/links/`.

**Short codes.** Each code is 6 random letters/digits (`secrets.choice`), about 56 billion options. The `code` column has `unique=True`, so the database itself refuses a repeated code. If a clash happens, `IntegrityError` is caught and a new code is tried (up to 10 times). Nothing is hard-coded. The `long_url` column is also unique, so the same URL submitted twice returns the same link instead of making a new one. Different URLs can therefore never share a code.

**Storage.** SQLite, saved as one file in a Docker volume (`/data`). I chose it because it needs no extra server, so it is simple to run and reproduce, and the file survives container restarts and re-creation.

**Concurrency.** Two people may create the same URL at once: the unique columns make one insert fail, and the code then loads the winner's row, so there is still one link. For click counting, the code uses `F("visits") + 1`, which makes the database do the addition itself, so two simultaneous visits are both counted (a read-then-write would lose one).

**Limitation.** SQLite allows only one writer at a time and lives on one machine, so it will not scale to many servers or heavy traffic. Fix: move to PostgreSQL (same Django models, change `DATABASES`), and add Redis to count clicks quickly and save them to the database in batches. Also, `http://a.com` and `http://a.com/` count as different URLs, which could be fixed by cleaning URLs before saving.
