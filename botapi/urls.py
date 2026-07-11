from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="bot-login"),
    path("profile/", views.profile_view, name="bot-profile"),
    path("payment/request/", views.payment_request_view, name="bot-payment-request"),
    path("payment/<int:request_id>/submit/", views.payment_submit_view, name="bot-payment-submit"),
    path("admin/statistics/", views.admin_statistics_view, name="bot-admin-statistics"),
    path("admin/pending-payments/", views.admin_pending_payments_view, name="bot-admin-pending-payments"),
    path("payment/approve/", views.payment_approve_view, name="bot-payment-approve"),
    path("payment/reject/", views.payment_reject_view, name="bot-payment-reject"),
]
