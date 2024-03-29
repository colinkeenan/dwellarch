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
    assert bool(estate) ^ bool(building), "Either an estate or a building must \
            be chosen, but not both."

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

    def owners(self, ondate=datetime.date.today()):
        """returns a list of this propertie's owners ondate (default's to today)
        there should always be at least one owner because if a prop is entered
        without an owner, that form needs to be setup to default to the 'Not
        determined yet' owner"""
        transfers_beforedate = self.prop_transfers_set.filter(date__lte=ondate)
        relevant_date = transfers_beforedate.latest().date
        return list(transfers_beforedate.filter(date=relevant_date))

class Occupant(models.Model): # everone in the database is an occupant if have that info
    person = models.ForeignKey(people.Person) # can be a corporation or government agency
    units = models.ManyToManyField(Unit, through='OccupantTransfers', 
            null=True, blank=True, default=None) # history of dwellings for this occupant
    corporations = models.ManyToManyField('self', symmetrical=False, 
        through='ShareTransfer', related_name='shareholder') \
                # corporations this occupant has ever owned a share of

    def shareholders(self):
        return self.shareholder_set

    def total_shares(self):
        total = 0
        for shareholder in self.shareholders():
            total += shareholder.share_transfer__shares
        return total

    def shares_owned(self, corp):
        owned = 0
        for transfer in self.share_transfer_set.filter(corporation = corp):
            owned += transfer__shares
        return owned
    
    def full_address(self):
        """Returns a dictionary of this occupant's personal street address, unit, city, 
        state, and zip, and comes from the latest OccupantTransfers for this occupant"""
        return self.occupant_transfers_set.latest().full_address()

class Owner(models.Model):
    """The first owner in the database needs to be the first occupant in the database
    and be named 'Not determined yet.' so that users can enter addresses even if they
    can't determine the owner"""
    occupant = models.ForeignKey(Occupant) #this owner is an occupant somewhere
    props = models.ManyToManyField(Prop, through='PropTransfers')

class Manager(models.Model):
    occupant = models.ForeignKey(Occupant) #this manager is an occupant somewhere
    units = models.ManyToManyField(Unit, through='UnitManageRate')

class SubletLessor(models.Model):
    occupant = models.ForeignKey(Occupant) #this sublet-lessor is an occupant somewhere
    units = models.ManyToManyField(Unit, through='SubletRate')

class Payer(models.Model):
    payer_identity = models.ForeignKey(Occupant) # person, corporation, or agency
    payees = models.ManyToManyField(Occupant, through='PayRate')
    end_date = models.DateField(blank=True, null=True, default=None)
    end_reason = models.CharField(max_length=128)
    EMPLOYER = 'E'
    UNEMPLOYMENT = 'U'
    FOODSTAMPS = 'F'
    SSI = 'I'
    TANF = 'T'
    SECTION8 = '8'
    DISABILITY = 'D'
    RETIREMENT = 'R'
    SURVIVOR = 'S'
    PENSION = 'P'
    CHILDSUPPORT = 'C'
    ALIMONY = 'A'
    GUARDIAN = 'G'
    SELF = 'L'
    OTHER = 'O'
    PAYER_TYPE_CHOICES = (
            (EMPLOYER, 'Employer'),
            (UNEMPLOYMENT, 'Unemployment Insurance'),
            (FOODSTAMPS, 'Social Services: Food Stamps'),
            (SSI, 'Social Services: SSI'),
            (TANF, 'Social Services: TANF'),
            (SECTION8, 'Public Housing Authority: Section 8'),
            (DISABILITY, 'Social Security: Disability of self/spouse/parent)'),
            (RETIREMENT, 'Social Security: Retirement of self/spouse/parent)'),
            (SURVIVOR, 'Social Security: Survivor'),
            (PENSION, 'Pension'),
            (CHILDSUPPORT, 'Former Spouse: Child Support'),
            (ALIMONY, 'Former Spouse: Alimony'),
            (GUARDIAN, 'Parent/Guardian'),
            (SELF, 'Self'),
            (OTHER, 'Other'),
    )
    payer_type = models.CharField(help_text='What type of agency is paying?',
            max_length=1, choices=PAYER_TYPE_CHOICES, default=EMPLOYER)
    description = models.CharField(help_text='Additional information about \
            this source of income.',max_length=128)

class Rate(models.Model):
    """Abstract class inherited by anything that needs a rate like UnitRate for
    rent, or UnitManageRate for paying managers, or PayRate for job income"""
    date = models.DateField('start date')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    HOURLY = 'HO'    # building up choices for the rate-period 
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
    frequency = models.CharField(help_text= 'Choose how often payment is made', 
            max_length=2, choices=PERIOD_CHOICES, default=MONTHLY)
    deadline = models.CharField(help_text="Examples: 'The first of every\
            month', 'By Noon every Monday', 'Every December 31'", max_length=32)
    info = models.CharField(help_text='Enter any additional relevant \
            information about the rate.', max_length=64)

    class Meta:
        abstract = True
        get_latest_by = 'date'
        ordering = ['-date'] 

class UnitRate(Rate):
    unit = models.ForeignKey(Unit)

class UnitManageRate(Rate):
    manager = models.ForeignKey(Manager)
    unit = models.ForeignKey(Unit)

class SubletRate(Rate):
    sublet_lessor = models.ForeignKey(SubletLessor)
    unit = models.ForeignKey(Unit)

class PayRate(Rate):
    payer = models.ForeignKey(Payer)
    payee = models.ForeignKey(Occupant)

class Unit(models.Model):
    prop = models.ForeignKey(Prop)
    number = models.CharField('unit number or name', help_text='examples: Apt 1A \
            or Front Bedroom. Leave blank if the entire property is one dwelling \
            unit, such as a single-family home. If there are multiple buildings \
            with dwelling units in each and all the buildings are on land with \
            the same address, then this unit number or name must be unique and so \
            should contain the building name or number.', 
            max_length=32, blank=True)

    def full_address(self):
        """Returns a dictionary of street address, unit number, city, state, zip"""
        address = self.prop.address()
        city = self.prop.city()
        state = self.prop.state()
        zip_code = self.prop.zip_code()
        return {'address':address, 'unit':self.number, 'city':city, 'state':state, 
                'zip_code':zip_code}

    def landlords(self, ondate=datetime.date.today()):
        """For 'ondate', returns a list of owners of the unit's prop (property)
        Usually, there will be just one or two owners in the list."""
        return self.prop.owners(ondate)

    def managers(self, ondate=datetime.date.today()):
        """Returns a list of managers for the given ondate, defaults to the 
        landlords if there aren't any managers for this unit."""
        manager_rates_beforedate = self.unit_manage_rate_set.filter(date__lte=ondate)
        if bool(manager_rates_beforedate):
            relevant_date = manager_rates_beforedate.latest().date
            return list(manager_rates_beforedate.filter(date=relevant_date))
        else:
            return self.landlords(ondate)

    def sublet_lessors(self, ondate=datetime.date.today()):
        """Returns a list of sublet-lessors for ondate. Will be an empty
        list most of the time"""
        sublet_rates_beforedate = self.sublet_rate_set.filter(date__lte=ondate)
        if bool(sublet_rates_beforedate):
            relevant_date = sublet_rates_beforedate.latest().date
            return list(sublet_rates_beforedate.filter(date=relevant_date))
        else:
            return []

class PropTransfers(models.Model):
    owner = models.ForeignKey(Owner)
    prop = models.ForeignKey(Prop)
    date = models.DateField('sale date')
    price = models.DecimalField('sale price', max_digits=14, 
            decimal_places=2)

    class Meta: 
        get_latest_by = 'date'
        ordering = ['-date'] #lists of prop transfers are ordered current first 

class OccupantTransfers(models.Model):
    unit = models.ForeignKey(Unit)
    occupant = models.ForeignKey(Occupant, help_text='Choose an occupant. \
            Leave blank if vacant.', null=True, blank=True, default=None)
    date = models.DateField('rental date', help_text='If nobody lives here, \
            enter the date that this unit became vacant.')
    eviction_date = models.DateField(help_text='Leave blank until this \
            occupant is evicted, if ever.', blank=True, null=True, default=None)

    def full_address(self):
        """Returns a dictionary of street address, unit, city, state, and zip"""
        return self.unit.full_address()

    def landlords(self):
        """Returns a list of landlords for the unit on the rental date.
        Usually, there will be just one or two landlords in the list."""
        return self.unit.landlords(self.date)

    class Meta: 
        get_latest_by = 'date'
        ordering = ['-date'] #lists of occupant transfers are ordered current first 

class Conviction(models.Model):
    occupant = models.ForeignKey(Occupant) #the person convicted
    date = models.DateField(Date)
    offense = models.CharField(max_length=64)
    county = models.CharField(max_length=64)
    state = USPostalCodeField
    doc = models.CharField(help_text='Enter D.O.C. ID Number, if known', 
            blank=True, max_length=64)
    po = models.CharField(help_text='If currently on parole or probation, include \
            P.O. name and phone number.', blank=True, max_length=128)

class Immunization(models.Model):
    occupant = models.ForeignKey(Occupant)
    doctor = models.ForeignKey(Occupant, blank=True, null=True, default=None)
    shot_name = models.CharField(max_length=16)
    date = models.DateField()
    expires = models.DateField()

class PetShots(models.Model):
    pet = models.ForeignKey(people.Pet)
    vet = models.ForeignKey(Occupant)
    shot_name = models.CharField(max_length=16)
    tag_number = models.CharField(max_length=16, help_text='Enter the number \
    from the tag associated with this shot, if there is a tag.', blank=True)
    date = models.DateField()
    expires = models.DateField()

class PetLicense(models.Model):
    pet = models.ForeignKey(people.Pet)
    agency = models.ForeignKey('pet licensing agency', Occupant)
    tag_number = models.CharField(max_length=16)
    date = models.DateField()
    expires = models.DateField()

class ShareTransfer(models.Model):
    """This is just to keep track of all the owners (shareholders) of a 
    corporation. In general, neither the dwelarch project, nor this 
    dwellings application, should be used for tracking financial details 
    of a corporation"""
    shareholder = models.ForeignKey(Occupant)
    corporation = models.ForeignKey(Occupant)
    transfer_date = models.DateField()
    shares_transfered = models.IntegerField(help_text='Enter a positive \
            number for shares purchased, and a negative number for \
            shares sold')

    class Meta: 
        get_latest_by = 'purchase_date'
        ordering = ['-date'] 
