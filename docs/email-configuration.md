# Email Configuration

TimesheetForYou sends transactional email for account setup invites. Additional email flows, such as user-owned password reset and admin timesheet-submission notifications, are being developed in separate PRs and should be documented as production behavior only after those PRs merge.

## Required production settings

Production must use a real email backend. When `DEBUG=False`, the default backend is Django SMTP and `EMAIL_HOST` is required.

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=replace-with-smtp-user
EMAIL_HOST_PASSWORD=replace-with-smtp-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@timesheet.example.com
ACCOUNT_SETUP_BASE_URL=https://timesheet.example.com
```

`ACCOUNT_SETUP_BASE_URL` controls account setup invite links. It should be the public HTTPS URL for the Django app or the public account setup page host.

`SITE_BASE_URL` can be set as the general public app URL and currently acts as the default value for `ACCOUNT_SETUP_BASE_URL` when `ACCOUNT_SETUP_BASE_URL` is not provided.

`ADMIN_NOTIFICATION_EMAIL` is reserved for admin-facing email notifications. It is optional until the timesheet-submission notification feature is merged.

## Local development

Local development defaults to the console email backend when `DEBUG=True`, so emails are printed to the backend process output instead of being sent externally.

To inspect emails in tests or local experiments, use Django's locmem backend:

```env
EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@timesheet.local
SITE_BASE_URL=http://localhost:8000
ACCOUNT_SETUP_BASE_URL=http://localhost:8000
```

## Account setup email flow

1. An admin creates a user with first name, last name, email, phone, and role.
2. The app creates the user with an unusable password.
3. The app generates an expiring account setup token.
4. The app emails the setup link to the user's email address.
5. The user opens the link and chooses their username and password through the account setup flow.

Admins cannot set another user's password and cannot force a password reset.

## Planned email flows

The following settings and behaviors are planned or implemented in separate unmerged PRs. Treat them as pending until their PRs are merged into `main`.

### User-owned password reset

Planned behavior:

1. The user opens the password reset page.
2. The user enters their account email.
3. The response is always generic so the app does not reveal whether an email belongs to an account.
4. If an active account with a usable password exists, the app sends a reset link.
5. The user opens the link and chooses a new password.

Pending setup users with unusable passwords should use the account setup flow, not password reset.

### Timesheet submission notification

Planned behavior:

When a timesheet submission transaction commits successfully, the app emails `ADMIN_NOTIFICATION_EMAIL` with:

- nanny name
- week range
- status
- total hours
- late status
- dashboard link

If `ADMIN_NOTIFICATION_EMAIL` is blank, the notification is skipped. If email delivery fails, the submission remains saved and the error is logged.

## Deployment checklist

Before promoting a production release that sends account setup email:

- Confirm `DEBUG=False`.
- Confirm `EMAIL_HOST` is set.
- Confirm SMTP credentials are valid.
- Confirm `DEFAULT_FROM_EMAIL` uses an approved sender domain.
- Confirm `ACCOUNT_SETUP_BASE_URL` is the public HTTPS setup URL host.
- Create a test pending user and verify the setup link works from email.

After the password-reset and admin-notification PRs merge, also verify their end-to-end email flows and set `ADMIN_NOTIFICATION_EMAIL` to the intended office/admin inbox if timesheet-submission notifications should be enabled.
