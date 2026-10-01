from django.db import models


class Customer(models.Model):
    customer_id = models.CharField(max_length=8, primary_key=True)
    customer_name = models.CharField(max_length=20)
    phone_contact = models.CharField(max_length=10)
    email_address = models.EmailField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.customer_name