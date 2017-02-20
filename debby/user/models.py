from django.db import models
from django.contrib.auth.models import AbstractUser, User, Group, PermissionsMixin, BaseUserManager

# Custom user model for line.
# example from https://www.caktusgroup.com/blog/2013/08/07/migrating-custom-user-model-django/

class CustomUserManager(BaseUserManager):
    def create_user(self, line_id, password=None):
        if not line_id:
            raise ValueError('no line_id was given. failed to create user.')
        else:
            user = self.model(
                line_id = line_id,
            )

            user.set_password(password)
            user.save(using=self._db)
            return user

    def create_superuser(self, line_id, password=None):
        superuser = self.model(
            line_id = line_id,
            is_superuser = True,
            is_staff = True,
        )

        superuser.set_password(password)
        superuser.save(using=self._db)
        return superuser

class CustomUserModel(AbstractUser, PermissionsMixin):
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=55)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    line_id = models.CharField(max_length=33, primary_key=True)
    line_token = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    groups = models.ForeignKey(Group, blank=True, default=0)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'line_id'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


    def __str__(self):
        return self.line_id
