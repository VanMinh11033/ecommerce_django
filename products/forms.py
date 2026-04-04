from django import forms
from .models import Product, Category, Brand, ProductImage, Review


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'brand', 'name', 'slug', 'description',
            'price', 'compare_price', 'stock', 'sku',
            'specifications', 'is_active', 'is_featured', 
            'is_bestseller', 'is_new'
        ]
        widgets = {
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_specifications(self):
        import json
        data = self.cleaned_data.get("specifications")

        if isinstance(data, dict):
            return data

        if data.strip() == "":
            return {}

        try:
            return json.loads(data)
        except Exception:
            raise forms.ValidationError("Specifications phải là JSON hợp lệ.")



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['parent', 'name', 'slug', 'description', 'image', 'is_active']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'slug', 'logo', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'is_primary', 'order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }