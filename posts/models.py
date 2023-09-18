from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()

class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    class Meta():
        ordering = ['-pub_date', '-id']
        
    text = models.TextField(max_length=200)
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, related_name="post")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

class Comment(models.Model):
    class Meta():
        ordering = ['-created']

    text = models.TextField(max_length=200)
    created = models.DateTimeField("date createded", auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return self.text
    
class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")