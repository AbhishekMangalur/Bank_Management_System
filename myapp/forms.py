from django import forms
from datetime import date
from .models import Account, Loan, FixedDeposit
from django.core.exceptions import ValidationError
from django.utils import timezone

class AccountForm(forms.ModelForm):
    terms_accepted = forms.BooleanField(label="I accept the terms and conditions", required=True)
    
    class Meta:
        model = Account
        fields = ['fname', 'lname', 'age', 'email', 'phone', 'address', 'gender', 'photo', 'date', 'amount', 'terms_accepted']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),  # Renders the date field as a date picker
            'phone': forms.NumberInput(attrs={'placeholder': ''}),  # Phone field as a number input
        }

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.fields['amount'].initial = None  # This makes the amount field empty by default
        self.fields['amount'].widget.attrs['placeholder'] = ''

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount < 0:
            raise ValidationError('The amount not less than 0')
        return amount

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date is not None and date < timezone.now().date():
            raise ValidationError('The date must be today or in the future')
        return date

class EditForm(forms.ModelForm):
    terms_accepted = forms.BooleanField(
        label="I accept the terms and conditions",
        required=True
    )

    class Meta:
        model = Account
        fields = [
            'account_number', 'fname', 'lname', 'age', 'email', 'phone', 'address', 'gender', 'photo', 'terms_accepted'
        ]

    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['account_number'].disabled = True

class EmailForm(forms.Form):
    email = forms.EmailField()

class AccountNumberForm(forms.Form):
    account_number = forms.CharField(
        max_length=20, 
        label='', 
        widget=forms.NumberInput(attrs={
            'min': '000000',
            'max': '99999999999999',
            'step': '1',
            'class': 'number-input'
        })
    )

class DepositeForm(forms.Form):
    account_number = forms.CharField(
        max_length=20, 
        label='', 
        widget=forms.NumberInput(attrs={
            'min': '000000',
            'max': '99999999999999',
            'step': '1',
            'class': 'number-input'
        })
    )

class UpdateAmountForm(forms.Form):
    account_number = forms.CharField(max_length=20, widget=forms.HiddenInput())
    new_amount = forms.DecimalField(max_digits=10, decimal_places=2, label='')

    def clean_new_amount(self):
        new_amount = self.cleaned_data.get('new_amount')
        if new_amount < 0:
            raise forms.ValidationError("The amount cannot be negative.")
        return new_amount

class NumberForm(forms.Form):
    generated_number = forms.CharField(
        max_length=20, 
        label='', 
        widget=forms.NumberInput(attrs={
            'min': '000000',
            'max': '99999999999999',
            'step': '1',
            'class': 'number-input'
        })
    )

class PinForm(forms.Form):
    pin = forms.CharField(
        required=False,  # Set required to False
        widget=forms.NumberInput(attrs={
            'min': '000000',
            'max': '999999',
            'step': '1',
            'class': 'pin-input'
        })
    )

    def __init__(self, *args, **kwargs):
        super(PinForm, self).__init__(*args, **kwargs)
        self.fields['pin'].label = ""


class AtmDepositForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label='')

class LoanAccountNumberForm(forms.Form):
    account_number = forms.CharField(
        max_length=14,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter Account Number',
            'class': 'form-control',
        }),
        label=''  # No label, just a clean input field
    )

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['loan_amount', 'tenure', 'interest_rate', 'reason']

    def __init__(self, *args, **kwargs):
        account_instance = kwargs.pop('account_instance', None)
        super(LoanForm, self).__init__(*args, **kwargs)
        if account_instance:
            # Set the account_number field with a custom label (account_number)
            self.fields['account_number'] = forms.ModelChoiceField(
                queryset=account.objects.filter(pk=account_instance.pk),
                initial=account_instance,
                widget=forms.TextInput(attrs={'readonly': 'readonly'})
            )
            self.fields['account_number'].label_from_instance = lambda obj: obj.account_number

class PayLoanForm(forms.Form):
    payed_loan = forms.DecimalField(max_digits=10, decimal_places=2)
    reason = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        account_number = kwargs.pop('account_number', None)
        super().__init__(*args, **kwargs)
        if account_number:
            # Update queryset based on account_number
            reasons = Loan.objects.filter(account_number=account_number).values_list('reason', flat=True).distinct()
            self.fields['reason'].choices = [(reason, reason) for reason in reasons]

class LoanSelectForm(forms.Form):
    reason = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        account_number = kwargs.pop('account_number', None)
        super().__init__(*args, **kwargs)
        if account_number:
            # Update queryset based on account_number
            reasons = Loan.objects.filter(account_number=account_number).values_list('reason', flat=True).distinct()
            self.fields['reason'].choices = [(reason, reason) for reason in reasons]

class FixedDepositForm(forms.ModelForm):
    class Meta:
        model = FixedDeposit
        fields = ['principal_amount', 'interest_rate', 'start_date', 'maturity_date']
        widgets = {
            'maturity_date': forms.DateInput(attrs={'type': 'date'}),  # Date picker for maturity_date
            'start_date': forms.DateInput(attrs={'type': 'date'})      # Optional: Add a date picker for start_date as well
        }

    # Validation to ensure maturity date is not in the past
    def clean_maturity_date(self):
        maturity_date = self.cleaned_data.get('maturity_date')
        if maturity_date < date.today():
            raise ValidationError("Maturity date cannot be in the past. Please select a future date.")
        return maturity_date

class FDAccountNumberForm(forms.Form):
    account_number = forms.CharField(max_length=14, label='Account Number')
