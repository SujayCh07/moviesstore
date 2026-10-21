from django.test import TestCase
from django.contrib.auth.models import User
from .models import Movie, Rating
from .views import star_icons

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
