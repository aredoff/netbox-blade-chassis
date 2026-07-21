from django.urls import path

from netbox_blade_chassis.api import views

app_name = 'netbox_blade_chassis-api'

urlpatterns = [
    path('racks/<int:pk>/elevation/', views.RackElevationAPIView.as_view(), name='rack-elevation'),
]
