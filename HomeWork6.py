class BankAccount:
    bank_name = "First National Bank"
    def __init__(self, account_holder:str, initial_balance:float = 0.0):
        self.account_holder = account_holder
        self.balance = initial_balance
        self.transactions = []
    def deposit(self, amount:float) -> None:
        if self.validate_amount():
            self.balance += amount
            self.transactions.append(f"+{amount}")
            print(f"Deposited. New Balance = {self.balance}")
        else:
            print("Invalid amount")
    def withdraw(self, amount:float) -> None:
        if self.validate_amount() and amount <= self.balance:
            self.balance -= amount
            self.transactions.append(f"-{amount}")
            print(f"Withdrawn. New Balance = {self.balance}")
        else:
            print("Invalid amount")
    def __str__(self) -> str:
        return f"Account Holder = {self.account_holder}, Balance = ${self.balance} "
    def change_bank_name(cls, new_name:str) -> None:
        cls.bank_name = new_name
    def validate_amount(amount:float) -> bool:
        if amount > 0:
            return
    def show_transactions(self) -> None:
        for x in self.transactions:
            print(f"Transactions History : {x}")

class SavingsAccount(BankAccount):
    def __init__(self, account_holder:str, initial_balance:float = 0.0, interest_rate:float = 0.01):
        super().__init__(account_holder, initial_balance)
        self.interest_rate = interest_rate
    def add_interest(self) -> None:
        interest = self.balance * self.interest_rate
        self.deposit(interest)
    def __str__(self) -> str:
        return f"Saving Acount - Account Holder: {self.account_holder}, Balance: {self.balance}, Interst Rate: {self.interest_rate} * 100%"
    
Account1 = BankAccount("Alice", 1000)
Account2 = BankAccount("Bob")
Account1.deposit(200)
Account1.withdraw(1500)
Account1.withdraw(100)
print(Account1)

BankAccount.change_bank_name("Global Trust Bank")

print("Is -50 valid?", BankAccount.validate_amount(-50))

savings = SavingsAccount("Charlie", 1000, 0.05)
savings.deposit(50)
savings.add_interest()
print(savings)
savings.show_transactions()