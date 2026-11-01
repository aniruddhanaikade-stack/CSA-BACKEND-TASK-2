import ipaddress
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import DatabaseError
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import Link, get_or_create_link


def check_url(text):
    """Return an error message if the URL is bad, or None if it is fine."""
    if not text:
        return "Please enter a URL."
    if len(text) > 2000:
        return "That URL is too long (max 2000 characters)."

    # only http and https (blocks javascript:, ftp:, file: ...)
    parts = urlparse(text)
    if parts.scheme not in ("http", "https"):
        return "URL must start with http:// or https://"

    try:
        URLValidator()(text)
    except ValidationError:
        return "That does not look like a valid URL."

    # do not allow links that point to our own machine or private networks
    host = parts.hostname
    if host == "localhost":
        return "Links to localhost are not allowed."
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return "Links to private addresses are not allowed."
    except ValueError:
        pass  # host is a normal name, not an IP

    return None


def show_error(request, message, status):
    return render(request, "links/error.html", {"message": message}, status=status)


def home(request):
    if request.method != "POST":
        return render(request, "links/home.html")

    text = request.POST.get("long_url", "").strip()
    error = check_url(text)
    if error:
        return render(request, "links/home.html", {"error": error, "text": text}, status=400)

    try:
        link, was_created = get_or_create_link(text)
    except (DatabaseError, RuntimeError):
        return show_error(request, "Could not save the link. Please try again.", 503)

    short_url = request.build_absolute_uri(reverse("go", args=[link.code]))
    stats_url = reverse("stats", args=[link.code])
    return render(
        request,
        "links/home.html",
        {"link": link, "short_url": short_url, "stats_url": stats_url, "was_created": was_created},
    )


def go(request, code):
    try:
        link = Link.objects.filter(code=code).first()
        if link is None:
            return show_error(request, "This short link does not exist.", 404)
        # F() adds 1 inside the database, so two visitors at once are both counted
        Link.objects.filter(pk=link.pk).update(visits=F("visits") + 1)
    except DatabaseError:
        return show_error(request, "Service problem. Please try again.", 503)

    return HttpResponseRedirect(link.long_url)


def stats(request, code):
    try:
        link = Link.objects.filter(code=code).first()
    except DatabaseError:
        return show_error(request, "Service problem. Please try again.", 503)

    if link is None:
        return show_error(request, "This short link does not exist.", 404)

    short_url = request.build_absolute_uri(reverse("go", args=[link.code]))
    return render(request, "links/stats.html", {"link": link, "short_url": short_url})
