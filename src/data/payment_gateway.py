from src.domain.gateways.payment_gateway import PaymentGateway


class MockPaymentGateway(PaymentGateway):
    def charge(self, amount: float, payment_details: dict) -> bool:
        return True
