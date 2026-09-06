import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .password_reset_forms import UserPasswordResetCompleteForm, UserPasswordResetRequestForm
from .password_reset_services import GENERIC_PASSWORD_RESET_MESSAGE, send_user_password_reset_email

logger = logging.getLogger(__name__)


def password_reset_request(request):
    form = UserPasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if user is not None:
            try:
                send_user_password_reset_email(user)
            except Exception:
                logger.exception("Failed to send password reset email for user %s", user.pk)
        messages.success(request, GENERIC_PASSWORD_RESET_MESSAGE)
        return redirect(reverse("password-reset-request-web"))

    return render(request, "accounts/password_reset_request.html", {"form": form})


def password_reset_confirm(request, uidb64, token):
    initial = {"uidb64": uidb64, "token": token}
    completed = False

    if request.method == "POST":
        form_data = request.POST.copy()
        form_data["uidb64"] = uidb64
        form_data["token"] = token
        form = UserPasswordResetCompleteForm(form_data)
        if form.is_valid():
            form.save()
            completed = True
    else:
        form = UserPasswordResetCompleteForm(initial=initial)

    return render(
        request,
        "accounts/password_reset_confirm.html",
        {
            "completed": completed,
            "form": form,
        },
    )
