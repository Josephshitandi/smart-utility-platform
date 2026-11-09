
from django.urls import path

from .views import (
    SupportTicketListCreateView,
    SupportTicketDetailView,
    TicketMessageListCreateView,
)


urlpatterns = [
    path(
        "tickets/",
        SupportTicketListCreateView.as_view(),
        name="support-ticket-list-create",
    ),

    path(
        "tickets/<int:pk>/",
        SupportTicketDetailView.as_view(),
        name="support-ticket-detail",
    ),

    path(
        "tickets/<int:ticket_id>/messages/",
        TicketMessageListCreateView.as_view(),
        name="ticket-message-list-create",
    ),
]
