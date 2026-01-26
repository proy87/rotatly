import datetime
import json
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.game.constants import DATE_FORMAT, JS_DATE_FORMAT, START_DATE
from apps.game.models import PuzzleAttempt
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


def _build_puzzle_data(attempts):
    daily_entries = {}
    custom_entries = {}

    for attempt in attempts:
        if attempt.puzzle_type == PuzzleAttempt.DAILY and attempt.daily_id:
            entry_date = START_DATE + datetime.timedelta(days=attempt.daily.index)
            entry_key = str(attempt.daily.index)
            entry = daily_entries.setdefault(entry_key, {
                'id': entry_key,
                'date': entry_date.strftime(DATE_FORMAT),
                'dateRaw': entry_date.strftime(JS_DATE_FORMAT),
                'attempts': [],
            })
        elif attempt.puzzle_type == PuzzleAttempt.CUSTOM and attempt.custom_id:
            entry_date = timezone.localtime(attempt.created_at)
            entry_key = attempt.custom.index
            entry = custom_entries.setdefault(entry_key, {
                'id': entry_key,
                'date': entry_date.strftime(DATE_FORMAT),
                'dateRaw': entry_date.strftime(JS_DATE_FORMAT),
                'attempts': [],
            })
        else:
            continue

        entry['attempts'].append({
            'moves': attempt.moves,
            'seconds': attempt.seconds,
        })

    def finalize(entries):
        results = []
        for entry in entries.values():
            for idx, attempt in enumerate(entry['attempts'], start=1):
                attempt['id'] = idx
            best_attempt = min(entry['attempts'], key=lambda item: (item['moves'], item['seconds']))
            entry['bestMoves'] = best_attempt['moves']
            entry['bestSeconds'] = best_attempt['seconds']
            results.append(entry)
        results.sort(key=lambda item: item['dateRaw'], reverse=True)
        return results

    return {
        'daily': finalize(daily_entries),
        'custom': finalize(custom_entries),
    }


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


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        context['username'] = user.username
        context['email'] = user.email
        context['date_joined'] = user.date_joined
        attempts = (PuzzleAttempt.objects
                    .filter(user=user)
                    .select_related('daily', 'custom')
                    .order_by('created_at'))
        puzzle_data = _build_puzzle_data(attempts)
        context['puzzle_data'] = json.dumps(puzzle_data)
        context['has_puzzles'] = len(puzzle_data['daily']) > 0
        return context


class LeaderboardView(TemplateView):
    template_name = 'accounts/leaderboard.html'


class PrivacyView(TemplateView):
    template_name = 'accounts/privacy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.conf import settings
        release_offset_hours = 0 if settings.DEBUG else 5
        today_date = datetime.datetime.now() - datetime.timedelta(hours=release_offset_hours)
        
        context['min_date_js'] = (START_DATE + datetime.timedelta(days=1)).strftime(JS_DATE_FORMAT)
        context['max_date_js'] = today_date.strftime(JS_DATE_FORMAT)
        context['current_date_js'] = today_date.strftime(JS_DATE_FORMAT)
        context['current_date'] = today_date.strftime(DATE_FORMAT)
        return context


@require_http_methods(["GET"])
def api_leaderboard_daily(request, date: datetime.datetime):
    """Get leaderboard for a specific daily puzzle."""
    from apps.game.models import Daily
    
    game_index = (date - START_DATE).days
    if game_index < 1:
        return JsonResponse({'entries': []})
    
    # Get the daily puzzle
    daily = Daily.objects.filter(index=game_index).first()
    if not daily:
        return JsonResponse({'entries': []})
    
    # Get best attempts for each user for this puzzle
    # Using a subquery to get the best attempt per user
    from django.db.models import Min, OuterRef, Subquery
    
    # Get all attempts for this puzzle
    attempts = (PuzzleAttempt.objects
                .filter(puzzle_type=PuzzleAttempt.DAILY, daily=daily)
                .select_related('user'))
    
    # Group by user and get best result (lowest moves, then lowest seconds)
    user_best = {}
    for attempt in attempts:
        user_id = attempt.user_id
        if user_id not in user_best:
            user_best[user_id] = {
                'userId': user_id,
                'username': attempt.user.username,
                'moves': attempt.moves,
                'seconds': attempt.seconds,
            }
        else:
            current = user_best[user_id]
            # Better if fewer moves, or same moves but less time
            if (attempt.moves < current['moves'] or 
                (attempt.moves == current['moves'] and attempt.seconds < current['seconds'])):
                user_best[user_id] = {
                    'userId': user_id,
                    'username': attempt.user.username,
                    'moves': attempt.moves,
                    'seconds': attempt.seconds,
                }
    
    # Sort by moves (ascending), then seconds (ascending)
    entries = sorted(user_best.values(), key=lambda x: (x['moves'], x['seconds']))
    
    return JsonResponse({'entries': entries})


@require_http_methods(["GET"])
def api_leaderboard_custom(request):
    """Get overall leaderboard for custom puzzles (best performers across all custom puzzles)."""
    from django.db.models import Count, Min
    
    # Get users with their total custom puzzles completed and best average performance
    attempts = (PuzzleAttempt.objects
                .filter(puzzle_type=PuzzleAttempt.CUSTOM)
                .select_related('user'))
    
    # Group by user and calculate stats
    user_stats = {}
    for attempt in attempts:
        user_id = attempt.user_id
        if user_id not in user_stats:
            user_stats[user_id] = {
                'userId': user_id,
                'username': attempt.user.username,
                'totalMoves': 0,
                'totalSeconds': 0,
                'puzzleCount': 0,
            }
        user_stats[user_id]['totalMoves'] += attempt.moves
        user_stats[user_id]['totalSeconds'] += attempt.seconds
        user_stats[user_id]['puzzleCount'] += 1
    
    # Calculate averages and prepare entries
    entries = []
    for stats in user_stats.values():
        if stats['puzzleCount'] > 0:
            entries.append({
                'userId': stats['userId'],
                'username': stats['username'],
                'moves': round(stats['totalMoves'] / stats['puzzleCount']),
                'seconds': round(stats['totalSeconds'] / stats['puzzleCount']),
                'puzzleCount': stats['puzzleCount'],
            })
    
    # Sort by average moves (ascending), then average seconds (ascending)
    entries.sort(key=lambda x: (x['moves'], x['seconds']))
    
    return JsonResponse({'entries': entries})


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
