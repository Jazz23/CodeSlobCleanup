class AccountManager:
    def __init__(self, balance):
        self.balance = balance

    def _get_tax_rate(self, region):
        """Refactored: Made private and simplified."""
        return 0.1 if region == "US" else 0.2

    def apply_interest(self, region):
        """Refactored: Removed redundant variables."""
        interest = self.balance * self._get_tax_rate(region)
        self.balance += interest
        return self.balance
