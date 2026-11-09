
from datetime import datetime, time

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

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
    successful_payment_queryset = Payment.objects.filter(
        status="successful"
    )

    successful_payments = successful_payment_queryset.count()

    total_payments_received = successful_payment_queryset.aggregate(
        total=Sum("amount")
    )["total"] or 0

    # Monthly revenue: last 12 calendar months
    today = timezone.localdate()

    current_month_index = today.year * 12 + today.month - 1

    month_periods = []

    for offset in reversed(range(12)):
        month_index = current_month_index - offset
        year, month_zero_based = divmod(month_index, 12)
        month = month_zero_based + 1

        month_periods.append((year, month))

    first_year, first_month = month_periods[0]

    start_date = datetime(
        first_year,
        first_month,
        1,
    )

    next_month_index = current_month_index + 1
    end_year, end_month_zero_based = divmod(
        next_month_index, 12
    )

    end_date = datetime(
        end_year,
        end_month_zero_based + 1,
        1,
    )

    start_datetime = timezone.make_aware(
        datetime.combine(start_date.date(), time.min)
    )

    end_datetime = timezone.make_aware(
        datetime.combine(end_date.date(), time.min)
    )

    monthly_totals = (
        Payment.objects.filter(
            status="successful",
            processed_at__isnull=False,
            processed_at__gte=start_datetime,
            processed_at__lt=end_datetime,
        )
        .annotate(month=TruncMonth("processed_at"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    revenue_by_month = {
        (item["month"].year, item["month"].month): item["total"]
        for item in monthly_totals
    }

    monthly_revenue = []

    for year, month in month_periods:
        amount = revenue_by_month.get(
            (year, month), 0
        )

        monthly_revenue.append({
            "label": datetime(year, month, 1).strftime("%b '%y"),
            "amount": amount,
        })

    max_revenue = max(
        (item["amount"] for item in monthly_revenue),
        default=0,
    )

    for item in monthly_revenue:
        if max_revenue:
            item["height"] = round(
                float(item["amount"] / max_revenue) * 100
            )
        else:
            item["height"] = 0

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
        "monthly_revenue": monthly_revenue,
        "open_tickets": open_tickets,
    })

    return context
