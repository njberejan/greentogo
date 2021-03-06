import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import Subscription
from core.stripe import stripe

endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
logger = logging.getLogger('django')
User = get_user_model()

handlers = {}


def handle_event(event_name):
    def handler_decorator(func):
        handlers[event_name] = func
        return func

    return handler_decorator


@require_POST
@csrf_exempt
def stripe_webhook(request):
    payload = request.body.decode("utf-8")
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    logger.info(payload)

    # Do something with event
    if event.type in handlers:
        handlers[event.type](event)

    return HttpResponse(status=200)


@handle_event('customer.subscription.deleted')
def handle_customer_subscription_deleted(event):
    event_sub = event.data.object

    subscription = Subscription.objects.filter(stripe_id=event_sub.id).first()
    if not subscription:
        logger.warn(
            "Subscription {} not found for customer.subscription.deleted webhook".
            format(event_sub.id)
        )
        return

    subscription.sync_with_stripe(event_sub)


@handle_event('customer.subscription.updated')
def handle_subscription_updated(event):
    """When a subscription is updated, update it in our DB."""
    event_sub = event.data.object

    subscription = Subscription.objects.filter(stripe_id=event_sub.id).first()
    if not subscription:
        logger.warn(
            "Subscription {} not found for customer.subscription.updated webhook".
            format(event_sub.id)
        )
        return

    subscription.sync_with_stripe(event_sub)


@handle_event('invoice.payment_succeeded')
def handle_invoice_payment_succeeded(event):
    """When an invoice payment is successful, update the subscription ends_at and status."""
    # TODO send an email to customer
    invoice = event.data.object
    customer = User.objects.filter(stripe_id=invoice.customer).first()
    if not customer:
        logger.warn(
            "Customer {} not found for invoice.payment_succeeded webhook".format(invoice.customer)
        )
        return

    if not invoice.lines.data:
        return
    for line in invoice.lines.data:
        if line.id.startswith("sub_"):
            subscription = Subscription.objects.filter(stripe_id=line.id).first()
            if not subscription:
                logger.warn(
                    "Subscription {} not found for invoice.payment_succeeded webhook".
                    format(line.id)
                )
            subscription.sync_with_stripe()


@handle_event('invoice.payment_failed')
def handle_invoice_payment_failed(event):
    """When an invoice payment fails, let the customer know and update their subscription (how?)"""
    # TODO send an email to customer
    invoice = event.data.object
    customer = User.objects.filter(stripe_id=invoice.customer).first()
    if not customer:
        logger.warn(
            "Customer {} not found for invoice.payment_failed webhook".format(invoice.customer)
        )
        return

    if not invoice.lines.data:
        return
    for line in invoice.lines.data:
        if line.id.startswith("sub_"):
            subscription = Subscription.objects.filter(stripe_id=line.id).first()
            if not subscription:
                logger.warn(
                    "Subscription {} not found for invoice.payment_failed webhook".format(line.id)
                )
            subscription.sync_with_stripe()
