from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Core functionality
    path('', views.landing_view, name='landing'),
    path('home', views.home, name='home'),
    path('explore/', views.explore, name='explore'),

    path('hashtag/<str:hashtag>/', views.hashtag_posts, name='hashtag_posts'),
    path('hashtag-search/', views.hashtag_search, name='hashtag_search'),
    path('search-users/', views.search_users, name='search_users'),
    
    # Profile related
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('followers/<int:user_id>/', views.user_followers, name='user_followers'),
    path('following/<int:user_id>/', views.user_following, name='user_following'),
    
    # Post related
    path('create-post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    
    # Comment related
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('delete-comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('like-comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    
    # Follow/unfollow
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
]