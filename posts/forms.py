from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Изображение',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text", )