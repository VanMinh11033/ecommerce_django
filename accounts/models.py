from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    ward = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
    
    def __str__(self):
        return self.username
    
    @property
    def full_address(self):
        parts = [self.address, self.ward, self.district, self.city]
        return ', '.join([p for p in parts if p])
