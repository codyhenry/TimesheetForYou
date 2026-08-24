from django.conf import settings


class NotificationConfigurationError(RuntimeError):
    pass


def sns_notifications_enabled():
    return bool(getattr(settings, "USE_SNS", False))


def _build_sns_client():
    region_name = getattr(settings, "AWS_SNS_REGION_NAME", "") or getattr(settings, "AWS_REGION", "")
    if not region_name:
        raise NotificationConfigurationError(
            "AWS_SNS_REGION_NAME or AWS_REGION must be set when USE_SNS=True."
        )

    import boto3

    return boto3.client("sns", region_name=region_name)


def _not_sent_result(phone_number, reason):
    return {
        "sent": False,
        "phone_number": phone_number,
        "message_id": "",
        "reason": reason,
    }


def send_sms_notification(phone_number, message, sns_client=None):
    """Send an SMS message through AWS SNS.

    When USE_SNS is false this is a safe no-op so reminder workflows can be
    tested or dry-run without sending external messages. Publish/configuration
    failures are returned as non-sent results so scheduled reminder runs can
    continue processing remaining recipients.
    """
    normalized_phone_number = str(phone_number or "").strip()
    if not normalized_phone_number:
        raise ValueError("phone_number is required.")
    if not message:
        raise ValueError("message is required.")

    if not sns_notifications_enabled():
        return _not_sent_result(
            normalized_phone_number,
            "SNS notifications are disabled.",
        )

    try:
        client = sns_client or _build_sns_client()
        publish_kwargs = {
            "PhoneNumber": normalized_phone_number,
            "Message": message,
        }
        sender_id = getattr(settings, "SNS_SENDER_ID", "")
        if sender_id:
            publish_kwargs["MessageAttributes"] = {
                "AWS.SNS.SMS.SenderID": {
                    "DataType": "String",
                    "StringValue": sender_id,
                }
            }

        response = client.publish(**publish_kwargs)
    except Exception as exc:  # pragma: no cover - exact SNS exception types vary by botocore version.
        return _not_sent_result(
            normalized_phone_number,
            f"SNS publish failed: {exc}",
        )

    return {
        "sent": True,
        "phone_number": normalized_phone_number,
        "message_id": response.get("MessageId", ""),
        "reason": "",
    }
