"""Business logic. Several design and correctness issues are intentional."""
from models import CartLine


class ShoppingCart:
    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_code = None
        self.discounted_total = None

    def add_item(self, sku, quantity):
        if type(quantity) is not int or quantity <= 0: # fix
            return False

        product = self.repository.get_product(sku)
        if not product:
            print('Unknown product')
            return False

        existing = next((x for x in self.lines if x.sku == sku), None)

        combined_quantity = quantity + (existing.quantity if existing else 0) # fix

        #if product.stock < quantity: # defect
        if product.stock < combined_quantity: # fix
            print('Not enough stock')
            return False

        if existing:
            existing.quantity += quantity
        else:
            self.lines.append(CartLine(sku, product.name, product.price, quantity))

        return True

    def remove_item(self, sku, quantity=None):
        if quantity is not None and (type(quantity) is not int or quantity <= 0): # fix
            return False
        
        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    line.quantity -= quantity
                return True
        print('Item not found')
        return False

    def subtotal(self):
        return sum(line.unit_price * line.quantity for line in self.lines)

    def total(self):
        #if self.discounted_total is not None: # defect
        #    return self.discounted_total

        amount = self.subtotal() # fix

        if self.discount_code == 'WELCOME10':
            amount *= 0.9
        elif self.discount_code == 'STUDENT20':
            amount *= 0.8
        elif self.discount_code == 'SAVE15':
            amount -= 15

        return round(max(0, amount), 2)

    def apply_discount(self, code):
        #amount = self.total() # defect

        if code not in ('WELCOME10', 'STUDENT20', 'SAVE15', 'FREESHIP'):
            print('Invalid coupon')
            return False

        if code == 'FREESHIP':
            print('Shipping is free')

        self.discount_code = code # fix
        self.discounted_total = None

        return True

    def load(self):
        # defect: existing cart items are not cleared before loading

        self.lines.clear() # fix

        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)
    
    def save(self):
        self.repository.save_cart(self.user_id, self.lines)
