from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Game
from .forms import GameForm


def game_list(request):
    games = Game.objects.all()
    return render(request, 'games/games_list.html', {'games': games})


def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)
    return render(request, 'games/game_detail.html', {'game': game})


# ---------------- Game Management ----------------

@login_required
def add_game(request):
    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES)
        if form.is_valid():
            game = form.save(commit=False)
            game.added_by = request.user
            game.save()
            messages.success(request, "Game added successfully!")
            return redirect('game_list')
    else:
        form = GameForm()
    return render(request, 'games/game_form.html', {'form': form, 'title': 'Add Game'})


@login_required
def edit_game(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES, instance=game)
        if form.is_valid():
            form.save()
            messages.success(request, "Game updated successfully!")
            return redirect('game_detail', pk=pk)
    else:
        form = GameForm(instance=game)
    return render(request, 'games/game_form.html', {'form': form, 'title': 'Edit Game'})


@login_required
def delete_game(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        game.delete()
        messages.success(request, "Game deleted successfully!")
        return redirect('game_list')
    return render(request, 'games/game_confirm_delete.html', {'game': game})
