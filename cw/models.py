from django.db import models

# Create your models here.
class News(models.Model):
    new_title = models.TextField()
    new_content = models.TextField()
    count_word=models.IntegerField(default=0)
    new_simliarity = models.IntegerField(default=0)

class Word(models.Model):
    key_word = models.CharField(max_length=20)