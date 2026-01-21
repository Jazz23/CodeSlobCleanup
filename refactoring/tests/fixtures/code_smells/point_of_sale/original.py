import random
import string
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Protocol

# --- From pos/order.py ---

class OrderStatus(Enum):
    """Order status"""

    OPEN = auto()
    PAID = auto()
    CANCELLED = auto()
    DELIVERED = auto()
    RETURNED = auto()


@dataclass
class Order:
    customer_id: int = 0
    customer_name: str = ""
    customer_address: str = ""
    customer_postal_code: str = ""
    customer_city: str = ""
    customer_email: str = ""
    items: list[str] = field(default_factory=list)
    quantities: list[int] = field(default_factory=list)
    prices: list[int] = field(default_factory=list)
    _status: OrderStatus = OrderStatus.OPEN
    id: str = ""

    def create_line_item(self, name: str, quantity: int, price: int) -> None:
        self.items.append(name)
        self.quantities.append(quantity)
        self.prices.append(price)

    def set_status(self, status: OrderStatus):
        self._status = status

# --- From pos/payment.py ---

class PaymentServiceConnectionError(Exception):
    """Custom error that is raised when we couldn't connect to the payment service."""


class OrderRepository(Protocol):
    def find_order(self, order_id: str) -> Order:
        ...

    def compute_order_total_price(self, order: Order) -> int:
        ...


class StripePaymentProcessor:
    def __init__(self, system: OrderRepository):
        self.connected = False
        self.system = system

    def connect_to_service(self, url: str) -> None:
        print(f"Connecting to payment processing service at url {url}... done!")
        self.connected = True

    def process_payment(self, order_id: str) -> None:
        if not self.connected:
            raise PaymentServiceConnectionError()
        order = self.system.find_order(order_id)
        total_price = self.system.compute_order_total_price(order)
        print(
            f"Processing payment of ${(total_price / 100):.2f}, reference: {order.id}."
        )

# --- From pos/system.py ---

def generate_id(length: int = 6) -> str:
    """Helper function for generating an id."""
    return "".join(random.choices(string.ascii_uppercase, k=length))


class POSSystem:
    def __init__(self):
        self.payment_processor = StripePaymentProcessor(self)
        self.orders: dict[str, Order] = {}

    def setup_payment_processor(self, url: str) -> None:
        self.payment_processor.connect_to_service(url)

    def register_order(self, order: Order):
        order.id = generate_id()
        self.orders[order.id] = order

    def find_order(self, order_id: str) -> Order:
        return self.orders[order_id]

    def compute_order_total_price(self, order: Order) -> int:
        total = 0
        for i in range(len(order.prices)):
            total += order.quantities[i] * order.prices[i]
        return total

    def process_order(self, order: Order) -> None:
        self.payment_processor.process_payment(order.id)
        order.set_status(OrderStatus.PAID)
        print("Shipping order to customer.")
