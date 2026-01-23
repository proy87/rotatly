import json
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .models import Gamer

User = get_user_model()


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({'error': message}, status=status)


def _read_payload(request) -> dict:
    if request.POST:
        return request.POST.dict()
    raw = request.body
    if not raw:
        return {}
    try:
        return json.loads(raw.decode('utf-8'))
    except (TypeError, ValueError, UnicodeDecodeError):
        try:
            parsed = parse_qs(raw.decode('utf-8'))
        except (TypeError, ValueError, UnicodeDecodeError):
            return {}
        return {key: values[0] if values else '' for key, values in parsed.items()}


@csrf_exempt
@require_http_methods(["POST"])
def api_signup(request):
    payload = _read_payload(request)
    username = (payload.get('username') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    confirm_password = payload.get('confirm_password') or payload.get('confirmPassword') or ''

    if not username or not email or not password or not confirm_password:
        return _json_error('Fill in all fields to create your account.')
    if password != confirm_password:
        return _json_error('Passwords do not match.')
    if User.objects.filter(username__iexact=username).exists():
        return _json_error('Username is already taken.')
    if User.objects.filter(email__iexact=email).exists():
        return _json_error('Email is already registered.')

    user = User.objects.create_user(username=username, email=email, password=password)
    Gamer.objects.get_or_create(user=user)

    return JsonResponse({
        'user': {
            'username': user.username,
            'email': user.email,
        }
    }, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    payload = _read_payload(request)
    email = (payload.get('email') or '').strip()
    password = payload.get('password') or ''

    if not email or not password:
        return _json_error('Enter your email and password.')

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User.objects.filter(username__iexact=email).first()

    if user is None or not user.check_password(password):
        return _json_error('Invalid email or password.', status=401)

    auth_login(request, user)

    return JsonResponse({
        'user': {
            'username': user.username,
            'email': user.email,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_reset_password(request):
    payload = _read_payload(request)
    email = (payload.get('email') or '').strip().lower()
    if not email:
        return _json_error('Enter your email address to continue.')

    user = User.objects.filter(email__iexact=email).first()
    reset_url = None

    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_path = f'/reset-password?uid={uid}&token={token}'
        reset_url = request.build_absolute_uri(reset_path)

        from_email = settings.DEFAULT_FROM_EMAIL or None
        if from_email:
            subject = 'Rotatly password reset'
            message = f'Reset your password using this link:\n{reset_url}'
            send_mail(subject, message, from_email, [user.email], fail_silently=True)

    return JsonResponse({'ok': True, 'resetUrl': reset_url})


@csrf_exempt
@require_http_methods(["POST"])
def api_reset_password_confirm(request):
    payload = _read_payload(request)
    uid = (payload.get('uid') or '').strip()
    token = (payload.get('token') or '').strip()
    password = payload.get('password') or ''
    confirm_password = payload.get('confirm_password') or payload.get('confirmPassword') or ''

    if not uid or not token:
        return _json_error('Invalid or expired reset link.')
    if not password or not confirm_password:
        return _json_error('Enter and confirm your new password.')
    if password != confirm_password:
        return _json_error('Passwords do not match.')

    try:
        user_id = urlsafe_base64_decode(uid).decode('utf-8')
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        return _json_error('Invalid or expired reset link.')

    if not default_token_generator.check_token(user, token):
        return _json_error('Invalid or expired reset link.')

    user.set_password(password)
    user.save(update_fields=['password'])

    return JsonResponse({'ok': True})


class LoginView(TemplateView):
    template_name = 'accounts/login.html'


class SignupView(TemplateView):
    template_name = 'accounts/signup.html'


class ResetView(TemplateView):
    template_name = 'accounts/reset.html'


class ResetEmailView(TemplateView):
    template_name = 'accounts/reset_email.html'


class NewPasswordView(TemplateView):
    template_name = 'accounts/new_password.html'


class ProfileView(TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['user'] = user
            context['username'] = user.username
            context['email'] = user.email
            context['date_joined'] = user.date_joined
        return context


@csrf_exempt
@require_http_methods(["POST"])
def api_update_profile(request):
    if not request.user.is_authenticated:
        return _json_error('You must be logged in to update your profile.', status=401)

    payload = _read_payload(request)
    username = (payload.get('username') or '').strip()

    if not username:
        return _json_error('Username cannot be empty.')

    user = request.user
    if username != user.username:
        if User.objects.filter(username__iexact=username).exclude(pk=user.pk).exists():
            return _json_error('Username is already taken.')
        user.username = username
        user.save(update_fields=['username'])

    return JsonResponse({
        'user': {
            'username': user.username,
            'email': user.email,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_change_password(request):
    if not request.user.is_authenticated:
        return _json_error('You must be logged in to change your password.', status=401)

    payload = _read_payload(request)
    current_password = payload.get('current_password') or payload.get('currentPassword') or ''
    new_password = payload.get('new_password') or payload.get('newPassword') or ''
    confirm_password = payload.get('confirm_password') or payload.get('confirmPassword') or ''

    if not current_password or not new_password or not confirm_password:
        return _json_error('Fill in all fields to change your password.')

    user = request.user
    if not user.check_password(current_password):
        return _json_error('Current password is incorrect.')

    if new_password != confirm_password:
        return _json_error('New passwords do not match.')

    if len(new_password) < 6:
        return _json_error('Password must be at least 6 characters.')

    user.set_password(new_password)
    user.save(update_fields=['password'])

    # Re-authenticate user to maintain session
    auth_login(request, user)

    return JsonResponse({'ok': True})


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return JsonResponse({'ok': True})
