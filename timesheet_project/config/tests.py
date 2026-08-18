from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class RootAndErrorRoutingTests(TestCase):
    def test_root_redirects_to_dashboard(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("dashboard-index"))

    def test_browser_unknown_route_uses_themed_404(self):
        response = self.client.get("/not-a-real-browser-page/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "This page wandered off during nap time.", status_code=404)
        self.assertContains(response, "Go to Dashboard", status_code=404)
        self.assertContains(response, reverse("dashboard-index"), status_code=404)

    def test_api_unknown_route_returns_json_404(self):
        response = self.client.get("/api/not-a-real-endpoint/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"detail": "Not found."})
