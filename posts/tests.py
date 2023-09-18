from urllib.parse import urljoin
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse
from .models import Post, Group, Comment, Follow
from django.conf import settings
import os.path as path

BASE_DIR = settings.BASE_DIR

def get_test_urls(username=None, post_id=None, group_slug=None):
    urls = {'index':  reverse("index")}
    if username:
        urls["profile"] = reverse("profile", kwargs={"username": username})
    if post_id:
        urls["post"] = reverse("post", kwargs={"username": username, 'post_id': post_id})
    if group_slug:
        urls["group_posts"] = reverse("group_posts", kwargs={"slug": group_slug})
    return urls

class TestBase(TestCase):
    def setUp(self):
        self.auth_client = Client()
        self.nonauth_client = Client()

        self.username = "test"
        self.email = " user@test.com"
        self.password = "12345"

        self.user = User.objects.create(username=self.username, email=self.email)
        self.user.set_password(self.password)
        self.user.save()
        self.auth_client.login(username=self.username, password=self.password)

        self.group_title = 'Test Group'
        self.group_slug = 'group_test'
        self.group_description = 'This is a test group'

        self.group = Group.objects.create(
            title=self.group_title,
            slug=self.group_slug,
            description=self.group_description
        )

        self.text_first = "first text" 
        self.text_second = "second text"
        self.text_edit = "edit text"

        self.post = Post.objects.create(
            text=self.text_first, 
            author=self.user,
            group = self.group
        )

    def tearDown(self):
        cache.clear()

class TestPost(TestBase):
    def test_profile_page(self):
        urls = get_test_urls(self.username)
        response = self.auth_client.get(urls['profile'])

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(response.context["author"], self.user)

    def test_auth_client_create_post(self):
        response = self.auth_client.post(
            reverse("new_post"), 
            data={"text": self.text_second, 'group': self.group.id}
        )
        self.assertEqual(response.status_code, 302)

        first_post = Post.objects.first()
        self.assertEqual(first_post.text, self.text_second)

        urls = get_test_urls(self.username, first_post.id, self.group_slug)
        for url in urls.values():
            response = self.auth_client.get(url)
            if 'page' in response.context:
                self.assertEqual(response.context['page'][0], first_post)
            else:
                self.assertEqual(response.context['post'], first_post)

    def test_auth_client_edit_post(self):
        response = self.auth_client.post(
            reverse("post_edit", kwargs={"post_id": self.post.id, "username": self.username}),
            data={"text": self.text_edit, 'group': self.group.id},
        )
        self.assertEqual(response.status_code, 302)

        urls = get_test_urls(self.username, self.post.id, self.group_slug)
        for url in urls.values():
            response = self.auth_client.get(url)
            if 'page' in response.context:
                self.assertEqual(response.context['page'][0], self.post)
            else:
                self.assertEqual(response.context['post'], self.post)


    def test_nonauth_client_create_post(self):
        response = self.nonauth_client.get(reverse("new_post"))
        url = urljoin(reverse("login"), "?next=/new/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)


class TestErrorPages(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404_not_found(self):
        response = self.client.get('/non_existent_page/')
        self.assertEqual(response.status_code, 404)


class TestPostWithImage(TestBase):
    def test_post_has_image(self):
        with open(path.join(BASE_DIR, rf'tests\media\test.jpg'), 'rb') as img:
            response = self.auth_client.post(
                reverse("post_edit", kwargs={"post_id": self.post.id, "username": self.username}), 
                data={
                    "text": self.text_second,
                    'group': self.group.id,
                    'image': img
                }
        )
        self.assertEqual(response.status_code, 302)

        urls = get_test_urls(self.username, self.post.id, self.group_slug)
        for url in urls.values():
            response = self.auth_client.get(url)
            self.assertIn('<img', response.content.decode())

    def test_wrong_format_detection(self):
        with open(path.join(BASE_DIR, rf'tests\media\not_image.txt'), 'rb') as img:
            response = self.auth_client.post(
                reverse("new_post"), 
                data={
                    "text": self.text_second,
                    'group': self.group.id,
                    'image': img
                },
                follow=True
        )

        self.assertEqual(len(response.context['form'].errors), 1)


class TestPostCached(TestBase):
    def test_index_cached(self):
        response = self.auth_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.text_first)

        response = self.auth_client.post(
            reverse("new_post"), 
            data={"text": self.text_second, 'group': self.group.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.text_second)

        cache.clear()
        response = self.auth_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.text_second)


class TestFollowing(TestBase):
    def setUp(self):
        username = "test_author"
        email = username  + "@test.com"
        password = "12345"

        self.author = User.objects.create(username=username, email=email)
        self.author.set_password(password)
        self.author.save()
        super().setUp()

    def test_auth_client_following(self):
        self.assertFalse(Follow.objects.filter(user=self.user, author=self.author).exists())

        response = self.auth_client.get(reverse("profile_follow", kwargs={'username': self.author.username}))
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(Follow.objects.get(user=self.user, author=self.author))

        response = self.auth_client.get(reverse("profile_unfollow", kwargs={'username': self.author.username}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Follow.objects.filter(user=self.user, author=self.author).exists())

    def test_follow_index(self):
        text = 'Hello, my followers!'
        Post.objects.create(author=self.author, text=text)

        response = self.auth_client.get(reverse('follow_index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, text)

        response = self.auth_client.get(reverse("profile_follow", kwargs={'username': self.author.username}))
        self.assertEqual(response.status_code, 302)

        response = self.auth_client.get(reverse('follow_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, text)
        

class TestComment(TestBase):
    def test_auth_client_can_comment(self):
        comment_text = 'I can comment'

        response = self.auth_client.post(
            reverse(
                'add_comment', 
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            ),
            data={
                'text': comment_text
            },
        )

        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(post=self.post, author=self.user, text=comment_text)
        self.assertIsNotNone(comment)

    def test_nonauth_client_cant_comment(self):
        comment_text = 'I can comment'

        response = self.nonauth_client.post(
            reverse(
                'add_comment', 
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            ),
            data={
                'text': comment_text
            },
        )

        redir_url = urljoin(reverse("login"), f"?next=/{self.user.username}/{self.post.id}/comment")
        self.assertRedirects(response, redir_url)
        self.assertFalse(Comment.objects.filter(post=self.post, author=self.user, text=comment_text).exists())
