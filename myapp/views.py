from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Post, Comment, Profile, UserFollowing, Activity
from .forms import ProfileUpdateForm, PostForm
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth.models import User
import re

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    following_users = request.user.following.values_list('following_user', flat=True)
    posts = Post.objects.filter(author__in=following_users).order_by('-created_at')
    
    suggested_users = User.objects.exclude(
        id__in=following_users
    ).exclude(
        id=request.user.id
    ).annotate(
        num_followers=Count('followers')
    ).order_by('-num_followers')[:5]
    
    trending_hashtags = Post.objects.values('hashtags').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    recent_activity = Activity.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:5]
    
    context = {
        'posts': posts,
        'suggested_users': suggested_users,
        'trending_hashtags': trending_hashtags,
        'recent_activity': recent_activity,
    }
    return render(request, 'home.html', context)

def explore(request):
    popular_hashtags = Post.objects.values('hashtags').annotate(
        count=Count('id')
    ).order_by('-count')[:12]
    
    context = {
        'popular_hashtags': popular_hashtags,
    }
    return render(request, 'explore.html', context)

def hashtag_posts(request, hashtag):
    posts = Post.objects.filter(
        hashtags__icontains=hashtag
    ).order_by('-created_at')
    
    context = {
        'hashtag': hashtag,
        'posts': posts,
    }
    return render(request, 'hashtag_posts.html', context)

def hashtag_search(request):
    query = request.GET.get('query', '')
    if query.startswith('#'):
        query = query[1:]
    
    hashtags = Post.objects.values('hashtags').annotate(
        count=Count('id')
    ).filter(
        hashtags__icontains=query
    ).order_by('-count')[:12]
    
    context = {
        'popular_hashtags': hashtags,
        'query': query,
    }
    return render(request, 'explore.html', context)

def search_users(request):
    query = request.GET.get('query', '')
    users = User.objects.filter(
        username__icontains=query
    ).exclude(
        id=request.user.id
    ) if query else []
    
    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'search_users.html', context)

def profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    user_posts = profile_user.posts.all().order_by('-created_at')
    
    is_following = False
    if request.user.is_authenticated:
        is_following = UserFollowing.objects.filter(
            user=request.user,
            following_user=profile_user
        ).exists()
    
    context = {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'is_following': is_following,
    }
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile', user_id=request.user.id)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'form': form,
    }
    return render(request, 'edit_profile.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            # Create activity
            Activity.objects.create(
                user=request.user,
                message=f'You created a new post'
            )
            
            messages.success(request, 'Your post has been created!')
            return redirect('home')
    else:
        form = PostForm()
    
    return redirect('home')

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
    }
    return render(request, 'post_detail.html', context)

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'edit_post.html', context)

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('home')
    return render(request, 'delete_post.html', {'post': post})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment = Comment.objects.create(
                post=post,
                user=request.user,
                content=content
            )
            
            # Create activity
            Activity.objects.create(
                user=request.user,
                message=f'You commented on {post.author.username}\'s post'
            )
            
            if request.user != post.author:
                Activity.objects.create(
                    user=post.author,
                    message=f'{request.user.username} commented on your post'
                )
            
            messages.success(request, 'Comment added!')
    return redirect('post_detail', post_id=post_id)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    post_id = comment.post.id
    comment.delete()
    messages.success(request, 'Comment deleted!')
    return redirect('post_detail', post_id=post_id)

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
        
        # Create activity only when liking (not unliking)
        if request.user != post.author:
            Activity.objects.create(
                user=post.author,
                message=f'{request.user.username} liked your post'
            )
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)
        
        # Create activity only when liking (not unliking)
        if request.user != comment.user:
            Activity.objects.create(
                user=comment.user,
                message=f'{request.user.username} liked your comment'
            )
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if request.user != user_to_follow:
        UserFollowing.objects.get_or_create(
            user=request.user,
            following_user=user_to_follow
        )
        
        # Create activity
        Activity.objects.create(
            user=user_to_follow,
            message=f'{request.user.username} started following you'
        )
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)
    UserFollowing.objects.filter(
        user=request.user,
        following_user=user_to_unfollow
    ).delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def user_followers(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    followers = profile_user.followers.all()
    
    context = {
        'title': 'Followers',
        'profile_user': profile_user,
        'users': [uf.user for uf in followers],
        'empty_message': f'{profile_user.username} has no followers yet.',
    }
    return render(request, 'followers_following.html', context)

def user_following(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    following = profile_user.following.all()
    
    context = {
        'title': 'Following',
        'profile_user': profile_user,
        'users': [uf.following_user for uf in following],
        'empty_message': f'{profile_user.username} is not following anyone yet.',
    }
    return render(request, 'followers_following.html', context)
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                # Create profile if it doesn't exist
                profile = Profile.objects.create(user=user)
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile will be automatically created by the signal
            login(request, user)
            return redirect('home')  # Redirect to home after successful registration
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')



def landing_view(request):
    posts = Post.objects.all().order_by('-created_at')[:10]  # Get 10 most recent posts
    return render(request, 'landing.html', {'posts': posts})

