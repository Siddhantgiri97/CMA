from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async, async_to_sync
import json
# Create your models here.


class Customer(models.Model):
    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=12, null=True)
    email = models.CharField(max_length=50, null=True)
    profile_pic = models.ImageField(
        default="IMG_20201012_165549-1_vgzh5DR.png", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY = (
        ('Indoor', 'Indoor'),
        ('Outdoor', 'Outdoor'),
    )
    name = models.CharField(max_length=200, null=True)
    price = models.FloatField(null=True)
    category = models.CharField(max_length=200, null=True, choices=CATEGORY)
    description = models.CharField(max_length=200, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Out for delivery', 'Out for delivery'),
        ('Delivered', 'Delivered'),
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(
        max_length=200, null=True, choices=STATUS, default="Pending")
    note = models.CharField(max_length=2000, null=True)

    def __str__(self):
        return str(self.product)

    @staticmethod
    def give_order_details(order_id):
        instance = Order.objects.filter(id=order_id).first()
        data = {}
        data['id'] = instance.id
        data['status'] = instance.status

        progress_percentage = 0

        if instance.status == 'Pending':
            progress_percentage = 33
        elif instance.status == 'Out for delivery':
            progress_percentage = 66

        elif instance.status == 'Delivered':
            progress_percentage = 100

        data['progress'] = progress_percentage

        return data


@receiver(post_save, sender=Order)
def order_status_handler(sender, instance, created, **kwargs):
    if not created:
        channel_layer = get_channel_layer()
        data = {}
        data['id'] = instance.id
        data['status'] = instance.status

        progress_percentage = 0

        if instance.status == 'Pending':
            progress_percentage = 33
        elif instance.status == 'Out for delivery':
            progress_percentage = 66

        elif instance.status == 'Delivered':
            progress_percentage = 100

        data['progress'] = progress_percentage

        async_to_sync(channel_layer.group_send)(
            'order_%s' % instance.id, {
                'type': 'order_status',
                'value': json.dumps(data)
            }
        )
