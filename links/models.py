import secrets
import string

from django.db import IntegrityError, models, transaction

LETTERS = string.ascii_letters + string.digits


class Link(models.Model):
    # unique=True: the database itself refuses a repeated URL or a repeated code
    long_url = models.URLField(max_length=2000, unique=True)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    visits = models.IntegerField(default=0)

    def __str__(self):
        return self.code


def make_code():
    # 6 random letters/digits (62^6 = about 56 billion options)
    return "".join(secrets.choice(LETTERS) for _ in range(6))


def get_or_create_link(long_url):
    """Return (link, was_created). Same URL twice gives the same link."""
    old = Link.objects.filter(long_url=long_url).first()
    if old:
        return old, False

    for _ in range(10):
        try:
            with transaction.atomic():
                new = Link.objects.create(long_url=long_url, code=make_code())
            return new, True
        except IntegrityError:
            # Either the code was taken, or another request saved the same URL first.
            old = Link.objects.filter(long_url=long_url).first()
            if old:
                return old, False
            # otherwise the code was taken: loop and try a new code

    raise RuntimeError("Could not make a unique code")
