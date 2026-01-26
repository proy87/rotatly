"""
URL configuration for rotatly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

from apps.accounts.views import (
    LoginView, SignupView, ResetView, ResetEmailView, NewPasswordView, 
    ProfileView, LeaderboardView, PrivacyView
)

urlpatterns = [
    path('admin-r/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('reset/', ResetView.as_view(), name='reset'),
    path('reset-email/', ResetEmailView.as_view(), name='reset-email'),
    path('reset-password/', NewPasswordView.as_view(), name='reset-password'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('api/auth/', include('apps.accounts.urls')),
    path('', include('apps.game.urls')),
]
