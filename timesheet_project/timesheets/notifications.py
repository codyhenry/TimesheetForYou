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


def send_sms_notification(phone_number, message, sns_client=None):
    """Send an SMS message through AWS SNS.

    When USE_SNS is false this is a safe no-op so reminder workflows can be
    tested or dry-run without sending external messages.
    """
    if not phone_number:
        raise ValueError("phone_number is required.")
    if not message:
        raise ValueError("message is required.")

    if not sns_notifications_enabled():
        return {
            "sent": False,
            "phone_number": phone_number,
            "message_id": "",
            "reason": "SNS notifications are disabled.",
        }

    client = sns_client or _build_sns_client()
    publish_kwargs = {
        "PhoneNumber": phone_number,
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
    return {
        "sent": True,
        "phone_number": phone_number,
        "message_id": response.get("MessageId", ""),
        "reason": "",
    }
