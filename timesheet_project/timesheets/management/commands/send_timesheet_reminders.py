from datetime import date

from django.core.management.base import BaseCommand, CommandError

from timesheets.reminders import send_due_timesheet_reminders
from timesheets.services import SATURDAY_WEEKDAY


class Command(BaseCommand):
    help = "Send SNS reminders to nannies who have not submitted a due timesheet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--week-start",
            help="Saturday week start date in YYYY-MM-DD format. Defaults to the latest due week.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List reminder recipients without sending SMS messages.",
        )

    def handle(self, *args, **options):
        week_start_date = None
        if options.get("week_start"):
            try:
                week_start_date = date.fromisoformat(options["week_start"])
            except ValueError as exc:
                raise CommandError("--week-start must use YYYY-MM-DD format.") from exc
            if week_start_date.weekday() != SATURDAY_WEEKDAY:
                raise CommandError("--week-start must be a Saturday week start date.")

        summary = send_due_timesheet_reminders(
            week_start_date=week_start_date,
            dry_run=options["dry_run"],
        )

        mode = "Dry run" if options["dry_run"] else "Sent"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode} reminders for {summary['week_start_date']} - {summary['week_end_date']}: "
                f"{summary['sent_count']} sent, {summary['recipient_count']} eligible."
            )
        )

        for result in summary["results"]:
            status = "sent" if result["sent"] else result["reason"]
            self.stdout.write(
                f"- {result['nanny_name']} ({result['phone_number']}): "
                f"{result['timesheet_status']} / {status}"
            )
