from django.db import models

class ExampleModel(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class YourModel(ExampleModel):
    additional_field = models.IntegerField()

    def __str__(self):
        return self.name