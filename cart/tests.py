from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from movies.models import Movie
from .models import Order, Item
from .utils import users_by_movies_bought

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

class PurchaseRankingAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin', password='pass')
        self.client.force_login(self.admin)
        self.movie = Movie.objects.create(
            name='Avatar', price=12, description='Blue')
        self.url = '/admin/cart/purchaseranking/'
        self.alice = User.objects.create_user(username='alice', password='pass')
        self.bob = User.objects.create_user(username='bob', password='pass')
        self.carol = User.objects.create_user(username='carol', password='pass')

    def buy(self, user, quantity):
        order = Order.objects.create(user=user, total=0)
        Item.objects.create(order=order, movie=self.movie,
            price=12, quantity=quantity)

    def ranked(self, response):
        return [(r['rank'], r['username'], r['movies_bought'])
            for r in response.context['rankings']]

    def test_all_users_ranked_including_zero_purchases(self):
        self.buy(self.alice, 2)
        self.buy(self.alice, 3)
        self.buy(self.bob, 4)
        response = self.client.get(self.url)
        self.assertEqual(self.ranked(response), [
            (1, 'alice', 5), (2, 'bob', 4),
            (3, 'admin', 0), (3, 'carol', 0)])
        self.assertEqual(response.context['total_users'], 4)

    def test_limit_selects_list_size(self):
        self.buy(self.alice, 2)
        self.buy(self.bob, 1)
        response = self.client.get(self.url, {'limit': 2})
        self.assertEqual(self.ranked(response),
            [(1, 'alice', 2), (2, 'bob', 1)])
        self.assertContains(response, 'Showing 2 of 4 users.')
        self.assertContains(response, 'type="number"')

    def test_limit_larger_than_user_count_shows_all(self):
        response = self.client.get(self.url, {'limit': 50})
        self.assertEqual(len(response.context['rankings']), 4)

    def test_invalid_limit_shows_all_with_error(self):
        response = self.client.get(self.url, {'limit': 0})
        self.assertEqual(len(response.context['rankings']), 4)
        self.assertTrue(response.context['form'].errors)

    def test_refresh_reflects_new_purchases(self):
        self.buy(self.alice, 1)
        response = self.client.get(self.url)
        self.assertEqual(self.ranked(response)[0], (1, 'alice', 1))
        self.buy(self.carol, 3)
        response = self.client.get(self.url)
        self.assertEqual(self.ranked(response)[0], (1, 'carol', 3))

    def test_listed_separately_on_admin_index(self):
        response = self.client.get('/admin/')
        self.assertContains(response, 'Purchase Rankings')
        self.assertContains(response, 'Top Buyer')

    def test_non_staff_redirected(self):
        self.client.logout()
        self.client.login(username='alice', password='pass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

class SharedAggregationTests(TestCase):
    def test_top_buyer_and_rankings_agree(self):
        movie = Movie.objects.create(name='Avatar', price=12, description='Blue')
        alice = User.objects.create_user(username='alice', password='pass')
        User.objects.create_user(username='bob', password='pass')
        order = Order.objects.create(user=alice, total=0)
        Item.objects.create(order=order, movie=movie, price=12, quantity=2)
        Item.objects.create(order=order, movie=movie, price=12, quantity=3)
        counts = {u.username: u.movies_bought for u in users_by_movies_bought()}
        self.assertEqual(counts, {'alice': 5, 'bob': 0})
