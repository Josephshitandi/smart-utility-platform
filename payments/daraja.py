
import base64
import re
from decimal import Decimal, InvalidOperation

import requests

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


class DarajaError(Exception):
    """Raised when a Daraja API operation fails."""


def get_access_token():
    """
    Retrieve and cache a Safaricom Daraja OAuth access token.
    """

    cache_key = "daraja_access_token"

    access_token = cache.get(cache_key)

    if access_token:
        return access_token

    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    if not consumer_key or not consumer_secret:
        raise DarajaError(
            "Daraja Consumer Key or Consumer Secret is missing."
        )

    url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate"

    try:
        response = requests.get(
            url,
            params={"grant_type": "client_credentials"},
            auth=(consumer_key, consumer_secret),
            headers={"Accept": "application/json"},
            timeout=settings.MPESA_API_TIMEOUT,
        )

        response.raise_for_status()
        data = response.json()

    except requests.Timeout as exc:
        raise DarajaError(
            "Daraja authentication request timed out."
        ) from exc

    except requests.RequestException as exc:
        raise DarajaError(
            "Unable to communicate with Daraja authentication service."
        ) from exc

    except ValueError as exc:
        raise DarajaError(
            "Daraja returned an invalid authentication response."
        ) from exc

    access_token = data.get("access_token")

    if not access_token:
        raise DarajaError(
            "Daraja authentication response did not contain an access token."
        )

    try:
        expires_in = int(data.get("expires_in", 3599))
    except (TypeError, ValueError):
        expires_in = 3599

    cache_timeout = max(expires_in - 60, 1)

    cache.set(
        cache_key,
        access_token,
        timeout=cache_timeout,
    )

    return access_token


def normalize_mpesa_phone(phone_number):
    """
    Normalize a Kenyan phone number to 254XXXXXXXXX.
    """

    if not phone_number:
        raise DarajaError("M-Pesa phone number is required.")

    phone = re.sub(r"[\s\-()+]", "", str(phone_number))

    if phone.startswith("0"):
        phone = "254" + phone[1:]

    if not re.fullmatch(r"254[17]\d{8}", phone):
        raise DarajaError(
            "Invalid Kenyan M-Pesa number. "
            "Use a number such as 0712345678 or 254712345678."
        )

    return phone


def generate_stk_password():
    """
    Generate the STK Push password and timestamp.
    """

    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY

    if not shortcode or not passkey:
        raise DarajaError(
            "Daraja Shortcode or Passkey is missing."
        )

    timestamp = timezone.localtime().strftime("%Y%m%d%H%M%S")

    password_string = f"{shortcode}{passkey}{timestamp}"

    password = base64.b64encode(
        password_string.encode("utf-8")
    ).decode("utf-8")

    return password, timestamp


def initiate_stk_push(
    *,
    phone_number,
    amount,
    account_reference,
    transaction_description="Utility payment",
):
    """
    Send an STK Push request to Safaricom Daraja.

    This only initiates the payment request.
    It does not confirm that payment has been completed.
    """

    shortcode = settings.MPESA_SHORTCODE
    callback_url = settings.MPESA_CALLBACK_URL

    if not shortcode:
        raise DarajaError("Daraja Shortcode is missing.")

    if not callback_url or not callback_url.startswith("https://"):
        raise DarajaError(
            "A publicly accessible HTTPS Daraja callback URL is required."
        )

    if not account_reference:
        raise DarajaError("Account reference is required.")

    account_reference = str(account_reference).strip()

    if len(account_reference) > 12:
        raise DarajaError(
            "Account reference cannot exceed 12 characters."
        )

    transaction_description = str(
        transaction_description
    ).strip()[:13]

    phone = normalize_mpesa_phone(phone_number)

    try:
        payment_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise DarajaError("Invalid payment amount.") from exc

    if not payment_amount.is_finite() or payment_amount <= 0:
        raise DarajaError(
            "Payment amount must be greater than zero."
        )

    if payment_amount != payment_amount.to_integral_value():
        raise DarajaError(
            "M-Pesa STK Push requires an amount in whole Kenya shillings."
        )

    amount = int(payment_amount)

    password, timestamp = generate_stk_password()

    access_token = get_access_token()

    url = (
        f"{settings.MPESA_BASE_URL}"
        "/mpesa/stkpush/v1/processrequest"
    )

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": settings.MPESA_TRANSACTION_TYPE,
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_description,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.MPESA_API_TIMEOUT,
        )

        response.raise_for_status()
        data = response.json()

    except requests.Timeout as exc:
        raise DarajaError(
            "Daraja STK Push request timed out."
        ) from exc

    except requests.RequestException as exc:
        raise DarajaError(
            "Unable to communicate with Daraja STK Push service."
        ) from exc

    except ValueError as exc:
        raise DarajaError(
            "Daraja returned an invalid STK Push response."
        ) from exc

    if str(data.get("ResponseCode")) != "0":
        raise DarajaError(
            data.get(
                "ResponseDescription",
                "Safaricom rejected the STK Push request.",
            )
        )

    checkout_request_id = data.get("CheckoutRequestID")
    merchant_request_id = data.get("MerchantRequestID")

    if not checkout_request_id or not merchant_request_id:
        raise DarajaError(
            "Daraja response did not contain the required request identifiers."
        )

    return {
        "merchant_request_id": merchant_request_id,
        "checkout_request_id": checkout_request_id,
        "response_code": data.get("ResponseCode"),
        "response_description": data.get("ResponseDescription", ""),
        "customer_message": data.get("CustomerMessage", ""),
    }

def query_stk_push(checkout_request_id):
    """
    Query Safaricom for the status of an STK Push transaction.

    A successful query response does not itself mean the
    customer paid. Inspect ResultCode before processing payment.
    """

    if not checkout_request_id:
        raise DarajaError("CheckoutRequestID is required.")

    shortcode = settings.MPESA_SHORTCODE

    if not shortcode:
        raise DarajaError("Daraja Shortcode is missing.")

    password, timestamp = generate_stk_password()
    access_token = get_access_token()

    url = (
        f"{settings.MPESA_BASE_URL}"
        "/mpesa/stkpushquery/v1/query"
    )

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.MPESA_API_TIMEOUT,
        )

        response.raise_for_status()
        data = response.json()

    except requests.Timeout as exc:
        raise DarajaError(
            "Daraja STK Query request timed out."
        ) from exc

    except requests.RequestException as exc:
        raise DarajaError(
            "Unable to communicate with Daraja STK Query service."
        ) from exc

    except ValueError as exc:
        raise DarajaError(
            "Daraja returned an invalid STK Query response."
        ) from exc

    return data
