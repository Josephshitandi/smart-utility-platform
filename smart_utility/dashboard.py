from datetime import date, datetime, time

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from accounts.models import User
from meters.models import Meter
from billing.models import Bill
from payments.models import Payment
from support.models import SupportTicket


def dashboard_callback(request, context):

    # --------------------------------------------------
    # USER STATISTICS
    # --------------------------------------------------

    total_customers = User.objects.filter(
        role="customer",
        is_superuser=False,
    ).count()

    total_users = User.objects.count()

    # --------------------------------------------------
    # METER STATISTICS
    # --------------------------------------------------

    total_meters = Meter.objects.count()

    active_meters = Meter.objects.filter(
        status="active",
    ).count()

    # --------------------------------------------------
    # BILLING STATISTICS
    # --------------------------------------------------

    total_bills = Bill.objects.count()

    outstanding_bills = Bill.objects.filter(
        status__in=["pending", "overdue"],
    ).count()

    outstanding_amount = (
        Bill.objects.filter(
            status__in=["pending", "overdue"],
        ).aggregate(
            total=Sum("amount"),
        )["total"] or 0
    )

    # --------------------------------------------------
    # PAYMENT STATISTICS
    # --------------------------------------------------

    successful_payments = Payment.objects.filter(
        status="successful",
    ).count()

    total_payments_received = (
        Payment.objects.filter(
            status="successful",
        ).aggregate(
            total=Sum("amount"),
        )["total"] or 0
    )

    # --------------------------------------------------
    # MONTHLY REVENUE - LAST 12 MONTHS
    # --------------------------------------------------

    current_month = timezone.localdate().replace(day=1)

    months = []

    for offset in range(11, -1, -1):
        month_index = (
            current_month.year * 12
            + current_month.month - 1
            - offset
        )

        year, month_zero_based = divmod(month_index, 12)

        months.append(
            date(year, month_zero_based + 1, 1)
        )

    start_date = months[0]

    next_month_index = (
        current_month.year * 12
        + current_month.month
    )

    end_year, end_month_zero_based = divmod(
        next_month_index,
        12,
    )

    end_date = date(
        end_year,
        end_month_zero_based + 1,
        1,
    )

    start_datetime = timezone.make_aware(
        datetime.combine(start_date, time.min)
    )

    end_datetime = timezone.make_aware(
        datetime.combine(end_date, time.min)
    )

    revenue_records = (
        Payment.objects.filter(
            status="successful",
            processed_at__gte=start_datetime,
            processed_at__lt=end_datetime,
        )
        .annotate(
            month=TruncMonth("processed_at"),
        )
        .values("month")
        .annotate(
            amount=Sum("amount"),
        )
        .order_by("month")
    )

    revenue_by_month = {
        record["month"].strftime("%Y-%m"): record["amount"]
        for record in revenue_records
    }

    monthly_amounts = [
        revenue_by_month.get(month.strftime("%Y-%m"), 0)
        for month in months
    ]

    maximum_revenue = max(monthly_amounts, default=0)

    monthly_revenue = []

    for month, amount in zip(months, monthly_amounts):

        if maximum_revenue:
            height = float(amount / maximum_revenue * 100)
        else:
            height = 0

        monthly_revenue.append({
            "label": month.strftime("%b %y"),
            "amount": amount,
            "height": round(height, 2),
        })

    # --------------------------------------------------
    # CUSTOMER SUPPORT STATISTICS
    # --------------------------------------------------

    open_tickets = SupportTicket.objects.exclude(
        status__in=["resolved", "closed"],
    ).count()

    # --------------------------------------------------
    # DASHBOARD CONTEXT
    # --------------------------------------------------

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

        "monthly_revenue": monthly_revenue,

        "open_tickets": open_tickets,
    })

    return context