from django.contrib.auth.models import User
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

def calculate_cart_total(cart, movies_in_cart):
    total = 0
    for movie in movies_in_cart:
        quantity = cart[str(movie.id)]
        total += movie.price * int(quantity)
    return total

def users_by_movies_bought():
    # Shared purchase aggregation (Stories 3, 5 and 6): every user annotated
    # with the total quantity of movies across all their orders, 0 if none.
    return User.objects.annotate(
        movies_bought=Coalesce(Sum('order__item__quantity'), Value(0))
    ).order_by('-movies_bought', 'username')
