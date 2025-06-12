from django import forms
from .models import Product, ColorVariant, Category
from django.core.exceptions import ValidationError

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'original_price', 'offer_percent', 'stock', 'image']  # Removed 'discount_price'

class ColorVariantForm(forms.ModelForm):
    class Meta:
        model = ColorVariant
        fields = ['color_name', 'color_code', 'main_image', 'stock', 'price_override']


'''
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'offer_percent']

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Category.objects.filter(name__iexact=name)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(f"Category '{name}' already exists.")
        return name
'''


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'offer_percent']

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')  # current category
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        # Exclude the current category (self.instance)
        qs = Category.objects.filter(name__iexact=name)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise forms.ValidationError(f"Category '{name}' already exists.")
        return name

