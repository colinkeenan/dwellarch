import people, places, datetime
import datetime
from django.utils import timezone
from django import forms
from django_localflavor_us.forms import USPhoneNumberField, USPSSelect, USSocialSecurityNumberField, USZipCodeField
from django_localflavor_us.models import PhoneNumberField, USPostalCodeField # two-letter postal codes: state/territory/country
from django.db import models

class Prop(models.Model):
    """Prop is short for property and should always have owners.
    The default owner will be 'Not determined yet.' so that
    users can enter new properties for the purpose of entering
    addresses even if they can't determine the owner.

    A prop is either an estate or a building, but not both. 
    
    If an estate and it's buildings all have the same owners, props and owners 
    should be specified for the estate only, not the buildings."""

    estate = models.OneToOneField(places.Estate, 
            null=True, blank=True, default=None)
    building = models.OneToOneField(places.Building, 
            null=True, blank=True, default=None)
    assert bool(estate) ^ bool(building) #one and only one should be given

    def land(self):
        return self.estate or self.building.estate

    def address(self):
        return self.land().address

    def city(self):
        return self.land().city

    def state(self):
        return self.land().state

    def zip_code(self):
        return self.land().zip_code

    def owners(self, date):
        """returns a list of this propertie's owners on 'date'"""
        relevant_date = self.prop_transfers_set.filter(date__lte=date).latest('date').date
        return list(self.owners_set.filter(prop_transfers__date=relevant_date))

class Owner(models.Model):
    """The first owner needs to be the first birth and be named 'Not determined yet.'
    so that users can enter addresses even if they can't determine the owner"""
    birth = models.ForeignKey(people.Birth)
    props = models.ManyToManyField(Prop, through='PropTransfers')

    def full_address(self):
        """Returns a dictionary of this owner's personal street address, unit, city, 
        state, and zip, and comes from the latest OccupantTransfers that matches the 
        owner's birth foreign key, where the unit can be a whole house and an occupant 
        can be an owner. 
        Any non-owners living there are tenants even if they don't pay anything 
        and are handled by Tenant(models.Model). It is not assumed that the
        owner lives on his own property though. An owner can also be a tenant."""
        return self.birth.occupant_transfers_set.latest('date').full_address()

class Tenant(models.Model): # everone in the database is either an owner or a tenant
    birth = models.ForeignKey(people.Birth)
    
    def full_address(self):
        """Returns a dictionary of this tenant's personal street address, unit, city, 
        state, and zip, and comes from the latest OccupantTransfers that matches the 
        birth foreign key."""
        return self.birth.occupant_transfers_set.latest('date').full_address()

class PropTransfers(models.Model):
    owner = models.ForeignKey(Owner)
    prop = models.ForeignKey(Prop)
    date = models.DateField('sale date')
    price = models.DecimalField('sale price', max_digits=14, 
            decimal_places=2)

class OccupantTransfers(models.Model):
    unit = models.ForeignKey(Unit)
    birth = models.ForeignKey(people.Birth, help_text='Choose an Occupant or \
            Lessor. Leave blank if vacant.', null=True, blank=True, default=None)
    date = models.DateField('rental date', help_text='If nobody lives here, \
            enter the date that this unit became vacant.')

    def full_address(self):
        """Returns a dictionary of street address, unit, city, state, and zip"""
        return self.unit.full_address()

    def landlords(self):
        """Returns a list of landlords for the unit on the rental date.
        Usually, there will be just one or two landlords in the list."""
        return self.unit.landlords(self.date)

class Unit(models.Model):
    prop = models.ForeignKey(Prop)
    number = models.CharField('unit number or name', help_text='examples: Apt 1A \
            or Front Bedroom. Leave blank if the entire property is one dwelling \
            unit, such as a single-family home. If there are multiple buildings \
            with dwelling units in each and all the buildings are on land with \
            the same address, then this unit number or name must be unique and so \
            should contain the building name or number.', 
            max_length=32, blank=True)
    births = models.ManyToManyField(people.Birth, through='OccupantTransfers', 
            null=True, blank=True, default=None) # occupants or lessors

    def full_address(self):
        """Returns a dictionary of street address, unit number, city, state, zip"""
        address = self.prop.address()
        city = self.prop.city()
        state = self.prop.state()
        zip_code = self.prop.zip_code()
        return {'address':address, 'unit':self.number, 'city':city, 'state':state, 'zip_code':zip_code}

    def landlords(self, date):
        """For 'date', returns a list of owners of the unit's prop (property)
        Usually, there will be just one or two owners in the list."""
        return self.prop.owners(date):

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

