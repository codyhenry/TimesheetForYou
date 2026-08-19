from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class SafeUserAdminTests(TestCase):
    def setUp(self):
        self.staff_admin = User.objects.create_user(
            username="staff-admin",
            password="StrongTestPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        user_content_type = ContentType.objects.get_for_model(User)
        user_permissions = Permission.objects.filter(
            content_type=user_content_type,
            codename__in={"add_user", "change_user", "view_user", "delete_user"},
        )
        group_content_type = ContentType.objects.get_for_model(Group)
        group_permissions = Permission.objects.filter(
            content_type=group_content_type,
            codename__in={"view_group", "change_group"},
        )
        self.staff_admin.user_permissions.add(*user_permissions, *group_permissions)

        self.nanny = User.objects.create_user(
            username="nanny-user",
            password="StrongTestPass123!",
            role=User.Role.NANNY,
            first_name="Nanny",
            last_name="User",
        )
        self.developer_superuser = User.objects.create_superuser(
            username="developer-superuser",
            password="StrongTestPass123!",
            email="developer@example.com",
        )
        self.client.force_login(self.staff_admin)

    def test_non_superuser_staff_changelist_hides_superusers(self):
        response = self.client.get(reverse("admin:accounts_user_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.nanny.username)
        self.assertNotContains(response, self.developer_superuser.username)

    def test_non_superuser_staff_change_form_hides_privilege_fields(self):
        response = self.client.get(
            reverse("admin:accounts_user_change", args=[self.nanny.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "id_is_staff")
        self.assertNotContains(response, "id_is_superuser")
        self.assertNotContains(response, "id_groups")
        self.assertNotContains(response, "id_user_permissions")

    def test_non_superuser_staff_cannot_open_superuser_change_form_directly(self):
        response = self.client.get(
            reverse("admin:accounts_user_change", args=[self.developer_superuser.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_non_superuser_staff_cannot_grant_staff_or_superuser_with_post(self):
        response = self.client.post(
            reverse("admin:accounts_user_change", args=[self.nanny.pk]),
            {
                "username": self.nanny.username,
                "password": self.nanny.password,
                "first_name": self.nanny.first_name,
                "last_name": self.nanny.last_name,
                "email": self.nanny.email,
                "is_active": "on",
                "is_staff": "on",
                "is_superuser": "on",
                "role": User.Role.ADMIN,
                "phone": "555-0100",
                "force_password_change": "on",
                "date_joined_0": self.nanny.date_joined.date().isoformat(),
                "date_joined_1": self.nanny.date_joined.time().strftime("%H:%M:%S"),
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.nanny.refresh_from_db()
        self.assertFalse(self.nanny.is_staff)
        self.assertFalse(self.nanny.is_superuser)
        self.assertEqual(self.nanny.role, User.Role.ADMIN)
        self.assertEqual(self.nanny.phone, "555-0100")
        self.assertTrue(self.nanny.force_password_change)

    def test_non_superuser_staff_cannot_delete_users_in_admin(self):
        response = self.client.get(
            reverse("admin:accounts_user_delete", args=[self.nanny.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_non_superuser_staff_cannot_open_group_admin_even_with_group_permissions(self):
        response = self.client.get(reverse("admin:auth_group_changelist"))

        self.assertEqual(response.status_code, 403)
