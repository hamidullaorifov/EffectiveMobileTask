from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import AdForm, ProposalForm, ProposalStatusForm
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .models import Ad, ExchangeProposal


class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('ad_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class AdListView(ListView):
    model = Ad
    template_name = "ads/ad_list.html"
    context_object_name = "ads"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get("category")
        search_query = self.request.GET.get("search")
        condition = self.request.GET.get("condition")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )
        if category:
            queryset = queryset.filter(category=category)
        if condition:
            queryset = queryset.filter(condition=condition)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Ad.CATEGORY_CHOICES
        context['conditions'] = Ad.CONDITION_CHOICES
        return context


class AdCreateView(LoginRequiredMixin, CreateView):
    model = Ad
    form_class = AdForm
    template_name = "ads/ad_form.html"
    success_url = '/ads/'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('ad_detail', kwargs={'pk': self.object.pk})


class AdDetailView(DetailView):
    model = Ad
    template_name = "ads/ad_detail.html"
    context_object_name = "ad"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exchange_proposals'] = ExchangeProposal.objects.filter(
            Q(ad_sender=self.object) | Q(ad_receiver=self.object)
        )

        if self.request.user.is_authenticated:
            context['user_ads'] = Ad.objects.filter(user=self.request.user)

        ad_user = self.object.user
        proposal_counts = ExchangeProposal.objects.aggregate(
            sent_count=Count('id', filter=Q(ad_sender__user=ad_user)),
            received_count=Count('id', filter=Q(ad_receiver__user=ad_user))
        )

        context['user_proposals'] = proposal_counts
        return context


class AdUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ad
    form_class = AdForm
    template_name = "ads/ad_form.html"

    def get_success_url(self):
        return reverse_lazy('ad_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def test_func(self):
        ad = self.get_object()
        return self.request.user == ad.user


class AdDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ad
    template_name = "ads/ad_confirm_delete.html"
    success_url = reverse_lazy('ad_list')

    def test_func(self):
        ad = self.get_object()
        return self.request.user == ad.user


class ProposalCreateView(LoginRequiredMixin, CreateView):
    model = ExchangeProposal
    form_class = ProposalForm
    template_name = "ads/proposal_form.html"
    success_url = reverse_lazy('ad_list')

    def dispatch(self, request, *args, **kwargs):
        self.ad_receiver = get_object_or_404(Ad, pk=self.kwargs['ad_receiver_pk'])
        if self.ad_receiver.user == request.user:
            raise PermissionDenied("You cannot send a proposal for your own ad.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.ad_receiver = self.ad_receiver
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ad_receiver'] = Ad.objects.get(pk=self.kwargs['ad_receiver_pk'])
        context['user_ads'] = Ad.objects.filter(user=self.request.user).exclude(pk=self.kwargs['ad_receiver_pk'])
        return context


class ProposalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ExchangeProposal
    form_class = ProposalStatusForm
    template_name = "ads/proposal_status_form.html"
    context_object_name = "proposal"

    def get_success_url(self):
        return reverse_lazy('manage_proposals')

    def test_func(self):
        proposal = self.get_object()
        return self.request.user == proposal.ad_receiver.user


class ProposalListView(LoginRequiredMixin, ListView):
    model = ExchangeProposal
    template_name = "ads/proposals.html"
    context_object_name = "proposals"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset.filter(
            Q(ad_sender__user=user) | Q(ad_receiver__user=user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ExchangeProposal.STATUS_CHOICES

        user = self.request.user
        context['received_proposals'] = self.object_list.filter(ad_receiver__user=user)
        context['sent_proposals'] = self.object_list.filter(ad_sender__user=user)

        return context


def generate_ads(request):
    from django.contrib.auth.models import User
    import random
    ad_data = [
        {
            'title': 'iPhone 13 Pro - 128GB',
            'description': 'Like new iPhone 13 Pro with original box and accessories. Battery health 98%.',
            'image_url': 'https://example.com/iphone13.jpg',
            'category': 'electronics',
            'condition': 'new',
            'created_at': timezone.now() - timezone.timedelta(days=2)
        },
        {
            'title': 'Samsung Galaxy S21 Ultra',
            'description': 'Excellent condition, no scratches. Comes with case and screen protector.',
            'image_url': 'https://example.com/s21ultra.jpg',
            'category': 'electronics',
            'condition': 'used',
            'created_at': timezone.now() - timezone.timedelta(days=5)
        },
        {
            'title': 'Nike Air Jordan 1 Retro',
            'description': 'Size 10.5, worn twice. Original box included.',
            'image_url': 'https://example.com/jordans.jpg',
            'category': 'clothing',
            'condition': 'used',
            'created_at': timezone.now() - timezone.timedelta(days=1)
        },
        {
            'title': 'Harry Potter Book Set',
            'description': 'Complete 7-book collection in great condition. No markings inside.',
            'image_url': 'https://example.com/harrypotter.jpg',
            'category': 'books',
            'condition': 'used',
            'created_at': timezone.now() - timezone.timedelta(hours=3)
        },
        {
            'title': 'Instant Pot Duo 7-in-1',
            'description': 'Brand new in box. Never opened.',
            'image_url': 'https://example.com/instantpot.jpg',
            'category': 'home',
            'condition': 'new',
            'created_at': timezone.now() - timezone.timedelta(days=7)
        },
        {
            'title': 'Vintage Leather Jacket',
            'description': 'Genuine leather, size M. Some wear but still stylish.',
            'image_url': 'https://example.com/jacket.jpg',
            'category': 'clothing',
            'condition': 'broken',
            'created_at': timezone.now() - timezone.timedelta(days=10)
        },
        {
            'title': 'Bose QuietComfort 35 II',
            'description': 'Wireless headphones with excellent noise cancellation. Includes carrying case.',
            'image_url': 'https://example.com/bose.jpg',
            'category': 'electronics',
            'condition': 'used',
            'created_at': timezone.now() - timezone.timedelta(hours=12)
        },
        {
            'title': 'IKEA KALLAX Shelf Unit',
            'description': 'White 4x2 cube organizer. Some scratches but fully functional.',
            'image_url': 'https://example.com/kallax.jpg',
            'category': 'home',
            'condition': 'used',
            'created_at': timezone.now() - timezone.timedelta(days=3)
        },
        {
            'title': 'Nintendo Switch OLED',
            'description': 'Complete set with dock, 2 joycons, and Mario Kart game.',
            'image_url': 'https://example.com/switch.jpg',
            'category': 'electronics',
            'condition': 'new',
            'created_at': timezone.now() - timezone.timedelta(hours=1)
        },
        {
            'title': 'Designer Sunglasses',
            'description': 'Ray-Ban Wayfarer, authentic. Minor scratch on left lens.',
            'image_url': 'https://example.com/rayban.jpg',
            'category': 'other',
            'condition': 'broken',
            'created_at': timezone.now() - timezone.timedelta(days=15)
        }
    ]
    users = User.objects.all()
    for ad in ad_data:
        Ad.objects.create(
            user=random.choice(users),
            title=ad['title'],
            description=ad['description'],
            category=ad['category'],
            condition=ad['condition'],
            created_at=ad['created_at']
        )
    return HttpResponse("Ads generated successfully.")
