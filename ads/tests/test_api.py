from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from ..models import Ad, ExchangeProposal
from rest_framework_simplejwt.tokens import RefreshToken


class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', password='password123')
        self.user2 = User.objects.create_user(
            username='user2', password='password123')

        # Create test ads (enough to test pagination)
        for i in range(1, 12):  # Creates 11 ads (more than PAGE_SIZE of 9)
            Ad.objects.create(
                user=self.user1 if i % 2 else self.user2,
                title=f'Ad {i}',
                description=f'Description {i}',
                category='electronics' if i % 2 else 'books',
                condition='new' if i % 2 else 'used'
            )

        # Get created ads for reference
        self.ads = Ad.objects.all().order_by('id')
        self.ad1 = self.ads[0]  # user1's ad
        self.ad2 = self.ads[1]  # user2's ad

        # Create test proposals (enough to test pagination)
        for i in range(1, 12):  # Creates 11 proposals
            ExchangeProposal.objects.create(
                ad_sender=self.ad1 if i % 2 else self.ad2,
                ad_receiver=self.ad2 if i % 2 else self.ad1,
                comment=f'Proposal {i}',
                status='accepted' if i % 3 == 0 else 'pending'
            )

        # Get created proposals for reference
        self.proposals = ExchangeProposal.objects.all()

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


class AdAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('api_ad_list')
        self.detail_url = lambda pk: reverse('api_ad_detail', kwargs={'pk': pk})

    def test_list_ads_pagination(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)

        self.assertEqual(response.data['count'], 11)
        self.assertEqual(len(response.data['results']), 9)
        response = self.client.get(self.list_url, {'page': 2})
        self.assertEqual(len(response.data['results']), 2)

    def test_list_ads_unauthenticated(self):
        """Unauthenticated users can list ads (read-only)"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 11)

    def test_filter_ads_with_pagination(self):
        """Test that filters work with pagination"""
        response = self.client.get(self.list_url, {'category': 'electronics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['results']), 6)
        for ad in response.data['results']:
            self.assertEqual(ad['category'], 'electronics')

    def test_filter_ads_by_condition(self):
        response = self.client.get(self.list_url, {'condition': 'used'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(len(response.data['results']), 5)
        for ad in response.data['results']:
            self.assertEqual(ad['condition'], 'used')

    def test_filter_ads_by_user(self):
        response = self.client.get(self.list_url, {'user': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(len(response.data['results']), 5)
        for ad in response.data['results']:
            self.assertEqual(ad['user']['id'], self.user2.id)

    def test_search_ads(self):
        response = self.client.get(self.list_url, {'search': 'Description 2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_ad_unauthenticated(self):
        data = {
            'title': 'New Ad',
            'description': 'New Description',
            'category': 'books',
            'condition': 'new'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_ad_authenticated(self):
        self.authenticate(self.user1)
        data = {
            'title': 'New Ad',
            'description': 'New Description',
            'category': 'books',
            'condition': 'new'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ad.objects.count(), 12)
        self.assertEqual(response.data['user'], self.user1.id)

    def test_retrieve_ad(self):
        url = self.detail_url(self.ad1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Ad 1')

    def test_update_ad_owner(self):
        self.authenticate(self.user1)
        url = self.detail_url(self.ad1.id)
        data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'category': 'electronics',
            'condition': 'used'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ad1.refresh_from_db()
        self.assertEqual(self.ad1.title, 'Updated Title')

    def test_update_ad_non_owner(self):
        self.authenticate(self.user2)
        url = self.detail_url(self.ad1.id)
        data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'category': 'electronics',
            'condition': 'used'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_ad_owner(self):
        self.authenticate(self.user1)
        url = self.detail_url(self.ad1.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ad.objects.count(), 10)

    def test_delete_ad_non_owner(self):
        self.authenticate(self.user2)
        url = self.detail_url(self.ad1.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Ad.objects.count(), 11)


class ExchangeProposalAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('api_proposal_list')
        self.detail_url = lambda pk: reverse('api_proposal_detail', kwargs={'pk': pk})
        self.proposal1 = self.proposals[0]
        self.proposal2 = self.proposals[1]

    def test_list_proposals_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_proposals_authenticated(self):
        self.authenticate(self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # user1 is involved in both proposals (as sender in proposal1, as receiver in proposal2)
        self.assertEqual(response.data['count'], 11)
        results = response.data['results']
        self.assertEqual(len(results), 9)

    def test_filter_proposals_by_status(self):
        self.authenticate(self.user1)
        response = self.client.get(self.list_url, {'status': 'accepted'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['status'], 'accepted')

    def test_filter_proposals_by_ad_sender(self):
        self.authenticate(self.user1)
        response = self.client.get(self.list_url, {'ad_sender': self.ad1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 6)
        self.assertEqual(results[0]['ad_sender']['id'], self.ad1.id)

    def test_filter_proposals_by_ad_receiver(self):
        self.authenticate(self.user1)
        response = self.client.get(self.list_url, {'ad_receiver': self.ad2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 6)
        self.assertEqual(results[0]['ad_receiver']['id'], self.ad2.id)

    def test_create_proposal_unauthenticated(self):
        data = {
            'ad_sender_id': self.ad1.id,
            'ad_receiver_id': self.ad2.id,
            'comment': 'New proposal'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_proposal_authenticated(self):
        self.authenticate(self.user1)
        data = {
            'ad_sender_id': self.ad1.id,
            'ad_receiver_id': self.ad2.id,
            'comment': 'New proposal'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExchangeProposal.objects.count(), 12)

    def test_create_proposal_to_self(self):
        self.authenticate(self.user1)
        data = {
            'ad_sender_id': self.ad1.id,
            'ad_receiver_id': self.ad1.id,
            'comment': 'New proposal to self'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_proposal_with_others_ad(self):
        self.authenticate(self.user1)
        data = {
            'ad_sender_id': self.ad2.id,  # user2's ad
            'ad_receiver_id': self.ad2.id,
            'comment': 'New proposal with others ad'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_proposal_participant(self):
        self.authenticate(self.user1)
        url = self.detail_url(self.proposal1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comment'], 'Proposal 1')

    def test_retrieve_proposal_non_participant(self):
        # Create a new user who isn't involved in any proposals
        user3 = User.objects.create_user(username='user3', password='password123')
        self.authenticate(user3)
        url = self.detail_url(self.proposal1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_proposal_status_receiver(self):
        self.authenticate(self.user1)  # user1 is receiver of proposal2
        url = self.detail_url(self.proposal2.id)
        data = {'status': 'rejected'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.proposal2.refresh_from_db()
        self.assertEqual(self.proposal2.status, 'rejected')

    def test_update_proposal_status_non_receiver(self):
        self.authenticate(self.user2)  # user2 is sender of proposal2, not receiver
        url = self.detail_url(self.proposal2.id)
        data = {'status': 'rejected'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
