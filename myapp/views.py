import random
import smtplib
from django.db import transaction, IntegrityError
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
from myapp.models import Account, Transaction, Loan, LoanTransaction, FixedDeposit
from myapp.forms import AccountForm, EmailForm, EditForm, AccountNumberForm, DepositeForm, UpdateAmountForm, NumberForm, PinForm, AtmDepositForm, LoanSelectForm, PayLoanForm, LoanForm, FixedDepositForm

def home(request):
    return render(request, 'home.html')

def user_form(request):
    if request.method == 'POST':
        form = AccountForm(request.POST, request.FILES)
        if form.is_valid():
            user_info = form.save()
            # Send a confirmation email
            send_mail(
                subject='Account Opening..!',
                message=f'Dear {user_info.fname} {user_info.lname},\n\nThank you for registering. We have received your information.\n\nYour Account No: {user_info.account_number}\n\n\nBest Regards,\nUNIQUE BANK',
                from_email='abhimangalur2@gmail.com',
                recipient_list=[user_info.email],
                fail_silently=False,
            )
            return redirect('home')
    else:
        form = AccountForm()
    return render(request, 'user_form.html', {'form': form})

def delete_account(request):
    error = None  # Variable to store error messages if account doesn't exist

    if request.method == 'POST':
        account_number = request.POST.get('account_number')
        try:
            # Retrieve the account using the account number
            accounts = Account.objects.get(account_number=account_number)
            registered_email = accounts.email  # Assuming the 'Account' model has an 'email' field
            
            # Delete the account
            accounts.delete()
            
            # Send a success message to the user's email
            send_mail(
                'Account Deletion Confirmation',
                'Your account has been successfully deleted.\n\nThank you for using UNIQUE BANK services.\n\nBest regards,\nUNIQUE BANK',
                'abhimangalur2@gmail.com',  # Replace with your "from" email
                [registered_email],
                fail_silently=False,
            )
            
            # Success message for the user and redirect to homepage
            messages.success(request, 'Account successfully deleted. A confirmation email has been sent.')
            return redirect('home')
        
        except Account.DoesNotExist:
            # If account does not exist, show the error above the delete button
            error = 'No account found with this account number.'

    # Render the form and pass the error message to the template
    return render(request, 'delete_account.html', {'error': error})

def edit_accounts(request):
    return render(request, 'edit_accounts.html')

def edit_account(request):
    account_number = request.GET.get('account_number') if request.method == 'GET' else request.POST.get('account_number')
    
    if request.method == 'POST':
        try:
            # Fetch the account instance only once
            accounts = get_object_or_404(Account, account_number=account_number)
            form = EditForm(request.POST, request.FILES, instance=accounts)
            if form.is_valid():
                form.save()
                return redirect('home')
            else:
                return render(request, 'edit_account.html', {'form': form, 'error': 'Form is invalid', 'account_number': account_number})
        except:
            return render(request, 'edit_account.html', {'error': 'Account number not found', 'account_number': account_number})
    
    else:  # Handle GET request
        try:
            accounts = get_object_or_404(Account, account_number=account_number)
            form = EditForm(instance=accounts)
            return render(request, 'edit_account.html', {'form': form, 'account_number': account_number})
        except:
            return render(request, 'edit_accounts.html', {'error': 'Account number not found'})

def atmappln(request):
    if request.method == 'POST':
        form = AccountNumberForm(request.POST)
        if form.is_valid():
            account_number = form.cleaned_data['account_number'].strip()  # Remove any extra spaces
            print(f"Checking for account number: '{account_number}'")  # Debugging output

            try:
                accounts = Account.objects.get(account_number=account_number)
                print(f"Account found: {accounts}")  # Debugging output
            except Account.DoesNotExist:
                print("Account not found")  # Debugging output
                return render(request, 'check_account.html', {'form': form, 'error': 'Account number does not exist'})

            # Check if the 12-digit number and 6-digit pin already exist
            if accounts.generated_number and accounts.pin:
                # If they already exist, show an error message
                return render(request, 'check_account.html', {
                    'form': form,
                    'error': 'ATM details already exist for this account.'
                })
            
            # Generate a 12-digit number and a 6-digit pin
            generated_number = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Save the generated values in the account
            accounts.generated_number = generated_number
            accounts.pin = pin
            accounts.save()

            # Send an email with the generated number and pin
            send_mail(
                'Your ATM Details',
                f'Here are your ATM Card details:\n\n12-digit Card Number: {generated_number}\n6-digit pin: {pin}\n\n\nBest Regards,\nUNIQUE BANK',
                'abhimangalur2@gmail.com',
                [accounts.email],
                fail_silently=False,
            )
            return redirect('home')  # Redirect to the homepage after processing
    else:
        form = AccountNumberForm()
    return render(request, 'check_account.html', {'form': form})

def deposite_amount(request):
    account_details = None
    error = None
    form = DepositeForm(request.POST or None)
    update_form = UpdateAmountForm(request.POST or None)

    if request.method == 'POST':
        if 'fetch_details' in request.POST:
            if form.is_valid():
                account_number = form.cleaned_data['account_number'].strip()
                try:
                    account_details = Account.objects.get(account_number=account_number)
                except Account.DoesNotExist:
                    error = 'Account number does not exist'
                else:
                    # Initialize the update_form with the fetched account number
                    update_form = UpdateAmountForm(initial={'account_number': account_number})
        
        elif 'update_amount' in request.POST:
            if update_form.is_valid():
                account_number = update_form.cleaned_data['account_number'].strip()
                new_amount = update_form.cleaned_data['new_amount']

                if new_amount <= 0:
                    error = 'Deposit amount must be greater than zero'
                else:
                    try:
                        with transaction.atomic():
                            accounts = Account.objects.get(account_number=account_number)
                            accounts.amount += new_amount
                            accounts.save()

                            # Save the transaction with account_number
                            Transaction.objects.create(
                                account_number=account_number,
                                amount=new_amount,
                                total_amount=accounts.amount,
                                description='Deposit via BANK'
                            )
                        return redirect('home')
                    except Account.DoesNotExist:
                        error = 'Account number does not exist'
    
    return render(request, 'deposit_amount.html', {
        'form': form,
        'update_form': update_form,
        'account_details': account_details,
        'error': error
    })

def withdraw_amount(request):
    account_details = None
    error = None
    form = DepositeForm(request.POST or None)
    update_form = UpdateAmountForm(request.POST or None)

    if request.method == 'POST':
        if 'fetch_details' in request.POST:
            if form.is_valid():
                account_number = form.cleaned_data['account_number'].strip()
                try:
                    account_details = Account.objects.get(account_number=account_number)
                except Account.DoesNotExist:
                    error = 'Account number does not exist'
        
        elif 'update_amount' in request.POST:
            if update_form.is_valid():
                account_number = update_form.cleaned_data['account_number'].strip()
                new_amount = update_form.cleaned_data['new_amount']

                try:
                    accounts = Account.objects.get(account_number=account_number)
                    
                    if new_amount <= accounts.amount:  # Check if withdrawal amount is less than or equal to the existing amount
                        with transaction.atomic():
                            # Update the account balance
                            accounts.amount -= new_amount
                            accounts.save()

                            # Save the transaction with the updated total_amount
                            Transaction.objects.create(
                                account_number=account_number,
                                amount=new_amount,
                                total_amount=accounts.amount,  # Store the updated balance
                                description='Withdraw via BANK'
                            )
                        return redirect('home')
                    else:
                        error = 'Insufficient funds. Please enter a smaller amount.'
                except Account.DoesNotExist:
                    error = 'Account number does not exist'
    
    else:
        if account_details:
            update_form = UpdateAmountForm(initial={'account_number': account_details.account_number})

    return render(request, 'withdraw_amount.html', {
        'form': form,
        'update_form': update_form,
        'account_details': account_details,
        'error': error
    })

def atm_redirect(request):
    error = None
    number_form = NumberForm(request.POST or None)

    if request.method == 'POST':
        if number_form.is_valid():
            generated_number = number_form.cleaned_data.get('generated_number').strip()
            try:
                account_details = Account.objects.get(generated_number=generated_number)
                # If account exists, redirect to the options page with the generated number
                return redirect('atm_options', generated_number=generated_number)
            except Account.DoesNotExist:
                error = 'Invalid ATM card number'

    return render(request, 'atm_redirect.html', {
        'number_form': number_form,
        'error': error
    })

def atm_options(request, generated_number):
    try:
        account_details = Account.objects.get(generated_number=generated_number)
    except Account.DoesNotExist:
        return redirect('atm_redirect')

    return render(request, 'atm_options.html', {
        'generated_number': generated_number,
        'account_details': account_details
    })

def balance_enquiry(request, generated_number):
    try:
        account_details = Account.objects.get(generated_number=generated_number)
        balance = account_details.amount
    except Account.DoesNotExist:
        return redirect('atm_redirect')

    return render(request, 'balance_enquiry.html', {
        'balance': balance,
        'generated_number': generated_number,
    })

def deposit(request, generated_number):
    account_details = None
    pin_error = None
    pin_validated = False  # To check if the PIN was validated
    form = PinForm(request.POST or None)
    deposit_form = None

    try:
        account_details = Account.objects.get(generated_number=generated_number)
    except Account.DoesNotExist:
        return redirect('atm_redirect')  # Handle non-existing account

    if request.method == 'POST':
        if 'check_pin' in request.POST and form.is_valid():
            entered_pin = form.cleaned_data.get('pin')
            if entered_pin == account_details.pin:
                pin_validated = True  # PIN is validated, show deposit form
                deposit_form = AtmDepositForm()  # Initialize the deposit form without POST data
            else:
                pin_error = 'Incorrect PIN. Please try again.'

        elif 'submit_deposit' in request.POST:
            deposit_form = AtmDepositForm(request.POST)
            if deposit_form.is_valid():
                new_amount = deposit_form.cleaned_data.get('amount')
                if new_amount > 0:
                    with transaction.atomic():
                        # Update the account balance
                        account_details.amount += new_amount
                        account_details.save()

                        # Save the transaction
                        Transaction.objects.create(
                            account_number=account_details.account_number,
                            amount=new_amount,
                            total_amount=account_details.amount,  # Store the updated balance
                            description='Deposit via ATM'
                        )

                    # Redirect to the ATM options page after a successful deposit
                    return redirect('atm_options', generated_number=generated_number)
                else:
                    pin_error = 'Amount must be positive.'
            else:
                pin_validated = True  # Ensure the deposit form is displayed again

    # Render the form if the PIN was validated
    if pin_validated and deposit_form is None:
        deposit_form = AtmDepositForm()

    return render(request, 'deposit.html', {
        'form': form,
        'deposit_form': deposit_form,
        'pin_error': pin_error,
        'pin_validated': pin_validated,
        'generated_number': generated_number,
    })

def withdraw(request, generated_number):
    account_details = None
    pin_error = None
    pin_validated = False  # To check if the PIN was validated
    form = PinForm(request.POST or None)
    deposit_form = None

    try:
        account_details = Account.objects.get(generated_number=generated_number)
    except Account.DoesNotExist:
        return redirect('atm_redirect')  # Handle non-existing account

    if request.method == 'POST':
        if 'check_pin' in request.POST and form.is_valid():
            entered_pin = form.cleaned_data.get('pin')
            if entered_pin == account_details.pin:
                pin_validated = True  # PIN is validated, show deposit form
                deposit_form = AtmDepositForm()  # Initialize the deposit form without POST data
            else:
                pin_error = 'Incorrect PIN. Please try again.'

        elif 'submit_deposit' in request.POST:
            deposit_form = AtmDepositForm(request.POST)
            if deposit_form.is_valid():
                new_amount = deposit_form.cleaned_data.get('amount')
                if new_amount > 0:
                    if new_amount <= account_details.amount:  # Check if the amount is less than or equal to the available balance
                        with transaction.atomic():
                            # Update the account balance
                            account_details.amount -= new_amount
                            account_details.save()

                            # Save the transaction
                            Transaction.objects.create(
                                account_number=account_details.account_number,
                                amount=new_amount,
                                total_amount=account_details.amount,  # Store the updated balance
                                description='Withdraw via ATM'
                            )

                        # Redirect to the ATM options page after a successful withdrawal
                        return redirect('atm_options', generated_number=generated_number)
                    else:
                        pin_error = 'Insufficient funds. Please enter a smaller amount.'
                else:
                    pin_error = 'Amount must be positive.'
            else:
                pin_validated = True  # Ensure the deposit form is displayed again

    # Render the form if the PIN was validated
    if pin_validated and deposit_form is None:
        deposit_form = AtmDepositForm()

    return render(request, 'withdraw.html', {
        'form': form,
        'deposit_form': deposit_form,
        'pin_error': pin_error,
        'pin_validated': pin_validated,
        'generated_number': generated_number,
    })

def view_transactions(request):
    form = AccountNumberForm(request.POST or None)
    transactions = None  # Use plural for multiple transactions
    error = None
    no_transactions_message = None  # Initialize the message variable

    if request.method == 'POST':
        if form.is_valid():
            account_number = form.cleaned_data['account_number'].strip()

            try:
                # Ensure the account exists
                account_obj = Account.objects.get(account_number=account_number)
                
                # Fetch all transactions related to the account_number, ordered from oldest to newest
                transactions = Transaction.objects.filter(account_number=account_number).order_by('date')
                
                # If no transactions exist, display a message
                if not transactions.exists():
                    no_transactions_message = 'No transactions found for this account.'
                    
            except Account.DoesNotExist:
                error = 'Account number does not exist.'

    return render(request, 'view_transactions.html', {
        'form': form,
        'transactions': transactions,  # Use plural for passing transactions
        'error': error,
        'no_transactions_message': no_transactions_message  # Handle no transactions message
    })


def loan_list(request, generated_number):
    # Use the generated_number in your logic
    loans = Loan.objects.filter(account_number=generated_number)
    context = {
        'loans': loans,
        'generated_number': generated_number
    }
    return render(request, 'loan_list.html', context)

def loan_fetch(request):
    account_details = None
    error = None
    form = AccountNumberForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            account_number = form.cleaned_data['account_number'].strip()
            try:
                account_details = Account.objects.get(account_number=account_number)
            except Account.DoesNotExist:
                error = "Account number does not exist."

    return render(request, 'loan_fetch.html', {
        'form': form,
        'account_details': account_details,
        'error': error,
    })

def get_loan(request, account_number):
    account_details = Account.objects.get(account_number=account_number)

    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            try:
                loan = form.save(commit=False)
                loan.account_number = account_number  # Ensure the correct account number is saved
                loan.reason = form.cleaned_data['reason']  # Capture the reason from the form
                loan.save()

                # Send an email notification
                send_mail(
                    'Loan Details',
                    f'Your loan has been successfully sanctioned.\n\nLoan Reason: {loan.reason} \nAmount: ₹{loan.loan_amount}\nInterest: {loan.interest_rate} %\nTime Period: {loan.tenure} Months\n\n\nBest Regards,\nUNIQUE BANK',
                    settings.DEFAULT_FROM_EMAIL,
                    [account_details.email],
                    fail_silently=False,
                )

                # Redirect to home after saving
                return redirect('home')
            except IntegrityError:
                # Handle duplicate entry by adding an error message to the form
                form.add_error(None, "A loan with this reason already exists for this account.")
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = LoanForm()

    return render(request, 'get_loan.html', {
        'form': form,
        'account_details': account_details,
    })

def pay_loan(request, account_number):
    # Fetch loans associated with the account_number
    loans = Loan.objects.filter(account_number=account_number)
    
    if request.method == 'POST':
        form = PayLoanForm(request.POST, account_number=account_number)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            payed_loan = form.cleaned_data['payed_loan']
            
            # Debug print
            print(f"Submitted reason: {reason}")
            print(f"Available reasons: {[loan.reason for loan in loans]}")

            # Find the loan with the matching reason
            loan = get_object_or_404(loans, reason=reason)
            
            # Process the payment
            if payed_loan > 0 and payed_loan <= loan.remaining_loan:
                loan.remaining_loan -= payed_loan
                loan.payed_loan += payed_loan  # Update paid amount
                loan.save()

                # Create a new loan transaction record
                LoanTransaction.objects.create(
                    loan=loan,
                    amount=payed_loan,
                    date_time=timezone.now(),  # Add current date and time
                    description=f"{reason} loan Payment"
                )

                # Redirect or render a success page
                return redirect('home')
            else:
                # Handle error if payment is invalid
                form.add_error('payed_loan', 'Payment amount is invalid or exceeds remaining loan.')
        else:
            # Debug print for form errors
            print(f"Form errors: {form.errors}")
    else:
        form = PayLoanForm(account_number=account_number)

    return render(request, 'pay_loan.html', {'form': form})

def close_loan(request, account_number):
    if request.method == 'POST':
        form = LoanSelectForm(request.POST, account_number=account_number)
        if form.is_valid():
            reason = form.cleaned_data.get('reason')
            # Fetch the loan object based on the selected reason and account number
            loan = get_object_or_404(Loan, account_number=account_number, reason=reason)
            
            if loan.remaining_loan == 0:
                # Close the loan
                loan.delete()

                # Get the email address of the account holder
                account = get_object_or_404(Account, account_number=account_number)
                recipient_email = account.email

                # Send an email notification
                send_mail(
                    'Loan Details',
                    f'Your "{reason}" loan has been successfully closed.\n\n\nBest Regards,\nUNIQUE BANK',
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient_email],
                    fail_silently=False,
                )

                messages.success(request, f"Loan '{loan.reason}' has been successfully closed.")
                return redirect('home')  # Redirect to a success page or home
            else:
                # Error message if loan balance is not zero
                messages.error(request, "Cannot close the loan. Remaining balance must be zero.")
    else:
        form = LoanSelectForm(account_number=account_number)

    return render(request, 'close_loan.html', {'form': form})

def loan_transactions(request):
    form = AccountNumberForm(request.POST or None)
    transactions = None
    error = None

    if request.method == 'POST':
        if form.is_valid():
            account_number = form.cleaned_data['account_number'].strip()
            try:
                # Ensure the account exists
                account_obj = Account.objects.get(account_number=account_number)
                
                # Fetch all transactions related to the account, ordered from oldest to newest
                transactions = LoanTransaction.objects.filter(
                    account_number=account_number
                ).order_by('date_time')
                
                if not transactions.exists():
                    error = 'No transactions found for this account number.'
                    
            except Account.DoesNotExist:
                error = 'Account number does not exist.'

    context = {
        'form': form,
        'transactions': transactions,
        'error': error
    }
    return render(request, 'loan_transactions.html', context)

def fetch_fd(request):
    form = AccountNumberForm(request.POST or None)
    account_holder = None
    error = None
    show_create_fd_button = False
    fds = []  # Initialize as an empty list

    if request.method == 'POST':
        if form.is_valid():
            account_number = form.cleaned_data['account_number'].strip()
            
            # Fetch account details using filter() instead of get_object_or_404()
            account_holder = Account.objects.filter(account_number=account_number).first()
            
            if account_holder:
                # Fetch all FDs associated with the account
                fds = FixedDeposit.objects.filter(account_number=account_holder)
                show_create_fd_button = True  # Show the "Create FD" button
            else:
                # If the account is not found, set the error message
                error = 'Account number does not exist.'

    return render(request, 'fetch_fd.html', {
        'form': form,
        'account_holder': account_holder,
        'fds': fds,  # Pass the FDs to the template
        'error': error,
        'show_create_fd_button': show_create_fd_button
    })


def create_fd(request, account_number):
    account = get_object_or_404(Account, account_number=account_number)

    if request.method == 'POST':
        form = FixedDepositForm(request.POST)
        if form.is_valid():
            fd = form.save(commit=False)
            fd.account_number = account_number
            fd.save()

            # Send an email notification
            send_mail(
                'Fixed Deposit Details',
                f'Your Fixed Deposit has been successfully created with the following details:\n\n'
                f'Account Number: ₹ {account_number}\n'
                f'Principal Amount: ₹ {fd.principal_amount:.2f}\n'
                f'Interest Rate: {fd.interest_rate}\n'
                f'Start Date: {fd.start_date}\n'
                f'Maturity Date: {fd.maturity_date}\n'
                f'Matured Amount: ₹ {fd.matured_amount:.2f}\n\n\nBest Regards,\nUNIQUE BANK',
                settings.DEFAULT_FROM_EMAIL,
                [account.email],
                fail_silently=False,
            )

            messages.success(request, "Fixed Deposit has been successfully created.")
            return redirect('home')
    else:
        form = FixedDepositForm()

    return render(request, 'create_fd.html', {
        'form': form,
        'account_number': account_number,
    })

def close_fd(request, account_number):
    # Fetch all Fixed Deposits for the account
    fds = FixedDeposit.objects.filter(account_number=account_number)
    
    if request.method == 'POST':
        fd_id = request.POST.get('fd_id')
        # Get the selected FD
        fd = get_object_or_404(FixedDeposit, id=fd_id)
        
        # Get the account associated with the FD
        account = get_object_or_404(Account, account_number=account_number)

        # Delete the FD
        fd.delete()

        # Send an email notification
        send_mail(
            'Fixed Deposit Details',
            f'Your Fixed Deposit with ID {fd_id} has been successfully closed. Here are the details:\n\n'
            f'Account Number: {account_number}\n'
            f'Principal Amount: ₹ {fd.principal_amount:.2f}\n'
            f'Interest Rate: {fd.interest_rate}%\n'
            f'Start Date: {fd.start_date}\n'
            f'Maturity Date: {fd.maturity_date}\n'
            f'Matured Amount: ₹ {fd.matured_amount:.2f}\n\n\nBest Regards,\nUNIQUE BANK',
            settings.DEFAULT_FROM_EMAIL,
            [account.email],
            fail_silently=False,
        )

        messages.success(request, "Fixed Deposit has been successfully closed.")
        return redirect('home')
    
    return render(request, 'close_fd.html', {
        'fds': fds,
        'account_number': account_number
    })

def fd_list(request, account_number):
    # Fetch Fixed Deposits for the given account_number
    fds = FixedDeposit.objects.filter(account_number=account_number)
    
    return render(request, 'fixed_deposit_list.html', {
        'fds': fds,
        'account_number': account_number
    })
