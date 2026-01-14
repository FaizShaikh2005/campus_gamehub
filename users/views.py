from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from rentals.models import Rental
from games.models import Game
from django.db.models import Sum, Q

User = get_user_model()


# ------------------ Register ------------------
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


# ------------------ Forgot Password ------------------
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Generate OTP
            otp = str(random.randint(100000, 999999))

            # Store OTP and email in session
            request.session['otp'] = otp
            request.session['reset_email'] = email

            # Print OTP in terminal for debugging
            print(f"OTP for {email}: {otp}")

            # Send OTP via email
            try:
                send_mail(
                    subject="Campus GameHub Password Reset OTP",
                    message=f"Your OTP is: {otp}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                )
            except Exception as e:
                print("Failed to send email:", e)

            messages.success(request, "OTP has been sent to your email and terminal.")
            return redirect('verify_otp')

        except User.DoesNotExist:
            messages.error(request, "Email not registered.")

    return render(request, 'users/forgot_password.html')


# ------------------ Verify OTP ------------------
def verify_otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if str(entered_otp) == str(request.session.get('otp')):
            request.session['otp_verified'] = True
            messages.success(request, "OTP verified. You can now reset your password.")
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP. Try again.")
    return render(request, 'users/otp_verify.html')


# ------------------ Reset Password ------------------
def reset_password_view(request):
    if not request.session.get('otp_verified'):
        messages.error(request, "You must verify OTP first.")
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            email = request.session.get('reset_email')
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # Clear session data
            request.session.pop('otp', None)
            request.session.pop('reset_email', None)
            request.session.pop('otp_verified', None)

            messages.success(request, "Password reset successful! You can log in now.")
            return redirect('login')

    return render(request, 'users/reset_password.html')


# ------------------ Login Redirect ------------------
@login_required
def login_redirect_view(request):
    user = request.user
    if user.role == 'super_admin':
        return redirect('superadmin_dashboard')
    elif user.role == 'student_admin':
        return redirect('student_admin_dashboard')
    else:
        return redirect('student_dashboard')


# ------------------ Super Admin Dashboard ------------------
@login_required
def superadmin_dashboard(request):
    users = User.objects.all()
    games = Game.objects.all()
    rentals = Rental.objects.all().order_by('-requested_at')

    return render(request, 'dashboard/superadmin_dashboard.html', {
        'users': users,
        'games': games,
        'rentals': rentals
    })


# ------------------ Student Admin Dashboard ------------------
@login_required
def student_admin_dashboard(request):
    # Show games they added
    games = Game.objects.filter(added_by=request.user)

    # Show rentals for those games
    rentals = Rental.objects.filter(game__added_by=request.user)

    return render(request, 'dashboard/student_admin_dashboard.html', {
        'games': games,
        'rentals': rentals
    })


# ------------------ Student Dashboard ------------------
@login_required
def student_dashboard(request):
    games = Game.objects.filter(available=True)
    rentals = Rental.objects.filter(user=request.user)
    return render(request, 'dashboard/student_dashboard.html', {
        'games': games,
        'rentals': rentals
    })


# ------------------ Profile View with Proper Permissions ------------------
@login_required
def profile_view(request, user_id=None):
    # Determine target user
    if user_id:
        target_user = get_object_or_404(User, id=user_id)
        is_own_profile = (request.user == target_user)
    else:
        target_user = request.user
        is_own_profile = True

    # Check if viewer is admin
    viewer_is_admin = request.user.role in ['super_admin', 'student_admin']
    
    # Initialize default values
    games_listed = []
    rentals_received = []
    total_games_listed = 0
    total_revenue_earned = 0.0
    show_financial_details = False

    # Determine what data to show based on viewer and profile owner
    # Financial details (revenue, payments) only visible to profile owner or super_admin
    show_financial_details = is_own_profile or request.user.role == 'super_admin'

    # Games & Rentals Analytics for student_admin and super_admin profiles
    if target_user.role in ['student_admin', 'super_admin']:
        # Games listed by target user
        games_listed = Game.objects.filter(added_by=target_user)
        total_games_listed = games_listed.count()

        # Rentals of their games
        rentals_received = Rental.objects.filter(game__added_by=target_user)

        # Revenue only if viewer has permission
        if show_financial_details:
            total_revenue_earned = rentals_received.filter(
                payment_status='paid'
            ).aggregate(total=Sum('cost'))['total'] or 0.0

    # Rentals made by target user (visible to all)
    rentals_made = Rental.objects.filter(user=target_user)
    
    # Basic rental statistics (visible to all)
    total_rentals_made = rentals_made.count()
    active_rentals = rentals_made.filter(status__in=['approved', 'ongoing']).count()
    completed_rentals = rentals_made.filter(status='returned').count()
    
    # Spending details only if viewer has permission
    total_spent_on_rentals = 0.0
    if show_financial_details:
        total_spent_on_rentals = rentals_made.filter(
            payment_status='paid'
        ).aggregate(total=Sum('cost'))['total'] or 0.0

    # Count currently rented games (for public view)
    currently_rented_games = rentals_received.filter(
        status__in=['approved', 'ongoing']
    ).count() if target_user.role in ['student_admin', 'super_admin'] else 0

    # Count past rentals of their games (for public view)
    past_rentals_of_games = rentals_received.filter(
        status='returned'
    ).count() if target_user.role in ['student_admin', 'super_admin'] else 0

    # Prepare context
    context = {
        'user_profile': target_user,
        'is_own_profile': is_own_profile,
        'viewer_is_admin': viewer_is_admin,
        'show_financial_details': show_financial_details,
        
        # Games data
        'games_listed': games_listed,
        'total_games_listed': total_games_listed,
        
        # Rental statistics (public)
        'total_rentals_made': total_rentals_made,
        'active_rentals': active_rentals,
        'completed_rentals': completed_rentals,
        'currently_rented_games': currently_rented_games,
        'past_rentals_of_games': past_rentals_of_games,
        
        # Financial data (restricted)
        'total_revenue_earned': total_revenue_earned,
        'total_spent_on_rentals': total_spent_on_rentals,
        
        # Detailed lists
        'rentals_made': rentals_made,
        'rentals_received': rentals_received,
    }

    return render(request, 'users/profile.html', context)

#####################################################

# from django.shortcuts import render, redirect,get_object_or_404
# from django.contrib import messages
# from django.contrib.auth import login, get_user_model
# from django.core.mail import send_mail
# from django.conf import settings
# import random
# from .forms import RegisterForm
# from django.contrib.auth.decorators import login_required
# from rentals.models import Rental
# from games.models import Game
# from django.contrib.auth import get_user_model
# from django.db.models import Sum, Q
# User = get_user_model()
# from django.contrib.auth import get_user_model
# User = get_user_model()



# # ------------------ Register ------------------
# def register_view(request):
#     if request.method == 'POST':
#         form = RegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.set_password(form.cleaned_data['password1'])
#             user.save()
#             login(request, user)
#             messages.success(request, "Registration successful!")
#             return redirect('home')
#     else:
#         form = RegisterForm()
#     return render(request, 'users/register.html', {'form': form})


# def forgot_password_view(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         try:
#             user = User.objects.get(email=email)
            
#             # Generate OTP
#             otp = str(random.randint(100000, 999999))

#             # Store OTP and email in session
#             request.session['otp'] = otp
#             request.session['reset_email'] = email

#             # 1️⃣ Print OTP in terminal for debugging/mock users
#             print(f"OTP for {email}: {otp}")

#             # 2️⃣ Send OTP via email
#             try:
#                 send_mail(
#                     subject="Campus GameHub Password Reset OTP",
#                     message=f"Your OTP is: {otp}",
#                     from_email=settings.EMAIL_HOST_USER,
#                     recipient_list=[email],
#                 )
#             except Exception as e:
#                 print("Failed to send email:", e)

#             messages.success(request, "OTP has been sent to your email and terminal.")
#             return redirect('verify_otp')

#         except User.DoesNotExist:
#             messages.error(request, "Email not registered.")

#     return render(request, 'users/forgot_password.html')

# # ------------------ Verify OTP ------------------
# def verify_otp_view(request):
#     if request.method == 'POST':
#         entered_otp = request.POST.get('otp')
#         if str(entered_otp) == str(request.session.get('otp')):
#             request.session['otp_verified'] = True
#             messages.success(request, "OTP verified. You can now reset your password.")
#             return redirect('reset_password')
#         else:
#             messages.error(request, "Invalid OTP. Try again.")
#     return render(request, 'users/otp_verify.html')

# # ------------------ Reset Password ------------------
# def reset_password_view(request):
#     if not request.session.get('otp_verified'):
#         messages.error(request, "You must verify OTP first.")
#         return redirect('forgot_password')

#     if request.method == 'POST':
#         new_password = request.POST.get('new_password')
#         confirm_password = request.POST.get('confirm_password')

#         if new_password != confirm_password:
#             messages.error(request, "Passwords do not match.")
#         else:
#             email = request.session.get('reset_email')
#             user = User.objects.get(email=email)
#             user.set_password(new_password)
#             user.save()

#             # Clear session data
#             request.session.pop('otp', None)
#             request.session.pop('reset_email', None)
#             request.session.pop('otp_verified', None)

#             messages.success(request, "Password reset successful! You can log in now.")
#             return redirect('login')

#     return render(request, 'users/reset_password.html')


# # ---------------- to make sure that dashboards work----------------


# @login_required
# def login_redirect_view(request):
#     user = request.user
#     if user.role == 'super_admin':
#         return redirect('superadmin_dashboard')
#     elif user.role == 'student_admin':
#         return redirect('student_admin_dashboard')
#     else:
#         return redirect('student_dashboard')
    
# # ------------------------ users Dashboard views ------------------------------

# @login_required
# def superadmin_dashboard(request):
#     users = User.objects.all()
#     games = Game.objects.all()
#     rentals = Rental.objects.all().order_by('-requested_at')  # latest first

#     return render(request, 'dashboard/superadmin_dashboard.html', {
#         'users': users,
#         'games': games,
#         'rentals': rentals
#     })


# #--------------------- student admin Dashboard views --------------------------------
# @login_required
# def student_admin_dashboard(request):
#     # Show games they added
#     games = Game.objects.filter(added_by=request.user)

#     # Show rentals for those games
#     rentals = Rental.objects.filter(game__added_by=request.user)

#     return render(request, 'dashboard/student_admin_dashboard.html', {
#         'games': games,
#         'rentals': rentals
#     })

# #------------------------- Student dasboard views -----------------------
# @login_required
# def student_dashboard(request):
#     games = Game.objects.filter(available=True)
#     rentals = Rental.objects.filter(user=request.user)
#     return render(request, 'dashboard/student_dashboard.html', {'games': games, 'rentals': rentals})

# #------------------------------- profile -------------------------------------
# @login_required
# def profile_view(request, user_id=None):
#     # -------------------- Determine target user --------------------
#     if user_id:
#         target_user = get_object_or_404(User, id=user_id)
#         viewing_as_admin = (request.user.role == 'super_admin')
#     else:
#         target_user = request.user
#         viewing_as_admin = False

#     # -------------------- Default values --------------------
#     ames_listed = []
#     rentals_received = []
#     total_games_listed = 0
#     total_revenue_earned = 0.0


#     # -------------------- Show games & revenue ONLY if owner or super admin --------------------
#     if target_user.role in ['student_admin', 'super_admin']:
#         games_listed = Game.objects.filter(added_by=target_user) if request.user == target_user or viewing_as_admin else []
#         total_games_listed = games_listed.count() if request.user == target_user or viewing_as_admin else 0
#         rentals_received = Rental.objects.filter(game__added_by=target_user) if request.user == target_user or viewing_as_admin else []
#         total_revenue_earned = rentals_received.filter(payment_status='paid').aggregate(total=Sum('cost'))['total'] or 0.0 if request.user == target_user or viewing_as_admin else 0.0

#     # -------------------- Rentals made (public for anyone) --------------------
#     rentals_made = Rental.objects.filter(user=target_user)
#     total_rentals_made = rentals_made.count()
#     active_rentals = rentals_made.filter(status__in=['approved', 'ongoing']).count()
#     completed_rentals = rentals_made.filter(status='returned').count()
#     total_spent_on_rentals = rentals_made.filter(payment_status='paid').aggregate(total=Sum('cost'))['total'] or 0.0

#     # -------------------- Prepare Context --------------------
#     context = {
#         'user_profile': target_user,
#         'viewing_as_admin': viewing_as_admin,
#         'games_listed': games_listed,
#         'rentals_made': rentals_made,
#         'rentals_received': rentals_received,
#         'total_games_listed': total_games_listed,
#         'total_revenue_earned': total_revenue_earned,
#         'total_rentals_made': total_rentals_made,
#         'active_rentals': active_rentals,
#         'completed_rentals': completed_rentals,
#         'total_spent_on_rentals': total_spent_on_rentals,
#     }

#     return render(request, 'users/profile.html', context)

