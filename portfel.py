import tracemalloc
tracemalloc.start()

class Portfel:
    def __init__(self, symbol: str) -> None:
        self.symbol = {}
    
    def add_owner(self,user_id: int, quantity : int, price : float):
        self.symbol[user_id] = {'quantity':[quantity], 'price': [price]}
        print(self.symbol)
  
    def buy_share(self, user_id : int, quantity: int, price : float):
        try:
            self.symbol[user_id]['quantity'].append(quantity)
            self.symbol[user_id]['price'].append(price)
            print(self.symbol[user_id])
            for i in range(len(self.symbol[user_id]['quantity'])):
                if self.symbol[user_id]['quantity'][0] == 0:
                    del self.symbol[user_id]['quantity'][0]
                    del self.symbol[user_id]['price'][0]
        except Exception as ex:
            self.symbol[user_id] = {'quantity':[quantity], 'price': [price]}


    def sell_share(self, user_id : int, quantity: int, price: float):
        if len(self.symbol[user_id]['quantity']) == 1:
            if quantity > self.symbol[user_id]['quantity'][0]:
                print('Cannot sell more shares than you own')
            else:
                self.symbol[user_id]['quantity'][0] -= quantity
                
                if self.symbol[user_id]['quantity'][0] == 0:                    
                    del self.symbol[user_id]['quantity'][0]
                    del self.symbol[user_id]['price'][0]
                print('Shares sold successfully')
        else:
            total_quantity = sum(self.symbol[user_id]['quantity'])
            if quantity > total_quantity:
                print('Cannot sell more shares than you own')
            else:
                for i in range(len(self.symbol[user_id]['quantity'])):
                    if quantity == 0:
                        break
                    if self.symbol[user_id]['quantity'][i] >= quantity:
                        self.symbol[user_id]['quantity'][i] -= quantity
                        quantity = 0
                    else:
                        quantity -= self.symbol[user_id]['quantity'][i]
                        self.symbol[user_id]['quantity'][i] = 0
                if quantity != 0:
                    print('Cannot sell more shares than you own')
                else:
                    for i in range(len(self.symbol[user_id]['quantity'])):
                        if self.symbol[user_id]['quantity'][0] == 0:
                            del self.symbol[user_id]['quantity'][0]
                            del self.symbol[user_id]['price'][0]
                    print('Shares sold successfully')

    def get_info(self, user_id: int):
        quantity = self.symbol[user_id]['quantity']
        price = self.symbol[user_id]['price']

        counter = []

        for i in range(len(quantity)):
            counter.append(quantity[i] * price[i])
        
        
        print(f'''
        Общая стоимость портфеля: {sum(counter)}

        Структура портфеля:       {self.symbol[user_id]['quantity']}''')
        return [counter, self.symbol[user_id]['quantity']]

# average_price = sum(quantity[i] * price[i] for i in range(len(quantity)))/sum(quantity)
# Усерднённая цена акций:   {round(average_price, 3)}
sber = Portfel(symbol = 'SBER')
# 1
# sber.add_owner(1111, 100, 100)
# sber.add_owner(2222, 100, 100)
# 2
sber.buy_share(1111, 100, 200)
# sber.buy_share(2222, 100, 200)
sber.get_info(1111)
# 3
sber.buy_share(1111, 400, 400)
# sber.buy_share(2222, 400, 400)
# 4
sber.sell_share(1111, 498, 170)
# sber.sell_share(2222, 200, 170)
sber.get_info(1111)
# sber.get_info(2222)

# yndx = Portfel(symbol = 'YNDX')
# # 1
# yndx.add_owner(1111, 100, 1000)
# yndx.add_owner(2222, 100, 1000)
# # yndx0
# yndx.buy_share(1111, 100, 2000)
# yndx.buy_share(2222, 100, 2000)
# yndx.get_info(1111)
# # yndx0
# yndx.buy_share(1111, 400, 4000)
# yndx.buy_share(2222, 400, 4000)
# # yndx0
# yndx.sell_share(1111, 590, 1700)
# yndx.sell_share(2222, 200, 1700)
# yndx.get_info(1111)
# yndx.get_info(2222)

# Отображение статистики
current, peak = tracemalloc.get_traced_memory()
print(f"Использовано {current / 10**6} МБ, пиковое значение {peak / 10**6} МБ")
tracemalloc.stop()