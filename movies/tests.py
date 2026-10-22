from django.test import TestCase
from django.contrib.auth.models import User
from .models import Movie, Rating, Review
from .views import star_icons
from cart.models import Item, Order

class RatingTests(TestCase):
    def setUp(self):
        self.movie = Movie.objects.create(name='Test', price=1,
            description='d', image='movie_images/x.jpg')
        self.a = User.objects.create_user('alice', password='pw-alice-123')
        self.b = User.objects.create_user('bob', password='pw-bob-123')
        self.url = '/movies/%d/rate/' % self.movie.id

    def test_star_icons(self):
        self.assertEqual(star_icons(0), ['empty'] * 5)
        self.assertEqual(star_icons(3.5), ['full'] * 3 + ['half', 'empty'])
        self.assertEqual(star_icons(4.2), ['full'] * 4 + ['empty'])

    def test_rate_update_average_and_validation(self):
        self.client.login(username='alice', password='pw-alice-123')
        self.client.post(self.url, {'stars': 4})
        self.client.post(self.url, {'stars': 2})  # edit, not a second row
        self.client.post(self.url, {'stars': 9})  # rejected
        self.client.post(self.url, {'stars': 'x'})  # rejected
        self.assertEqual(Rating.objects.get(user=self.a).stars, 2)
        self.client.logout()
        self.client.login(username='bob', password='pw-bob-123')
        self.client.post(self.url, {'stars': 5})
        data = self.client.get('/movies/%d/' % self.movie.id).context['template_data']
        self.assertEqual(data['rating_count'], 2)
        self.assertEqual(data['rating_average'], 3.5)
        self.assertEqual(data['user_stars'], 5)

    def test_anonymous_cannot_rate(self):
        self.client.post(self.url, {'stars': 5})
        self.assertFalse(Rating.objects.exists())


class MovieLeadersAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='pass')
        self.client.force_login(self.admin)
        self.url = '/admin/movies/movieleaders/'
        self.avatar = Movie.objects.create(
            name='Avatar', price=12, description='Blue',
            image='movie_images/avatar.jpg')
        self.inception = Movie.objects.create(
            name='Inception', price=10, description='Dreams',
            image='movie_images/inception.jpg')

    def buy(self, movie, quantity):
        order = Order.objects.create(user=self.admin, total=movie.price * quantity)
        Item.objects.create(order=order, movie=movie,
            price=movie.price, quantity=quantity)

    def review(self, movie, comment, flagged=False):
        return Review.objects.create(movie=movie, user=self.admin,
            comment=comment, flagged=flagged)

    def leader_names(self, response, context_key):
        self.assertEqual(response.status_code, 200)
        return [movie.name for movie in response.context[context_key]]

    def test_empty_categories_have_independent_messages(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No purchases yet.')
        self.assertContains(response, 'No reviews yet.')
        self.assertEqual(self.leader_names(response, 'most_purchased_movies'), [])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'), [])
        self.assertEqual(response.context['purchase_count'], 0)
        self.assertEqual(response.context['review_count'], 0)

    def test_purchase_count_sums_quantities_across_orders(self):
        self.buy(self.avatar, 2)
        self.buy(self.avatar, 1)
        self.buy(self.avatar, 4)

        response = self.client.get(self.url)

        self.assertEqual(self.leader_names(response, 'most_purchased_movies'),
            ['Avatar'])
        self.assertEqual(response.context['purchase_count'], 7)

    def test_same_movie_can_lead_both_categories(self):
        self.buy(self.avatar, 2)
        self.buy(self.inception, 1)
        self.review(self.avatar, 'First Avatar review')
        self.review(self.avatar, 'Second Avatar review')
        self.review(self.inception, 'Inception review')

        response = self.client.get(self.url)

        self.assertEqual(self.leader_names(response, 'most_purchased_movies'),
            ['Avatar'])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'),
            ['Avatar'])
        self.assertEqual(response.context['purchase_count'], 2)
        self.assertEqual(response.context['review_count'], 2)

    def test_different_movies_can_lead_each_category(self):
        self.buy(self.inception, 3)
        self.buy(self.avatar, 1)
        self.review(self.avatar, 'First Avatar review')
        self.review(self.avatar, 'Second Avatar review')
        self.review(self.inception, 'Inception review')

        response = self.client.get(self.url)

        self.assertEqual(self.leader_names(response, 'most_purchased_movies'),
            ['Inception'])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'),
            ['Avatar'])
        self.assertEqual(response.context['purchase_count'], 3)
        self.assertEqual(response.context['review_count'], 2)

    def test_tied_movies_all_appear_as_leaders(self):
        self.buy(self.avatar, 2)
        self.buy(self.inception, 2)
        self.review(self.avatar, 'Avatar review')
        self.review(self.inception, 'Inception review')

        response = self.client.get(self.url)

        self.assertEqual(self.leader_names(response, 'most_purchased_movies'),
            ['Avatar', 'Inception'])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'),
            ['Avatar', 'Inception'])
        self.assertEqual(response.context['purchase_count'], 2)
        self.assertEqual(response.context['review_count'], 1)

    def test_refresh_reflects_new_purchases_and_reviews(self):
        self.buy(self.avatar, 1)
        self.review(self.avatar, 'Avatar review')
        first = self.client.get(self.url)
        self.assertEqual(self.leader_names(first, 'most_purchased_movies'),
            ['Avatar'])
        self.assertEqual(self.leader_names(first, 'most_reviewed_movies'),
            ['Avatar'])

        self.buy(self.inception, 3)
        self.review(self.inception, 'First Inception review')
        self.review(self.inception, 'Second Inception review')
        refreshed = self.client.get(self.url)

        self.assertEqual(self.leader_names(refreshed, 'most_purchased_movies'),
            ['Inception'])
        self.assertEqual(self.leader_names(refreshed, 'most_reviewed_movies'),
            ['Inception'])
        self.assertEqual(refreshed.context['purchase_count'], 3)
        self.assertEqual(refreshed.context['review_count'], 2)

    def test_flagged_reviews_count_but_ratings_do_not(self):
        self.review(self.avatar, 'Flagged review', flagged=True)
        Rating.objects.create(movie=self.inception, user=self.admin, stars=5)

        response = self.client.get(self.url)

        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'),
            ['Avatar'])
        self.assertEqual(response.context['review_count'], 1)

    def test_movie_leaders_is_listed_on_admin_index(self):
        response = self.client.get('/admin/')

        self.assertContains(response, 'Movie Leaders')

    def test_movie_leaders_does_not_allow_movie_edits(self):
        response = self.client.get(
            f'/admin/movies/movieleaders/{self.avatar.pk}/change/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['has_change_permission'])

    def test_non_staff_user_cannot_view_movie_leaders(self):
        self.client.logout()
        customer = User.objects.create_user(username='customer', password='pass')
        self.client.force_login(customer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
