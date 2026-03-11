"""Mock Stripe SDK for subscription/payment testing."""
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class MockStripeError(Exception):
    pass


class CardError(MockStripeError):
    def __init__(self, message="Card declined", code="card_declined"):
        self.code = code
        super().__init__(message)


class MockStripeObject(dict):
    """Dict that also supports attribute access (like Stripe objects)."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


def _stripe_obj(data: dict) -> MockStripeObject:
    return MockStripeObject(data)


class Customer:
    _store = {}

    @classmethod
    def create(cls, **kwargs) -> MockStripeObject:
        cid = f"cus_test_{len(cls._store) + 1:03d}"
        obj = _stripe_obj({"id": cid, "email": kwargs.get("email", ""), "name": kwargs.get("name", ""), "metadata": kwargs.get("metadata", {})})
        cls._store[cid] = obj
        return obj

    @classmethod
    def retrieve(cls, customer_id: str) -> MockStripeObject:
        if customer_id in cls._store:
            return cls._store[customer_id]
        return _stripe_obj({"id": customer_id, "email": "test@test.com"})

    @classmethod
    def modify(cls, customer_id: str, **kwargs) -> MockStripeObject:
        obj = cls.retrieve(customer_id)
        obj.update(kwargs)
        return obj

    @classmethod
    def _reset(cls):
        cls._store.clear()


class PaymentMethod:
    @classmethod
    def attach(cls, payment_method_id: str, **kwargs) -> MockStripeObject:
        return _stripe_obj({"id": payment_method_id, "customer": kwargs.get("customer", ""), "type": "card"})

    @classmethod
    def list(cls, **kwargs) -> MockStripeObject:
        return _stripe_obj({"data": [
            _stripe_obj({"id": "pm_test_001", "type": "card", "card": {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2028}})
        ]})


class Subscription:
    _store = {}

    @classmethod
    def create(cls, **kwargs) -> MockStripeObject:
        sid = f"sub_test_{len(cls._store) + 1:03d}"
        now = int(time.time())
        obj = _stripe_obj({
            "id": sid,
            "customer": kwargs.get("customer", ""),
            "status": "active",
            "current_period_start": now,
            "current_period_end": now + 30 * 86400,
            "items": _stripe_obj({"data": [_stripe_obj({"price": _stripe_obj({"id": kwargs.get("items", [{}])[0].get("price", "price_test")})})]}),
            "default_payment_method": kwargs.get("default_payment_method", "pm_test_001"),
            "cancel_at_period_end": False,
        })
        cls._store[sid] = obj
        return obj

    @classmethod
    def retrieve(cls, sub_id: str) -> MockStripeObject:
        if sub_id in cls._store:
            return cls._store[sub_id]
        return _stripe_obj({"id": sub_id, "status": "active"})

    @classmethod
    def modify(cls, sub_id: str, **kwargs) -> MockStripeObject:
        obj = cls.retrieve(sub_id)
        obj.update(kwargs)
        return obj

    @classmethod
    def delete(cls, sub_id: str) -> MockStripeObject:
        obj = cls.retrieve(sub_id)
        obj["status"] = "canceled"
        return obj

    @classmethod
    def _reset(cls):
        cls._store.clear()


class Webhook:
    @classmethod
    def construct_event(cls, payload: bytes, sig_header: str, secret: str) -> MockStripeObject:
        """Always succeeds in tests — returns the payload as an event."""
        import json as _json
        data = _json.loads(payload)
        return _stripe_obj(data)


class WebhookEvents:
    """Factory for realistic Stripe webhook events."""

    @staticmethod
    def payment_succeeded(customer_id: str, amount: int = 2999, subscription_id: str = "sub_test_001") -> dict:
        return {
            "type": "invoice.payment_succeeded",
            "data": {"object": {
                "customer": customer_id,
                "subscription": subscription_id,
                "amount_paid": amount,
                "currency": "usd",
                "status": "paid",
                "payment_intent": f"pi_test_{int(time.time())}",
            }}
        }

    @staticmethod
    def payment_failed(customer_id: str, subscription_id: str = "sub_test_001") -> dict:
        return {
            "type": "invoice.payment_failed",
            "data": {"object": {
                "customer": customer_id,
                "subscription": subscription_id,
                "amount_due": 2999,
                "currency": "usd",
                "status": "open",
            }}
        }

    @staticmethod
    def subscription_updated(subscription_id: str, status: str = "active") -> dict:
        return {
            "type": "customer.subscription.updated",
            "data": {"object": {
                "id": subscription_id,
                "status": status,
                "cancel_at_period_end": status == "canceled",
                "current_period_start": int(time.time()),
                "current_period_end": int(time.time()) + 30 * 86400,
            }}
        }

    @staticmethod
    def subscription_deleted(subscription_id: str) -> dict:
        return {
            "type": "customer.subscription.deleted",
            "data": {"object": {
                "id": subscription_id,
                "status": "canceled",
            }}
        }


# Reset function for test cleanup
def reset_all():
    Customer._reset()
    Subscription._reset()


# Module-level error class
error = type("error", (), {"CardError": CardError, "StripeError": MockStripeError})()
