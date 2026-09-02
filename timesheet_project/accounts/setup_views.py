from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import AccountSetupCompleteForm, AccountSetupRequestForm
from .services import GENERIC_SETUP_REQUEST_MESSAGE, get_available_account_setup_token


def account_setup(request):
    token = request.POST.get("token") if request.method == "POST" else request.GET.get("token")
    token = token or ""
    setup_token = get_available_account_setup_token(token)
    complete_form = None
    completed_user_name = request.session.pop("account_setup_completed_user_name", "")

    if request.method == "POST" and request.POST.get("action") == "request":
        request_form = AccountSetupRequestForm(request.POST)
        if request_form.is_valid():
            request_form.save()
            messages.success(request, GENERIC_SETUP_REQUEST_MESSAGE)
            return redirect(reverse("account-setup-web"))
    else:
        request_form = AccountSetupRequestForm()

    if request.method == "POST" and request.POST.get("action") == "complete":
        complete_form = AccountSetupCompleteForm(request.POST)
        if complete_form.is_valid():
            completed_user = complete_form.save()
            request.session["account_setup_completed_user_name"] = (
                completed_user.get_full_name() or completed_user.username
            )
            return redirect(f"{reverse('account-setup-web')}?complete=1")
    elif token:
        complete_form = AccountSetupCompleteForm(initial={"token": token})
        if setup_token is None:
            complete_form.add_error("token", "Setup link is invalid or expired.")

    return render(
        request,
        "accounts/account_setup.html",
        {
            "complete_form": complete_form,
            "completed_user_name": completed_user_name,
            "request_form": request_form,
            "setup_token": setup_token,
        },
    )
