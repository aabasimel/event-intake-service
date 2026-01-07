from django.urls import path
from .views import EventView

urlpatterns = [
    path('v1/events', EventView.as_view(), name='events'),
]