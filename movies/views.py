from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Rating
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
# Create your views here.

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html',
                  {'template_data': template_data})
def show(request, id):
    movie =  Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie, flagged=False)
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    ratings = Rating.objects.filter(movie=movie)
    average = ratings.aggregate(Avg('stars'))['stars__avg']
    template_data['rating_count'] = ratings.count()
    template_data['rating_average'] = average
    template_data['average_stars'] = star_icons(average or 0)
    user_rating = None
    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).first()
    template_data['user_stars'] = user_rating.stars if user_rating else 0
    return render(request, 'movies/show.html',
        {'template_data': template_data})
def star_icons(average):
    # 5 entries of 'full' / 'half' / 'empty', rounding to the nearest half star
    halves = round(average * 2)
    return ['full' if halves >= i * 2 else 'half' if halves == i * 2 - 1
            else 'empty' for i in range(1, 6)]
@login_required
def rate_movie(request, id):
    movie = get_object_or_404(Movie, id=id)
    if request.method == 'POST':
        try:
            stars = int(request.POST.get('stars', ''))
        except ValueError:
            stars = 0
        if 1 <= stars <= 5:
            Rating.objects.update_or_create(movie=movie, user=request.user,
                defaults={'stars': stars})
    return redirect('movies.show', id=id)
@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html',
            {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id,
        user=request.user)
    review.delete()
    return redirect('movies.show', id=id)
#report review implementation
@login_required
def report_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user == review.user:
        return redirect('movies.show', id=id)
    if request.method == 'POST':
        review = Review.objects.get(id=review_id)
        review.flagged = True
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)