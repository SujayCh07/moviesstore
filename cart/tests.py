from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from movies.models import Movie
from .models import Order, Item

class TopBuyerAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='pass')
        self.client.force_login(self.admin)
        self.movie = Movie.objects.create(
            name='Avatar', price=12, description='Blue')
        self.url = '/admin/cart/topbuyer/'

    def buy(self, user, quantity):
        order = Order.objects.create(user=user, total=0)
        Item.objects.create(order=order, movie=self.movie,
            price=12, quantity=quantity)

    def test_no_purchases(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'No movies have been bought yet.')

    def test_counts_quantity_across_orders(self):
        alice = User.objects.create_user(username='alice', password='pass')
        bob = User.objects.create_user(username='bob', password='pass')
        self.buy(alice, 2)
        self.buy(alice, 3)
        self.buy(bob, 4)
        response = self.client.get(self.url)
        self.assertEqual(list(response.context['top_buyers']), [alice])
        self.assertEqual(response.context['movies_bought'], 5)
        self.assertNotContains(response, 'bob')

    def test_tie_shows_all_top_buyers(self):
        alice = User.objects.create_user(username='alice', password='pass')
        bob = User.objects.create_user(username='bob', password='pass')
        self.buy(alice, 2)
        self.buy(bob, 2)
        response = self.client.get(self.url)
        self.assertEqual(set(response.context['top_buyers']), {alice, bob})
        self.assertContains(response, 'tied')

    def test_listed_on_admin_index(self):
        response = self.client.get('/admin/')
        self.assertContains(response, 'Top Buyer')

    def test_non_staff_redirected(self):
        User.objects.create_user(username='customer', password='pass')
        self.client.logout()
        self.client.login(username='customer', password='pass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
