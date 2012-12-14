import datetime
from django.utils import timezone
from django import forms
from django_localflavor_us.forms import USPhoneNumberField, USPSSelect, USSocialSecurityNumberField, USZipCodeField
from django_localflavor_us.models import PhoneNumberField, USPostalCodeField # two-letter postal codes: state/territory/country
from django.db import models

class Name(models.Model):
    date = models.DateField('date of birth or name change')
    prime_given_name = models.CharField('first given name', 
            max_length=32, blank=True)
    other_given_name = models.CharField('middle given names', 
            max_length=64, blank=True)
    first_family_name = models.CharField(
            'first family name (surname)', help_text=
            'Required. If this person only has one name, put it here.',
            max_length=32)
    second_family_name = models.CharField(
            "second family name or mother's maiden name", 
            max_length=32, blank=True)
    use1st = models.BooleanField(help_text=
            'Use this name in last name?', default=True)
    use2nd = models.BooleanField(help_text=
            'If both family names are used, the last name will be hyphenated.',
            default=False)

    def last(self):
        return ('{}-{}'.format(self.first_family_name, self.second_family_name) if
                self.use1st and self.use2nd else
                self.second_family_name if self.use2nd else
                self.first_family_name)

    def __str__(self):
        return '{} {} {}'.format(
                self.prime_given_name, self.other_given_name, self.last())

    class Meta:
        abstract = True
        get_latest_by = 'date'
        ordering = ['-date'] # history of names for a person are returned current first 

class Birth(Name):
    # name fields and the birthdate as Birth#date is inherited from Name()
    social_security_num = models.CharField(max_length=11, blank=True)

class Nick(models.Model):
    """A person should only have one nickname at a time and then only as an easy
    way for people to refer to them. A person never pretends that their nickname
    is their real name: that would be an alias. See isAlias method of NameChange."""
    birth = models.ForeignKey(Birth)
    date = models.DateField('date began using this nickname', help_text='Enter the \
            date this nickname started to be used. If stopped using the previous \
            one, enter the date no longer used and leave the nickname blank.')
    name = models.CharField('nickname', help_text='Enter new nickname. If stopped \
            using the previous nickname, indicate by leaving this blank.', 
            max_length=32, blank=True)

class NameChange(Name):
    # inherits name fields and the NameChange#date from Name()
    birth = models.ForeignKey(Birth)
    reason = models.CharField('reason name was changed', max_length=64) 
    
    COURT = 'CO'    # building up choices for the method of name change
    MARRIAGE = 'MA'
    DIVORCE = 'DI'
    ADOPTION = 'AD'
    NATURALIZATION = 'NA'
    PSEUDONYM = 'PS'
    METHOD_CHOICES = (
            (COURT, 'Court Order'),
            (MARRIAGE, 'Marriage'),
            (DIVORCE, 'Divorce'),
            (ADOPTION, 'Adoption'),
            (NATURALIZATION, 'Naturalization'),
            (PSEUDONYM, 'Pseudonym'),
    )
    method = models.CharField(help_text=
            'Choose which method was used for this name-change.',
            max_length=2, choices=METHOD_CHOICES, default=COURT)
    method_info = models.CharField('additional method information',
            help_text='Enter additional information about the name change \
                    such as the court and document number', 
                    max_length=32, blank=True)

    def isAlias(self):
        """returns True if self hasn't been registered:
        i.e., True if there are no NameRegistration children of self """
        return not self.name_registration_set.exists()

class NameRegistration(models.Model):
    name_change = models.ForeignKey(NameChange)
    date = models.DateField("this name's registration-date")

    SSA = 'SSA' # building up choices of where the new name was registered
    BCA = 'BCA'
    USPS = 'USP'
    DMV = 'DMV'
    SECSTATE = 'SOS'
    COUNTYCL = 'COC'
    OTHER = 'OTH'
    REGISTRATION_CHOICES = (
            (SSA, 'Social Security Administration'),
            (BCA, 'Bureau of Consular Affairs'),
            (USPS, 'United States Postal Service'),
            (DMV, 'Department of Motor Vehicles'),
            (SECSTATE, 'Secretary of State'),
            (COUNTYCL, 'County Clerk'),
            (OTHER, 'Other'),
    )
    registration = models.CharField(help_text=
            'Choose where this name was registered', 
            max_length=3, choices=REGISTRATION_CHOICES, default=SSA)
    reg_info = models.CharField('registration information', help_text=
            'Enter additional relevant information like state, county, \
                    or details about "Other" such as the Company Name \
                    of the Employer/Bank/Doctor/Mortgage/Insurance/\
                    Credit Card...', 
                    max_length=64, blank=True) 

class IdDoc(models.Model):
    birth = models.ForeignKey(Birth)
    name = models.CharField('identification-document name', 
            help_text='For example: Missouri Driver License', max_length=16)
    number = models.CharField(max_length=32)
    date = models.DateField('id issue date')
    expire = models.DateField('id expiration date', blank=True)
    info = models.CharField(max_length=32, blank=True)

class Phone(models.Model):
    birth = models.ForeignKey(Birth)
    start_date = models.DateField('service start date', help_text=
            'Enter date this phone number went into service for this person \
                    with this carrier. Leave blank if that date cannot be determined.', 
                    blank=True, null=True, default=None)
    end_date = models.DateField('service end date', help_text=
            'Enter date this phone number for this person ended with this carrier. \
                    Leave blank if that date cannot be determined.', 
                    blank=True, null=True, default=None)
    valid_date = models.DateField(help_text='Enter a date when this phone \
            number was a valid way to contact this person.')
    invalid_date = models.DateField(help_text'Enter a date when this phone \
            number was no longer a valid way to contact this person.')
    phone_number = PhoneNumberField()
    carrier = models.CharField('carrier and type', help_text=
            "Enter phone-service provider's name and/or type \
                    (contract/prepaid/landline/voip/virtual). \
                    Leave blank if both provider and type cannot be determined.", 
                    blank=True, max_length=64)
    private = models.BooleanField(help_text='If marked as private, this phone \
            number will not be visible to other users of the database unless \
            given on a form like a rental applicaton. Anyone owning rental \
            units may gain access to any rental application in the database.')
    belongs = models.NullBooleanField('belongs to this person', help_text='Does/did this \
            phone number belong to this person? Should be checked if a service start date \
            was entered.')
    assert belongs==True if bool(start_date), "Since there's a date for this phone number \
            going into service for this person, you must check off the box showing this \
            phone number does/did belong to this person. If this phone number never \
                    really belonged to this person, delete the service start date."

class Email(models.Model):
    birth = models.ForeignKey(Birth)
    date = models.DateField('email-signup date')
    addr = models.EmailField('email', max_length=254)
    term = models.DateField('email-termination date')

class Profile(models.Model):
    birth = models.ForeignKey(Birth)
    date = models.DateField('online-profile creation date')
    uri = models.URLField('online-profile link')
    del_date = models.DateField('online-profile deletion date')
    
