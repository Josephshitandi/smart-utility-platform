
from django.db.models import Sum

from accounts.models import User
from meters.models import Meter
from billing.models import Bill
from payments.models import Payment
from support.models import SupportTicket


def dashboard_callback(request, context):
    # User statistics
    total_customers = User.objects.filter(
        role="customer",
        is_superuser=False,
    ).count()

    total_users = User.objects.count()

    # Meter statistics
    total_meters = Meter.objects.count()

    active_meters = Meter.objects.filter(
        status="active"
    ).count()

    # Billing statistics
    total_bills = Bill.objects.count()

    outstanding_bills = Bill.objects.filter(
        status__in=["pending", "overdue"]
    ).count()

    outstanding_amount = Bill.objects.filter(
        status__in=["pending", "overdue"]
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0

    # Payment statistics
    successful_payments = Payment.objects.filter(
        status="successful"
    ).count()

    total_payments_received = Payment.objects.filter(
        status="successful"
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0

    # Support statistics
    open_tickets = SupportTicket.objects.exclude(
        status__in=["resolved", "closed"]
    ).count()

    context.update({
        "total_users": total_users,
        "total_customers": total_customers,
        "total_meters": total_meters,
        "active_meters": active_meters,
        "total_bills": total_bills,
        "outstanding_bills": outstanding_bills,
        "outstanding_amount": outstanding_amount,
        "successful_payments": successful_payments,
        "total_payments_received": total_payments_received,
        "open_tickets": open_tickets,
    })

    return context
