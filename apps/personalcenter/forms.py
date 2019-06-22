from django import forms
from .models import *


class ProductForm(forms.ModelForm):
    class Meta:
        model = MyNote
        fields = ['author', 'title', 'content']
