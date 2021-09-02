from django import forms
from django.db.models import fields
from .models import Word
class HomeForm(forms.Form):
    key_word = forms.CharField(max_length=20)

class InputForm(forms.Form):
    key_word = forms.CharField(max_length=20)


