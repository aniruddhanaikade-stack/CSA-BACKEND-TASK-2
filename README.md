# URL Shortener

This is my Django project for Task 2. You paste a long link and the site gives you a short link. When someone opens the short link, it takes them to the original page. Each link also has a stats page that shows when it was created and how many times it was visited.

Live site: http://3.25.166.46

GitHub: https://github.com/aniruddhanaikade-stack/CSA-BACKEND-TASK-2

## Pages

- `/` : form to make a short link
- `/<code>/` : goes to the original link
- `/stats/<code>/` : shows creation time and total visits

My design choices are written in `design_notes.md`.

## Running on my computer

I used Windows so I typed `python`. On Mac or Linux it is `python3`.

```
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000

## Tests

```
python manage.py test tests -v 2
```

The tests check a normal flow, wrong URLs, a short code that does not exist, a database error, the same URL sent twice, different URLs getting different codes, a code clash, and data still being there after a restart.

## Docker

```
copy .env.example .env
docker compose up -d --build
```

On Mac or Linux use `cp` instead of `copy`. Open the `.env` file and set these values first:

- `SECRET_KEY` : a long random text
- `DEBUG` : keep it `False`
- `ALLOWED_HOSTS` : the IP or domain you use to open the site, like `localhost,127.0.0.1`

Then open http://localhost

The database is saved in a Docker volume called `shortener_data`. So the links and visit counts are still there after the container is stopped, removed and started again. I did not use `docker compose down -v` because `-v` deletes the volume and all the data.

## Deploying on AWS EC2

1. I created an EC2 instance in the Sydney region with Ubuntu and type t3.micro using my free AWS credits. I also made a key pair and downloaded the `.pem` file.
2. In the security group I allowed only SSH (port 22) from my own IP and HTTP (port 80) from the internet. No other ports are open.
3. I connected to the server from PowerShell:
   ```
   ssh -i C:\Users\Admin\mykey.pem ubuntu@3.25.166.46
   ```
4. I installed Docker and git on the server:
   ```
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
   ```
5. I downloaded my code from GitHub:
   ```
   git clone https://github.com/aniruddhanaikade-stack/CSA-BACKEND-TASK-2.git
   cd CSA-BACKEND-TASK-2
   ```
6. I made the `.env` file on the server with a new `SECRET_KEY`, `DEBUG=False` and `ALLOWED_HOSTS` set to my public IP. This file is only on the server and is not on GitHub.
   ```
   IP=$(curl -s https://checkip.amazonaws.com)
   echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')" > .env
   echo "DEBUG=False" >> .env
   echo "ALLOWED_HOSTS=$IP,localhost" >> .env
   ```
7. I started the app:
   ```
   sudo docker compose up -d --build
   ```
8. I opened http://3.25.166.46 in the browser and the site was working.

Commands to manage the app on the server:

```
sudo docker compose ps
sudo docker compose logs
sudo docker compose restart
```

To update the app after changing the code I run `git pull` and then `sudo docker compose up -d --build`. The app starts again by itself if the server reboots because of `restart: unless-stopped` in `docker-compose.yml`.

## Screenshots

Home page with a short link:

![home page](screenshots/home.png)

Stats page:

![stats page](screenshots/stats.png)

Stats page after restarting the app:

![stats after restart](screenshots/after_restart.png)

AWS security group:

![security group](screenshots/security_group.png)

## Restart test

I opened a short link a few times and noted the visit count on the stats page. Then I ran `sudo docker compose restart` on the server. After the restart the stats page showed the same count, so the data is not lost.

## Problems I faced

- On Windows `pip` was not recognized, so I used `python -m pip` instead.
- My `.pem` key file was in the Downloads folder, so I copied it to `C:\Users\Admin\mykey.pem` before `ssh` could find it.