from django.db import models

from home.storage import OverwriteStorage


class Fund(models.Model):
    code = models.CharField(db_index=True, max_length=6)
    name = models.CharField(max_length=100)
    is_focus = models.BooleanField()


class NetValue(models.Model):
    date = models.DateField(db_index=True)
    fund = models.ForeignKey(Fund)
    nav = models.DecimalField(max_digits=8, decimal_places=4)
    acc_nav = models.DecimalField(max_digits=8, decimal_places=4)
    adjust_nav = models.DecimalField(max_digits=8, decimal_places=4, null=True)


class FundFile(models.Model):
    date = models.DateField()
    fetch_time = models.DateTimeField()
    provider = models.CharField(max_length=20)
    file = models.FileField(upload_to='fund-file/', storage=OverwriteStorage())
