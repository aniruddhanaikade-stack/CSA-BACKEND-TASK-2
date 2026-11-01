# URL Shortener (Django)

Paste a long URL, get a short link. Visiting the short link sends you to the original page. Each link has a stats page (creation time and total visits).

Pages:
- `/` : form to create a short link
- `/<code>/` : redirect to the original URL
- `/stats/<code>/` : stats for the link

Design choices are explained in [design_notes.md](design_notes.md).

## 1. Run locally (no Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000

## 2. Run the tests

```bash
python manage.py test tests -v 2
```

The tests cover: a normal flow, bad URLs, unknown codes, a database failure, duplicate URLs, unique codes, a code clash, and data surviving a restart.

## 3. Run with Docker

```bash
cp .env.example .env        # then edit .env (see below)
docker compose up -d --build
```

Open http://localhost (port 80).

Useful commands:

```bash
docker compose ps           # is it running?
docker compose logs -f      # see logs
docker compose restart      # restart
docker compose down         # stop and remove the container (data is kept)
docker compose up -d        # start again
```

Your data lives in the Docker volume `shortener_data`, so it stays after `down` and `up`. Do NOT run `docker compose down -v`, because `-v` deletes the volume.

### The .env file

| Name | Meaning |
|------|---------|
| `SECRET_KEY` | A long random string. Make one with: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | Keep `False` on a server |
| `ALLOWED_HOSTS` | Comma separated list of your IP/domain, e.g. `localhost,127.0.0.1,3.110.10.20` |

## 4. Deploy on AWS EC2

1. **Launch an instance.** In the AWS console go to EC2 > Launch instance. Choose Ubuntu 24.04, type `t2.micro` or `t3.micro` (free tier), and create a key pair (download the `.pem` file).
2. **Security group (firewall).** Allow only:
   - SSH (22) from **My IP** only (not 0.0.0.0/0)
   - HTTP (80) from Anywhere
   Do not open any other port.
3. **Storage.** The default 8 GB disk is fine. The database is in a Docker volume on this disk.
4. **Connect:**
   ```bash
   chmod 400 mykey.pem
   ssh -i mykey.pem ubuntu@<PUBLIC_IP>
   ```
5. **Install Docker (on the server):**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker ubuntu
   ```
   Log out and log in again so the group change works.
6. **Get the code:**
   ```bash
   git clone <YOUR_REPO_URL> shortener
   cd shortener
   ```
7. **Set secrets:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   Set a new `SECRET_KEY`, keep `DEBUG=False`, and set `ALLOWED_HOSTS=<PUBLIC_IP>`.
   The `.env` file stays only on the server and is never committed to git.
8. **Start:**
   ```bash
   docker compose up -d --build
   ```
9. **Check:** open `http://<PUBLIC_IP>` in your browser.

### Start / restart

- `restart: unless-stopped` in `docker-compose.yml` brings the app back after a server reboot.
- Restart by hand: `docker compose restart`
- Update after code changes: `git pull && docker compose up -d --build`

### Evidence that it works

Add here after deploying:
- Deployed link: `http://<PUBLIC_IP>`
- Screenshots: create page, short link redirect, stats page
- Restart proof: note the visit count, run `docker compose down && docker compose up -d`, and show the count is the same.

## Project files

```
config/            settings, main urls
links/             models, views, urls, templates, migrations
tests/             automated tests
Dockerfile         builds the image
docker-compose.yml runs it with a data volume
design_notes.md    design explanation
```
