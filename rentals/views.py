# rentals/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from games.models import Game
from .models import Rental
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseForbidden
from .forms import RentalRequestForm

# @login_required
# def request_rental(request, game_id):
#     game = get_object_or_404(Game, id=game_id)
#     if not game.available:
#         messages.error(request, "This game is currently not available.")
#         return redirect('student_dashboard')

#     # Check if already requested
#     if Rental.objects.filter(user=request.user, game=game, status='pending').exists():
#         messages.warning(request, "You have already requested this game.")
#         return redirect('student_dashboard')

#     Rental.objects.create(user=request.user, game=game)
#     messages.success(request, f"Rental request for {game.title} submitted!")
#     return redirect('student_dashboard')

# @login_required
# def request_rental(request, game_id):
#     game = get_object_or_404(Game, id=game_id)

#     if not game.available:
#         messages.error(request, "This game is currently not available.")
#         return redirect('student_dashboard')

#     # Check if already requested
#     if Rental.objects.filter(user=request.user, game=game, status='pending').exists():
#         messages.warning(request, "You have already requested this game.")
#         return redirect('student_dashboard')

#     if request.method == "POST":
#         form = RentalRequestForm(request.POST)
#         if form.is_valid():
#             rental_days = form.cleaned_data['rental_days']
#             cost = rental_days * game.price_per_day 
#             Rental.objects.create(
#                 user=request.user,
#                 game=game,
#                 rental_days=rental_days,
#                 cost=cost
#             )
#             messages.success(request, f"Rental request for {game.title} submitted for {rental_days} days! Cost: ₹{cost}")
#             return redirect('student_dashboard')
#     else:
#         form = RentalRequestForm()

#     return render(request, "rentals/request_rentals.html", {"form": form, "game": game})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from games.models import Game
from .models import Rental
from .forms import RentalRequestForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def request_rental(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if not game.available:
        messages.error(request, "This game is currently not available.")
        return redirect('student_dashboard')

    # Check if already requested
    if Rental.objects.filter(user=request.user, game=game, status='pending').exists():
        messages.warning(request, "You have already requested this game.")
        return redirect('student_dashboard')

    if request.method == "POST":
        form = RentalRequestForm(request.POST)
        if form.is_valid():
            rental_days = form.cleaned_data['rental_days']
            cost = rental_days * float(game.price_per_day)  # calculate total cost based on the game's price

            Rental.objects.create(
                user=request.user,
                game=game,
                rental_days=rental_days,
                cost=cost
            )

            messages.success(
                request,
                f"Rental request for {game.title} submitted for {rental_days} days! Total cost: ₹{cost:.2f}"
            )
            return redirect('student_dashboard')
    else:
        form = RentalRequestForm()

    return render(request, "rentals/request_rentals.html", {"form": form, "game": game})



@login_required
def my_rentals(request):
    rentals = Rental.objects.filter(user=request.user)
    return render(request, 'rentals/my_rentals.html', {'rentals': rentals})


@login_required
def update_rental_status(request, rental_id, new_status):  # <- accept new_status
    rental = get_object_or_404(Rental, id=rental_id)

    # Optional: restrict student admins to only their own rentals
    if not request.user.is_superuser and rental.game.added_by != request.user:
        messages.error(request, "You don't have permission to update this rental.")
        return redirect('student_admin_dashboard')

    rental.status = new_status.lower()
    if new_status.lower() == 'approved':
        rental.approved_at = timezone.now()
    rental.save()
    messages.success(request, f"Rental status updated to {new_status}.")
    
    # Redirect to appropriate dashboard
    if request.user.is_superuser:
        return redirect('superadmin_dashboard')
    else:
        return redirect('student_admin_dashboard')

@login_required
def pay_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)

    if rental.status != 'approved':
        messages.error(request, "You cannot pay for a rental that is not approved.")
        return redirect('my_rentals')

    if rental.payment_status == 'paid':
        messages.info(request, "This rental is already paid.")
        return redirect('my_rentals')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'Mock Method')
        rental.payment_status = 'paid'
        rental.payment_method = payment_method
        rental.payment_date = timezone.now()
        rental.transaction_id = f"TXN-{rental.id}-{int(timezone.now().timestamp())}"
        rental.save()
        messages.success(request, f"Payment successful! Transaction ID: {rental.transaction_id}")
        return redirect('my_rentals')

    return render(request, 'rentals/pay_rental.html', {'rental': rental})



