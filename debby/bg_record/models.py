from django.db import models
from user.models import CustomUserModel


class BGModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    time = models.DateTimeField(auto_now_add=True)
    glucose_val = models.IntegerField(blank=False)
    type = models.CharField(max_length=10,
                            choices=(
                                ('before', '餐前'),
                                ('after', '飯後'),
                            ),
                            )

    def __str__(self):
        return self.user.line_id
