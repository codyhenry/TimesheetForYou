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

    role = forms.ChoiceField(choices=MANAGED_ROLE_CHOICES)

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
            "email": forms.EmailInput(),
        }

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
    temporary_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text="Optional temporary password reset. If set, the user must change it on next sign-in.",
        strip=False,
    )

    role = forms.ChoiceField(choices=MANAGED_ROLE_CHOICES)

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
        ]
        widgets = {
            "email": forms.EmailInput(),
        }

    def clean_temporary_password(self):
        password = self.cleaned_data.get("temporary_password")
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        password = self.cleaned_data.get("temporary_password", "")
        user = super().save(commit=False)
        if password:
            user.set_password(password)
            user.force_password_change = True
        if commit:
            user.save()
        return user
