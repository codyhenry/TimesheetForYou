from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User


MANAGED_ROLES = (User.Role.NANNY, User.Role.OFFICE, User.Role.ADMIN)
MANAGED_ROLE_CHOICES = [
    (value, label) for value, label in User.Role.choices if value in MANAGED_ROLES
]


class DashboardManagedUserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Temporary password. The user must change it on next sign-in.",
        strip=False,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_active",
        ]
        widgets = {
            "email": forms.EmailInput,
        }

    role = forms.ChoiceField(choices=MANAGED_ROLE_CHOICES)

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        password = self.cleaned_data.pop("password")
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.force_password_change = True
        user.set_password(password)
        if commit:
            user.save()
        return user


class DashboardManagedUserUpdateForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text="Optional temporary password reset. If set, the user must change it on next sign-in.",
        strip=False,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_active",
            "force_password_change",
            "password",
        ]
        widgets = {
            "email": forms.EmailInput,
        }

    role = forms.ChoiceField(choices=MANAGED_ROLE_CHOICES)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        password = self.cleaned_data.pop("password", "")
        user = super().save(commit=False)
        if password:
            user.set_password(password)
            user.force_password_change = True
        user.is_staff = False if not user.is_superuser else user.is_staff
        if commit:
            user.save()
        return user
