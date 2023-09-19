from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Follow
from .forms import PostForm, CommentForm
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page
from django.core.cache import cache


def user_is_follower(user, author):
    return user.is_authenticated and Follow.objects.filter(user=user, author=author).exists()


def get_cached_index_page():
    data = cache.get('index_page')
    if data is None:
        data = Post.objects.select_related('author', 'group').all()
        cache.set('index_page', data, 20)
    return data


def index(request):
    post_list = get_cached_index_page()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.post.select_related('author', 'group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


def profile(request, username):
    author = get_object_or_404(get_user_model(), username=username)
    post_list = author.post.select_related('author', 'group').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {
            'page': page,
            'paginator': paginator,
            'author': author,
            'following': user_is_follower(request.user, author)
        }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    form = CommentForm()
    return render(
        request,
        'post.html',
        {
            'post': post,
            'author': author,
            'form': form,
            'following': user_is_follower(request.user, author),
            'comments': post.comments.all()
        },
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse('index'))
    return render(request, 'new_post.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    if request.user.username == username:
        post = get_object_or_404(Post, id=post_id, author__username=username)
        if request.method == 'POST':
            form = PostForm(request.POST, files=request.FILES, instance=post)
            if form.is_valid():
                form.save()
                return redirect('post', username=username, post_id=post_id)
        else:
            form = PostForm(instance=post)
        return render(request, 'new_post.html', {'form': form, 'post': post})
    return redirect('post', username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(reverse('post', kwargs={'username': username, 'post_id': post_id}))


@login_required
def follow_index(request):
    post_list = Post.objects.select_related('author', 'group').filter(author__following__user=request.user).all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
)


def profile_following(request, username, follow: bool = True):
    user = request.user
    author = get_object_or_404(get_user_model(), username=username)
    if user != author:
        if follow and not user_is_follower(user, author):
            Follow.objects.create(user=user, author=author)
        elif not follow and user_is_follower(user, author):
            Follow.objects.get(user=user, author=author).delete()
    return redirect('profile', username=username)


@login_required
def profile_follow(request, username):
    return profile_following(request, username)


@login_required
def profile_unfollow(request, username):
    return profile_following(request, username, False)