from django.urls import path

from .views import (
    api_login, api_signup, api_reset_password, api_reset_password_confirm,
    api_update_profile, api_change_password, api_logout
)

urlpatterns = [
    path('login/', api_login, name='api-login'),
    path('signup/', api_signup, name='api-signup'),
    path('reset-password/', api_reset_password, name='api-reset-password'),
    path('reset-password/confirm/', api_reset_password_confirm, name='api-reset-password-confirm'),
    path('profile/', api_update_profile, name='api-update-profile'),
    path('change-password/', api_change_password, name='api-change-password'),
    path('logout/', api_logout, name='api-logout'),
]
