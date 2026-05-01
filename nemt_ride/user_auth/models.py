from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserRoles(models.Model):
    """I will add roles instead of string field to the user 
    since it is more efficient and we can easily add more 
    roles in the future if needed"""
    #id 1 admin
    #id 2 driver
    #id 3 rider
    # ... add more roles as we may need in future 
    role = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.role

class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Please provide an email address.")
        email = self.normalize_email(email)  #normalize here
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
    

class User(AbstractBaseUser, PermissionsMixin):

    id_user = models.AutoField(primary_key=True)
    email = models.EmailField(blank=False, max_length=75, unique=True)
    first_name = models.CharField(blank=True, max_length=50, default='', 
                                  verbose_name="First name", null=True)
    last_name = models.CharField(blank=True, max_length=50, default='', 
                                 verbose_name="Last name", null=True)
    phone_number = models.CharField(blank=True, max_length=20, default='', 
                                    verbose_name="Phone number", null=True)
    
    role = models.ForeignKey(UserRoles, on_delete=models.SET_DEFAULT, default=3,
                             related_name='users_role')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def get_short_name(self):
        return self.first_name

