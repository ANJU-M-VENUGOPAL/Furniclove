from decimal import Decimal

def calculate_refund_for_item(order, order_item):
    subtotal = order.subtotal
    total_discount = order.discount
    item_total = order_item.price * order_item.quantity
    if subtotal > 0:
        proportional_discount = (item_total / subtotal) * total_discount
    else:
        proportional_discount = Decimal("0.00")
    refund_amount = item_total - proportional_discount
    return refund_amount.quantize(Decimal('0.01'))