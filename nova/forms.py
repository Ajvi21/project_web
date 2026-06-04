"""
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    ChatbotFaq,
    ContactRequest,
    NewsComment,
    NewsPost,
    Project,
    ProjectComment,
    ProjectImage,
    ProjectReview,
)

PROJECT_STAR_CHOICES = [(i, f'{i} Yll{"" if i == 1 else "e"}') for i in range(1, 6)]

class NewsPostForm(forms.ModelForm):
    class Meta:
        model = NewsPost
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Titulli i lajmit',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Shkruaj përmbajtjen e lajmit...',
            }),
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 5:
            raise forms.ValidationError('Titulli duhet të ketë të paktën 5 karaktere.')
        return title


class NewsCommentForm(forms.ModelForm):
    class Meta:
        model = NewsComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Shkruaj komentin tënd...',
            }),
        }

    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content) < 10:
            raise forms.ValidationError('Komenti duhet të ketë të paktën 10 karaktere.')
        return content


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ky email është përdorur tashmë.')
        return email



class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'location',
            'category',
            'status',
            'year',
            'floor_area_m2',
            'cover',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emri i projektit',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Përshkrimi i projektit...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiranë, Durrës, ...',
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900}),
            'floor_area_m2': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'cover': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year is not None and year < 1900:
            raise forms.ValidationError('Viti nuk mund të jetë para 1900.')
        return year

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 3:
            raise forms.ValidationError('Emri i projektit duhet të ketë të paktën 3 karaktere.')
        return name


class ProjectImageForm(forms.ModelForm):
    class Meta:
        model = ProjectImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Përshkrim opsional i fotos',
            }),
        }


class ProjectReviewForm(forms.ModelForm):
    class Meta:
        model = ProjectReview
        fields = ['stars']
        widgets = {
            'stars': forms.Select(
                choices=PROJECT_STAR_CHOICES,
                attrs={'class': 'form-select'},
            ),
        }

    def clean_stars(self):
        stars = self.cleaned_data.get('stars')
        if stars is None or stars < 1 or stars > 5:
            raise forms.ValidationError('Vlerësimi duhet të jetë midis 1 dhe 5 yje.')
        return stars


class ProjectCommentForm(forms.ModelForm):
    class Meta:
        model = ProjectComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Shkruaj komentin tënd...',
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 5:
            raise forms.ValidationError('Komenti duhet të ketë të paktën 5 karaktere.')
        return content


# -----------------------------------------------------------------------------
# Contact form -- new ModelForm for the Nova-specific ContactRequest model.
# -----------------------------------------------------------------------------

class ContactRequestForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ['name', 'surname', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shkruaj emrin',
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shkruaj mbiemrin',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+355 ...',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Për çfarë dëshiron të na kontaktosh?',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Shkruaj mesazhin tënd këtu...',
            }),
        }

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Mesazhi duhet të ketë të paktën 10 karaktere.')
        return message

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Emri duhet të ketë të paktën 2 karaktere.')
        return name



class ChatbotFaqForm(forms.ModelForm):
    class Meta:
        model = ChatbotFaq
        fields = ['question', 'keywords', 'answer', 'is_featured']
