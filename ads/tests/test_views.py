from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Ad, ExchangeProposal
from ..forms import AdForm, ProposalForm


class BarterPlatformTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )

        self.ad1 = Ad.objects.create(
            user=self.user1,
            title='iPhone 13',
            description='Like new iPhone',
            category='electronics',
            condition='used',
            image_url='http://example.com/iphone.jpg'
        )

        self.ad2 = Ad.objects.create(
            user=self.user2,
            title='MacBook Pro',
            description='2020 model',
            category='electronics',
            condition='used',
            image_url='http://example.com/macbook.jpg'
        )

        self.proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            comment='I want to trade my iPhone for your MacBook',
            status='pending'
        )

        self.client = Client()

    # ==============
    # Model Tests
    # ==============

    def test_ad_creation(self):
        self.assertEqual(self.ad1.title, 'iPhone 13')
        self.assertEqual(self.ad1.get_category_display(), 'Electronics')
        self.assertEqual(self.ad1.user.username, 'user1')

    def test_proposal_creation(self):
        self.assertEqual(self.proposal.ad_sender, self.ad1)
        self.assertEqual(self.proposal.ad_receiver, self.ad2)
        self.assertEqual(self.proposal.status, 'pending')

    # ==============
    # View Tests
    # ==============

    def test_ad_list_view(self):
        response = self.client.get(reverse('ad_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'iPhone 13')
        self.assertTemplateUsed(response, 'ads/ad_list.html')

    def test_ad_detail_view(self):
        url = reverse('ad_detail', kwargs={'pk': self.ad1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Like new iPhone')

    def test_ad_create_view_authenticated(self):
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('ad_create'))
        self.assertEqual(response.status_code, 200)

    def test_ad_create_view_unauthenticated(self):
        response = self.client.get(reverse('ad_create'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    # ==============
    # Form Tests
    # ==============

    def test_valid_ad_form(self):
        data = {
            'title': 'Test Ad',
            'description': 'Test description',
            'category': 'electronics',
            'condition': 'new'
        }
        form = AdForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_ad_form(self):
        data = {
            'title': '',
            'description': 'Test description',
            'category': 'invalid',
            'condition': 'new'
        }
        form = AdForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)

    def test_valid_proposal_form(self):
        data = {
            'ad_sender': self.ad2.pk,
            'comment': 'Test proposal'
        }
        form = ProposalForm(data=data)
        self.assertTrue(form.is_valid())

    # ==============
    # Feature Tests
    # ==============

    def test_search_functionality(self):
        response = self.client.get(reverse('ad_list') + '?search=iPhone')
        self.assertContains(response, 'iPhone 13')
        self.assertNotContains(response, 'MacBook Pro')

    def test_filter_functionality(self):
        response = self.client.get(
            reverse('ad_list') + '?category=electronics'
        )
        self.assertContains(response, 'iPhone 13')
        self.assertContains(response, 'MacBook Pro')

    def test_pagination(self):
        for i in range(15):
            Ad.objects.create(
                user=self.user1,
                title=f'Test Ad {i}',
                description='Test',
                category='electronics',
                condition='new'
            )
        response = self.client.get(reverse('ad_list'))
        self.assertContains(response, 'page=2')

    def test_proposal_creation_flow(self):
        self.client.login(username='user1', password='testpass123')
        url = reverse('send_proposal', kwargs={'ad_receiver_pk': self.ad2.pk})
        response = self.client.post(url, {
            'ad_sender': self.ad1.pk,
            'comment': 'Test proposal'
        })
        self.assertEqual(response.status_code, 302)

    def test_proposal_status_update(self):
        self.client.login(username='user2', password='testpass123')
        url = reverse('update_proposal_status', kwargs={'pk': self.proposal.pk})
        self.client.post(url, {'status': 'accepted'})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'accepted')

    # ==============
    # Permission Tests
    # ==============

    def test_edit_permission(self):
        self.client.login(username='user2', password='testpass123')
        url = reverse('ad_edit', kwargs={'pk': self.ad1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_permission(self):
        self.client.login(username='user2', password='testpass123')
        url = reverse('ad_delete', kwargs={'pk': self.ad1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Ad.objects.filter(pk=self.ad1.pk).exists())

    # ==============
    # Edge Cases
    # ==============

    def test_proposal_to_own_item(self):
        self.client.login(username='user1', password='testpass123')
        url = reverse('send_proposal', kwargs={'ad_receiver_pk': self.ad1.pk})
        response = self.client.post(url, {
            'ad_sender': self.ad1.pk,
            'comment': 'Invalid proposal'
        })
        self.assertEqual(response.status_code, 403)

    def test_nonexistent_ad(self):
        url = reverse('ad_detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
