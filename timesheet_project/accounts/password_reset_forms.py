from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

User = get_user_model()


class UserPasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

    def get_user(self):
        email = self.cleaned_data["email"].strip()
        return (
            User.objects.filter(is_active=True, email__iexact=email)
            .exclude(email="")
            .first()
        )


class UserPasswordResetCompleteForm(forms.Form):
    uidb64 = forms.CharField(widget=forms.HiddenInput)
    token = forms.CharField(widget=forms.HiddenInput)
    password = forms.CharField(widget=forms.PasswordInput, strip=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, strip=False)

    def clean(self):
        cleaned_data = super().clean()
        uidb64 = cleaned_data.get("uidb64")
        token = cleaned_data.get("token")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        user = None
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id, is_active=True)
        except Exception:
            user = None

        if user is None or not user.has_usable_password() or not default_token_generator.check_token(user, token):
            self.add_error("token", "Password reset link is invalid or expired.")
            return cleaned_data

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")
            return cleaned_data

        if password:
            validate_password(password, user)

        cleaned_data["user"] = user
        return cleaned_data

    def save(self):
        user = self.cleaned_data["user"]
        user.set_password(self.cleaned_data["password"])
        user.force_password_change = False
        user.save(update_fields=["password", "force_password_change"])
        return user
