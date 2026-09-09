from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User
from .services import get_available_account_setup_token, send_setup_email_for_identifier


class AccountSetupRequestForm(forms.Form):
    identifier = forms.CharField(
        label="Email or phone",
        max_length=254,
        help_text="Enter the email address or phone number your admin used to create your account.",
    )

    def save(self):
        send_setup_email_for_identifier(self.cleaned_data["identifier"])


class AccountSetupCompleteForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput)
    username = forms.CharField(max_length=User._meta.get_field("username").max_length)
    password = forms.CharField(widget=forms.PasswordInput, strip=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_token_resolved = False
        self._setup_token = None

    def _get_setup_token(self):
        if not self._setup_token_resolved:
            raw_token = self.data.get(self.add_prefix("token")) or self.data.get("token")
            self._setup_token = get_available_account_setup_token(raw_token)
            self._setup_token_resolved = True
        return self._setup_token

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        username_field = User._meta.get_field("username")
        for validator in username_field.validators:
            validator(username)

        matching_users = User.objects.filter(username__iexact=username)
        setup_token = self._get_setup_token()
        if setup_token is not None:
            matching_users = matching_users.exclude(pk=setup_token.user_id)
        if matching_users.exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        setup_token = self._get_setup_token()
        if setup_token is None:
            self.add_error("token", "Setup link is invalid or expired.")
            return cleaned_data

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")
            return cleaned_data

        if password:
            validate_password(password, setup_token.user)

        cleaned_data["setup_token"] = setup_token
        return cleaned_data

    def save(self):
        setup_token = self.cleaned_data["setup_token"]
        user = setup_token.user
        user.username = self.cleaned_data["username"]
        user.set_password(self.cleaned_data["password"])
        user.force_password_change = False
        user.save(update_fields=["username", "password", "force_password_change"])
        setup_token.mark_used()
        return user
