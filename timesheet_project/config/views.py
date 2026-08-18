from django.http import JsonResponse
from django.shortcuts import redirect, render


def root_redirect(request):
    return redirect("dashboard-index")


def custom_404(request, exception=None):
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Not found."}, status=404)
    return render(request, "404.html", status=404)
