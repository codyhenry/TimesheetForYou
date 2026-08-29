from django import forms

from accounts.models import User
from accounts.services import generate_pending_username


MANAGED_ROLES = (User.Role.NANNY, User.Role.OFFICE, User.Role.ADMIN)
MANAGED_ROLE_CHOICES = [
    (value, label) for value, label in User.Role.choices if value in MANAGED_ROLES
]


class DashboardManagedUserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(choices=MANAGED_ROLE_CHOICES)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, max_length=30)

    class Meta:
        model = User
        fields = [
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

    def clean_first_name(self):
        value = self.cleaned_data.get("first_name", "").strip()
        if not value:
            raise forms.ValidationError("First name is required.")
        return value

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "").strip()
        if not value:
            raise forms.ValidationError("Last name is required.")
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = generate_pending_username()
        user.is_staff = False
        user.is_superuser = False
        user.force_password_change = False
        user.set_unusable_password()
        if commit:
            user.save()
        return user


class DashboardManagedUserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(choices=MANAGED_ROLE_CHOICES)
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False, max_length=30)

    class Meta:
        model = User
        fields = [
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

    def clean_first_name(self):
        value = self.cleaned_data.get("first_name", "").strip()
        if not value:
            raise forms.ValidationError("First name is required.")
        return value

    def clean_last_name(self):
        value = self.cleaned_data.get("last_name", "").strip()
        if not value:
            raise forms.ValidationError("Last name is required.")
        return value
