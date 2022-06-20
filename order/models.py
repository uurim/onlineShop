from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from coupon.models import Coupon
from shop.models import Product

import hashlib
from .iamport import payments_prepare, find_transaction

# class Order(models.Model):
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#     email = models.EmailField()
#     address = models.CharField(max_length=250)
#     postal_code = models.CharField(max_length=20)
#     city = models.CharField(max_length=100)
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now=True)
#     paid = models.BooleanField(default=False)
#
#     coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT,
#                                related_name='order_coupon', null=True, blank=True)
#     discount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100000)])
#
#     class Meta:
#         ordering = ['-created']
#
#     def __str__(self):
#         return 'Order {}'.format(self.id)
#
#     def get_total_product(self):
#         return sum(item.get_item_price() for item in self.items.all())
#
#     def get_total_price(self):
#         total_product = self.get_total_product()
#         return total_product - self.discount
#
# # 주문에 포함된 정보 담기 위한 모델
# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name = 'item')
# 주문 정보 저장 모델
class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT,
                               related_name='order_coupon', null=True, blank=True)
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100000)])


    class Meta:
        ordering=['-created']

    def __str__(self):
        return 'Order {}'.format(self.id)

    def get_total_product(self):
        return sum(item.get_item_price() for item in self.items.all())

    def get_total_price(self):
        total_product = self.get_total_product()
        return total_product - self.discount


# 주문에 포함된 제품 정보 담기 위해 만드는 모델
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.id)

    def get_item_price(self):
        return self.price * self.quantity


class OrderTransactionManager(models.Manager):
    print("OrderTransactionManager가 실행되었습니다.")
    def create_new(self, order, amount, success=None, transaction_status=None):

        print('merchant_order_id...')

        if not order:
            raise ValueError("주문 오류")

        #해시 함수를 사용해 merchant_order_id 생성
        order_hash = hashlib.sha1(str(order.id).encode('utf-8')).hexdigest()
        email_hash = str(order.email).split("@")[0]
        final_hash = hashlib.sha1((order_hash+email_hash).encode('utf-8')).hexdigest()[:10]
        merchant_order_id = "%s"%(final_hash)

        print('merchant_order_id?', merchant_order_id)
        payments_prepare(merchant_order_id, amount)

        #self.model은 OrderTransaction을 의미함
        transaction = self.model(
            order = order,
            merchant_order_id = merchant_order_id,
            amount=amount
        )

        print('merchant_order_id?', merchant_order_id)
        if success is not None:
            transaction.success = success
            transaction.transaction_status = transaction_status

        try :
            transaction.save()
        except Exception as e :
            print("save error", e)

        return transaction.merchant_order_id

    def get_transaction(self, merchant_order_id):
        result = find_transaction(merchant_order_id)
        if result['status'] == 'paid':
            print('merchant_order_id if result', merchant_order_id)
            return result
        else :
            return None


class OrderTransaction(models.Model):
    order = models.ForeignKey(Order, on_delete = models.CASCADE)
    merchant_order_id = models.CharField(max_length=120, null=True, blank=True)
    transaction_id = models.CharField(max_length=120, null=True, blank=True)
    amount = models.PositiveIntegerField(default=0)
    transaction_status = models.CharField(max_length=220, null=True, blank = True)
    type = models.CharField(max_length=120, blank=True)
    created = models.DateTimeField(auto_now_add=True, auto_now=False)

    objects = OrderTransactionManager()

    def __str__(self):
        return str(self.order.id)

    class Meta:
        ordering = ['-created']

# 결제 검증 함수
def order_payment_validation(sender, instance, created, *args, **kwargs):
    print("order_payment_validation이 실행되었습니다.")
    if instance.transaction_id:
        import_transaction = OrderTransaction.objects.get_transaction(
            merchant_order_id=instance.merchant_order_id)
        merchant_order_id=import_transaction['merchant_order_id']
        imp_id = import_transaction['imp_id']
        amount = import_transaction['amount']


        local_transaction = OrderTransaction.objects.filter(merchant_order_id=merchant_order_id,
                                                            transaction_id = imp_id, amount=amount).exists()

        if not import_transaction or not local_transaction:
            raise ValueError("비정상 거래입니다.")

from django.db.models.signals import post_save
post_save.connect(order_payment_validation, sender=OrderTransaction)
