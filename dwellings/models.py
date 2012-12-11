import people, places, datetime
import datetime
from django.utils import timezone
from django import forms
from django_localflavor_us.forms import USPhoneNumberField, USPSSelect, USSocialSecurityNumberField, USZipCodeField
from django_localflavor_us.models import PhoneNumberField, USPostalCodeField # two-letter postal codes: state/territory/country
from django.db import models

class LandTransfers(models.Model):
    owner = models.ForeignKey(Owner)
    land = models.ForeignKey(places.Land)
    date = models.DateField('sale date')
    price = models.DecimalField('sale price', max_digits=14, 
            decimal_places=2)

class Owner(models.Model):
    birth = models.ForeignKey(people.Birth)
    lands = models.ManyToManyField(places.Land, through='LandTransfers')

class OccupantTransfers(models.Model):
    unit = models.ForeignKey(Unit)
    birth = models.ForeignKey(people.Birth, help_text='Choose an Occupant or \
            Lessor. Leave blank if vacant.', null=True, blank=True, default=None)
    date = models.DateField('rental date', help_text='If nobody lives here, \
            enter the date that this unit became vacant.')

class Unit(models.Model):
    building = models.ForeignKey(places.Building)
    number = models.CharField('unit number or name', help_text='examples: 1A \
            or Front Bedroom. Leave blank if the entire building is one dwelling \
            unit, such as a single-family home.', 
            max_length=32, blank=True)
    births = models.ManyToManyField(people.Birth, through='OccupantTransfers', 
            null=True, blank=True, default=None) # occupants or lessors

class UnitRate(models.Model):
    unit = models.ForeignKey(Unit)
    rent = models.DecimalField(max_digits=9, decimal_places=2)
    HOURLY = 'HO'    # building up choices for the rental period
    DAILY = 'DA'
    WEEKLY = 'WE'
    TWICE-A-MONTH = 'TW'
    MONTHLY = 'MO'
    2MONTHLY = '2M'
    3MONTHLY = '3M'
    6MONTHLY = '6M'
    YEARLY = 'YE'
    NEVER = 'NE'
    PERIOD_CHOICES = (
            (HOURLY, 'Hourly'),
            (DAILY, 'Daily'),
            (WEEKLY, 'Weekly'),
            (TWICE-A-MONTH, 'Twice-a-month'),
            (MONTHLY, 'Monthly'),
            (2MONTHLY, 'Every-two-months'),
            (3MONTHLY, 'Every-three-months'),
            (6MONTHLY, 'Every-six-months'),
            (YEARLY, 'Yearly'),
            (NEVER, 'Never'),
    )
    rent_frequency = models.CharField(help_text= 'Choose how often rent is due', 
            max_length=2, choices=PERIOD_CHOICES, default=MONTHLY)
    rent_deadline = models.CharField(help_text="Examples: 'The first of every\
            month', 'By Noon every Monday', 'Every December 31'", max_length=32)
    rent_info = models.CharField(help_text='Enter any additional relevant \
            information about the rent.', max_length=64)
