import people, places, datetime
import datetime
from django.utils import timezone
from django import forms
from django_localflavor_us.forms import USPhoneNumberField, USPSSelect, USSocialSecurityNumberField, USZipCodeField
from django_localflavor_us.models import PhoneNumberField, USPostalCodeField # two-letter postal codes: state/territory/country
from django.db import models

class LandTransfers(models.Model):
    owner = models.ForeignKey(Owner)
    land = models.ForeignKey(Land)
    date = models.DateField('sale date')
    price = models.DecimalField('sale price', max_digits=14, decimal_places=2)

class Owner(models.Model):
    birth = models.ForeignKey(people.Birth)
    lands = models.ManyToManyField(places.Land, through = 'LandTransfers')

    def isLandlord(self):
        """ returns True if self has rental units """
        return self.rental_unit_set.exists()
