from unittest.mock import patch

from django.db import DatabaseError, connection
from django.test import TestCase, TransactionTestCase

from links.models import Link


class NormalFlowTest(TestCase):
    def test_create_redirect_and_stats(self):
        # 1. make a short link
        answer = self.client.post("/", {"long_url": "https://example.com/hello"})
        self.assertEqual(answer.status_code, 200)
        link = Link.objects.get(long_url="https://example.com/hello")

        # 2. visit it: we must be sent to the original URL
        answer = self.client.get("/" + link.code + "/")
        self.assertEqual(answer.status_code, 302)
        self.assertEqual(answer["Location"], "https://example.com/hello")

        # 3. stats page shows 1 visit
        self.client.get("/" + link.code + "/")
        answer = self.client.get("/stats/" + link.code + "/")
        self.assertEqual(answer.status_code, 200)
        link.refresh_from_db()
        self.assertEqual(link.visits, 2)
        self.assertContains(answer, "Total visits")


class FailureTest(TestCase):
    def test_bad_url_text(self):
        answer = self.client.post("/", {"long_url": "not a url"})
        self.assertEqual(answer.status_code, 400)
        self.assertEqual(Link.objects.count(), 0)

    def test_empty_url(self):
        answer = self.client.post("/", {"long_url": ""})
        self.assertEqual(answer.status_code, 400)

    def test_wrong_scheme(self):
        answer = self.client.post("/", {"long_url": "javascript:alert(1)"})
        self.assertEqual(answer.status_code, 400)
        answer = self.client.post("/", {"long_url": "ftp://example.com/file"})
        self.assertEqual(answer.status_code, 400)

    def test_private_address_blocked(self):
        for bad in ["http://localhost/x", "http://127.0.0.1/x", "http://192.168.1.5/x"]:
            answer = self.client.post("/", {"long_url": bad})
            self.assertEqual(answer.status_code, 400)
        self.assertEqual(Link.objects.count(), 0)

    def test_unknown_code(self):
        self.assertEqual(self.client.get("/nope12/").status_code, 404)
        self.assertEqual(self.client.get("/stats/nope12/").status_code, 404)

    def test_database_failure_gives_503_not_fake_success(self):
        with patch("links.views.Link.objects.filter", side_effect=DatabaseError):
            answer = self.client.get("/abc123/")
        self.assertEqual(answer.status_code, 503)


class DuplicateAndUniqueTest(TestCase):
    def test_same_url_twice_gives_same_link(self):
        self.client.post("/", {"long_url": "https://example.com/a"})
        self.client.post("/", {"long_url": "https://example.com/a"})
        self.assertEqual(Link.objects.count(), 1)

    def test_different_urls_get_different_codes(self):
        for number in range(50):
            self.client.post("/", {"long_url": "https://example.com/page" + str(number)})
        codes = list(Link.objects.values_list("code", flat=True))
        self.assertEqual(len(codes), 50)
        self.assertEqual(len(set(codes)), 50)

    def test_code_clash_is_retried(self):
        # Force make_code to give "aaaaaa" twice, then "bbbbbb".
        # The second URL must NOT get "aaaaaa".
        with patch("links.models.make_code", side_effect=["aaaaaa", "aaaaaa", "bbbbbb"]):
            self.client.post("/", {"long_url": "https://example.com/one"})
            self.client.post("/", {"long_url": "https://example.com/two"})
        one = Link.objects.get(long_url="https://example.com/one")
        two = Link.objects.get(long_url="https://example.com/two")
        self.assertEqual(one.code, "aaaaaa")
        self.assertEqual(two.code, "bbbbbb")


class PersistenceTest(TransactionTestCase):
    def test_data_survives_restart(self):
        self.client.post("/", {"long_url": "https://example.com/keep"})
        link = Link.objects.get(long_url="https://example.com/keep")
        self.client.get("/" + link.code + "/")

        # "Restart": close the database connection. Django opens a new one
        # on the next query, reading everything back from the file on disk.
        connection.close()

        link = Link.objects.get(long_url="https://example.com/keep")
        self.assertEqual(link.visits, 1)
        answer = self.client.get("/" + link.code + "/")
        self.assertEqual(answer.status_code, 302)
