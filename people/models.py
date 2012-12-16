import datetime
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from django_localflavor_us.forms import USPhoneNumberField, USPSSelect, USSocialSecurityNumberField, USZipCodeField
from django_localflavor_us.models import PhoneNumberField, USPostalCodeField # two-letter postal codes: state/territory/country
from django.db import models

class Person(models.Model):
    """The purpose of this class is to supply an id for a person in the database.
    The only thing I could think to track here that shouldn't change through
    a person's life is their race/ethnicity/ancestory, but it can all be left blank."""
    # check all that apply
    hispanic_or_latino = models.NullBooleanField()
    white_or_caucasian = models.NullBooleanField()
    european = models.NullBooleanField()
    middle_eastern = models.NullBooleanField()
    arab_world_african = models.NullBooleanField()
    black_african = models.NullBooleanField()
    american_indian = models.NullBooleanField()
    eskimo_or_inuit = models.NullBooleanField()
    asian = models.NullBooleanField()
    pacific_islander = models.NullBooleanField()
    hawaiin = models.NullBooleanField()
    other = models.NullBooleanField()
    additional_ancestory_information = models.CharField(max_length=64, blank=True)

    def allCurrentNames(self):
        """returns list of (name,type) where isCurrent() is True
        and type is either 'registered', 'pseudonym' or 'alias'"""
        pass

    def allNamesFor(self, date):
        """returns all names that were current on date"""
        pass

    def theProperPseudonym(self):
        """returns the registered pseudonym like some authors 
        or actors have, if it exists"""
        pass

class Nick(models.Model):
    """A person should only have one nickname at a time and then only as an easy
    way for people to refer to them. A person never pretends that their nickname
    is their real name: that would be an alias. See isAlias method of NameChange."""
    person = models.ForeignKey(Person)
    date = models.DateField('date began using this nickname', help_text='Enter the \
            date this nickname started to be used. If stopped using the previous \
            one, enter the date no longer used and leave the nickname blank.')
    name = models.CharField('nickname', help_text='Enter new nickname. If stopped \
            using the previous nickname, indicate by leaving this blank.', 
            max_length=32, blank=True)

class Name(models.Model):
    date = models.DateField('date first used', help_text='Enter \
            best estimate of the date this name was first used.')
    prime_given_name = models.CharField('first given name', 
            max_length=32, blank=True)
    other_given_name = models.CharField('middle given names', 
            max_length=64, blank=True)
    first_family_name = models.CharField(
            'first family name (surname)', help_text=
            'Required. If the full name is just one name, put it here and leave \
                    the other name fields blank.',
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

    def full_name(self):
        return '{} {} {}'.format(
                self.prime_given_name, self.other_given_name, self.last())

    def __str__(self):
        return self.full_name()

    class Meta:
        abstract = True
        get_latest_by = 'date'
        ordering = ['-date'] # history of names for a person are returned current first 

class NameChange(Name):
    """The first NameChange is the one on the birth certificate. 
    A person normally has one registered name and one nickname at a time.
    Additional names are aliases that are recognized because they aren't
    registered. If an old registered name is used as an alias, it should be
    entered again with method of name change being Pseudonym, and not registered.
    Any unregistered name will be considered an alias, even if not a pseudonym.
    Pseudonyms can be registered as well though - stage names or authors
    for example. If a Pseudonym is registered with an agency like County Clerk,
    but not with Social Security and DMV, then the County Clerk Pseudonym can be 
    used simultaneously with the Social Security/DMV 'real' name."""

    # inherits name fields and the NameChange#date from Name()
    person = models.ForeignKey(Person)
    reason = models.CharField('reason for name change', 
            help_text='Enter the reason this name was assigned to this person.', 
            max_length=64) 
    date_registered = models.DateField('date first registered', help_text='Leave \
            blank until there are registrations entered for this name; then \
            return to this form and fill in the date of first registration or \
            leave blank again and that date will be filled in automatically',
            blank=True, null=True, default=None)
    
    BIRTH = 'BI'    # building up choices for the method of name change
    COURT = 'CO'
    MARRIAGE = 'MA'
    DIVORCE = 'DI'
    ADOPTION = 'AD'
    NATURALIZATION = 'NA'
    PSEUDONYM = 'PS'
    METHOD_CHOICES = (
            (BIRTH, 'Birth'),
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
                    such as the court and document number. May also enter \
                    information about parents and hospital if this is the \
                    birth name. To enter the Birth Certificate, Social \
                    Security Number, and other identification, show this \
                    name as registered with each relevant agency (County \
                    Clerk, Social Security Administration, DMV etc.)', 
                    max_length=32, blank=True)
    
    def dateFirstRegistered(self):
        if self.isAlias():
            return None
        else:
            return min([reg.date for reg in self.name_registration_set])

    def clean(self):
        if self.date_registered != self.dateFirstRegistered():
            if self.date_registered is None:
                self.date_registered = self.dateFirstRegistered()
            elif self.dateFirstRegistered is None:
                raise ValidationError('First enter some registrations \
                        for this name before entering the registration \
                        date')
            else:
                raise ValidationError('The registration date entered \
                        does not match the earliest registration date \
                        for this name. Leave this field blank and the \
                        correct date will be filled in automatically.')

    def isAlias(self):
        """returns True if self hasn't been registered:
        i.e., True if there are no NameRegistration children of self """
        return not self.name_registration_set.exists()

    def isProperPseudonym(self):
        """returns True if self is a pseudonym, but not an alias,
        and not registered with both the DMV and Social Security"""
        if self.method==PSEUDONYM and not isAlias(): 
            regs = [name.registered_with for name in self.name_registration_set]
            SSA, DMV = NameRegistration.SSA, NameRegistration.DMV
            return not ((SSA in regs) and (DMV in regs))
        else:
            return False

    def isCurrent(self):
        """returns True for any of the following:
        the latest registered name 
        any Alias
        any ProperPseudonym
        the latest non-pseudonym registered name"""
        
        name_changes = self.person.name_change_set
        all_registered = name_changes.filter(
                name_registration__name_change__isnull=False)
        latest_registered = all_registered.latest('date_registered')
        if (latest_registered == self) or isAlias() or isProperPseudonym():
            return True
        elif latest_registered.isProperPseudonym():
            registered_nonpseudos = all_registered.exclude(method=PSEUDONYM)
            latest_registered_nonpseudo = registered_nonpseudos.latest('date_registered')
            return latest_registered_nonpseudo == self
        else:
            return False

class NameRegistration(models.Model):
    name_change = models.ForeignKey(NameChange)
    date = models.DateField('date name registered with agency')

    SSA = 'SSA' # building up choices of where the new name was registered
    BCA = 'BCA'
    USPS = 'USP'
    DMV = 'DMV'
    SECSTATE = 'SOS'
    COUNTYCL = 'COC'
    OTHER = 'OTH'
    AGENCIES = (
            (SSA, 'Social Security Administration'),
            (BCA, 'Bureau of Consular Affairs'),
            (USPS, 'United States Postal Service'),
            (DMV, 'Department of Motor Vehicles'),
            (SECSTATE, 'Secretary of State'),
            (COUNTYCL, 'County Clerk'),
            (OTHER, 'Other'),
    )
    registered_with = models.CharField(help_text=
            'Choose the agency this name was registered with', 
            max_length=3, choices=AGENCIES, default=SSA)
    reg_info = models.CharField('registration information', help_text=
            'Enter additional relevant information like state, county, \
                    or details about "Other" such as the Company Name \
                    of the Employer/Bank/Doctor/Mortgage/Insurance/\
                    Credit Card...', 
                    max_length=64, blank=True) 

    class Meta:
        get_latest_by = 'date'
        ordering = ['-date'] # name registrations for a person are returned current first 

class IdDoc(models.Model):
    name_registration = models.ForeignKey(NameRegistration)
    name_on_id = models.CharField(help_text='Enter full name as listed on this \
            identification.', max_length=128)
    name = models.CharField('identification-document name', 
            help_text='For example: Missouri Driver License', max_length=16)
    number = models.CharField(max_length=32)
    date = models.DateField('id issue date')
    expire = models.DateField('id expiration date', blank=True)
    info = models.CharField(max_length=32, blank=True)

class Phone(models.Model):
    person = models.ForeignKey(Person)
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
    person = models.ForeignKey(Person)
    date = models.DateField('email-signup date')
    addr = models.EmailField('email', max_length=254)
    term = models.DateField('email-termination date')

class Profile(models.Model):
    person = models.ForeignKey(Person)
    date = models.DateField('online-profile creation date')
    uri = models.URLField('online-profile link')
    del_date = models.DateField('online-profile deletion date')
    
