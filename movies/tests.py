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
            name='Avatar', price=12, description='Blue')
        self.inception = Movie.objects.create(
            name='Inception', price=10, description='Dreams')

    def buy(self, movie, quantity=1):
        order = Order.objects.create(user=self.admin, total=movie.price * quantity)
        Item.objects.create(order=order, movie=movie,
            price=movie.price, quantity=quantity)

    def review(self, movie, comment='Good movie', flagged=False):
        return Review.objects.create(movie=movie, user=self.admin,
            comment=comment, flagged=flagged)

    def leader_names(self, response, context_key):
        return [movie.name for movie in response.context[context_key]]

    def test_same_movie_can_lead_both_measures_independently(self):
        self.buy(self.avatar, quantity=2)
        self.buy(self.inception)
        self.review(self.avatar, 'First Avatar review')
        self.review(self.avatar, 'Second Avatar review')
        self.review(self.inception)
        Rating.objects.create(movie=self.inception, user=self.admin, stars=5)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.leader_names(response, 'most_purchased_movies'),
            ['Avatar'])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'),
            ['Avatar'])
        self.assertEqual(response.context['purchase_count'], 2)
        self.assertEqual(response.context['review_count'], 2)

    def test_different_movies_can_lead_each_measure(self):
        self.client.post('/movies/%d/review/create/' % self.avatar.id,
            {'comment': 'Avatar review'})
        self.client.post('/cart/%d/add/' % self.avatar.id, {'quantity': 1})
        self.client.post('/cart/purchase/')

        same_leader_response = self.client.get(self.url)
        self.assertEqual(
            self.leader_names(same_leader_response, 'most_purchased_movies'),
            ['Avatar'])
        self.assertEqual(
            self.leader_names(same_leader_response, 'most_reviewed_movies'),
            ['Avatar'])

        self.client.post('/cart/%d/add/' % self.inception.id, {'quantity': 1})
        self.client.post('/cart/purchase/')
        self.client.post('/cart/%d/add/' % self.inception.id, {'quantity': 1})
        self.client.post('/cart/purchase/')
        response = self.client.get(self.url)

        self.assertEqual(self.leader_names(response, 'most_purchased_movies'),
            ['Inception'])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'),
            ['Avatar'])
        self.assertEqual(response.context['purchase_count'], 2)
        self.assertEqual(response.context['review_count'], 1)

    def test_ties_show_every_movie_and_empty_metrics_have_messages(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'No purchases yet.')
        self.assertContains(response, 'No reviews yet.')
        self.assertEqual(self.leader_names(response, 'most_purchased_movies'), [])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'), [])

        self.buy(self.avatar)
        self.buy(self.inception)
        self.review(self.avatar)
        self.review(self.inception)
        response = self.client.get(self.url)

        self.assertEqual(self.leader_names(response, 'most_purchased_movies'),
            ['Avatar', 'Inception'])
        self.assertEqual(self.leader_names(response, 'most_reviewed_movies'),
            ['Avatar', 'Inception'])

    def test_non_staff_user_cannot_view_movie_leaders(self):
        self.client.logout()
        customer = User.objects.create_user(username='customer', password='pass')
        self.client.force_login(customer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_movie_leaders_is_listed_on_admin_index(self):
        response = self.client.get('/admin/')

        self.assertContains(response, 'Movie Leaders')
