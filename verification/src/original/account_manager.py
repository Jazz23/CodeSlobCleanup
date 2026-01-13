class AccountManager:
    def __init__(self, balance):
        self.balance = balance
        self.version = "1.0.0" # Slob: unused attribute

    def get_tax_rate(self, region):
        # Slob: Should be private, region logic is messy
        if region == "US":
            return 0.1
        else:
            return 0.2

    def apply_interest(self, region):
        # Slob: Redundant variable assignment
        rate = self.get_tax_rate(region)
        current_balance = self.balance
        interest = current_balance * rate
        self.balance = current_balance + interest
        return self.balance
