import datetime
from django.utils import timezone
from django import forms
from django_localflavor_us.forms import USPhoneNumberField, USPSSelect, USSocialSecurityNumberField, USZipCodeField
from django_localflavor_us.models import PhoneNumberField, USPostalCodeField # two-letter postal codes: state/territory/country
from django.db import models

class Land(models.Model):
    tax_parcel_number = models.CharField(max_length=64, blank=True)
    tax_property_description = models.CharField(max_length=64, blank=True)
    address = models.CharField(max_length=64)
    city = models.CharField(max_length=32)
    state = USPostalCodeField
    zip_code = models.CharField(max_length=10)

class Building(models.Model):
    land = models.ForeignKey(Land)
    date = models.DateField('date of construction')
    building_area = models.CharField(max_length=16, blank=True)
    bedrooms = models.IntegerField(blank=True)
    bathrooms = models.IntegerField(blank=True)
    partial_bathrooms = models.IntegerField(blank=True)
    rooms = models.IntegerField(blank=True)
    pool = models.CharField(max_length=16, blank=True)
    fire_place = models.CharField(max_length=16, blank=True)
    type_construction = models.CharField(max_length=16, blank=True) 
    number_of_stories = models.IntegerField(blank=True)
    style = models.CharField(max_length=16, blank=True)
    basement = models.CharField(max_length=16, blank=True)
    roof cover = models.CharField(max_length=16, blank=True)
    foundation = models.CharField(max_length=16, blank=True)
    elevator = models.CharField(max_length=16, blank=True)
