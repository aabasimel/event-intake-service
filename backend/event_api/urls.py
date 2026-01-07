from django.urls import path
from .views import EventCreateView

urlpatterns = [
    path('v1/events', EventCreateView.as_view(), name='create-event'),
]