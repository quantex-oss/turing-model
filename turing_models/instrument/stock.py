class stock:
    def __init__(self, stock_price, quantity, multiplier=100):
        self.stock_price = stock_price
        self.quantity = quantity
        self.multiplier = multiplier  # A股的合约乘数是100

    def price(self):
        """"计算一手股票的价格"""
        return self.stock_price * self.multiplier

    def value(self):
        """"计算持仓现值"""
        return self.stock_price * self.multiplier * self.quantity

    def delta(self):
        return self.multiplier
