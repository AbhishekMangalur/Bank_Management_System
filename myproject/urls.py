"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from myapp.views import home, user_form, delete_account, edit_account, edit_accounts, deposite_amount, withdraw_amount, atm_redirect, atm_options, balance_enquiry, deposit, withdraw, view_transactions, loan_fetch, get_loan, close_loan, pay_loan, atmappln, loan_transactions, fetch_fd, fd_list, create_fd, close_fd, loan_list


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('form/', user_form, name='user_form'),
    path('delete/', delete_account, name='delete_account'),
    path('edit/', edit_account, name='edit_account'),
    path('edits/', edit_accounts, name='edit_accounts'),
    path('atmappln/', atmappln, name='atmappln'),
    path('deposite/', deposite_amount, name='deposite_amount'),
    path('withdraw/', withdraw_amount, name='withdraw_amount'),
    path('view_transactions/', view_transactions, name='view_transactions'),
    path('loans/', loan_list, name='loan_list'),
    path('loan_fetch/', loan_fetch, name='loan_fetch'),
    path('loan_transactions/', loan_transactions, name='loan_transactions'),
    path('fetch_fd/', fetch_fd, name='fetch_fd'),
    path('atm/', atm_redirect, name='atm_redirect'),
    path('atm/options/<str:generated_number>/', atm_options, name='atm_options'),
    path('balance/<str:generated_number>/', balance_enquiry, name='balance_enquiry'),
    path('atmdeposit/<str:generated_number>/', deposit, name='deposit'),
    path('atmwithdraw/<str:generated_number>/', withdraw, name='withdraw'),
    path('get-loan/<str:account_number>/', get_loan, name='get_loan'),
    path('pay-loan/<str:account_number>/', pay_loan, name='pay_loan'),
    path('close-loan/<str:account_number>/', close_loan, name='close_loan'),    
    path('create-fd/<str:account_number>/', create_fd, name='create_fd'),
    path('close-fd/<str:account_number>/', close_fd, name='close_fd'),
    path('loan_list/<str:generated_number>/', loan_list, name='loan_list'),
    path('fixed-deposits/<str:account_number>/', fd_list, name='fd_list'),
]