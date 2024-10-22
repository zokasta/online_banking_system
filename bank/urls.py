# urls.py

from django.urls import path
from .views import city_state,credit_card_views,account_views,user_views,transaction_views,auth_views, report_views
from .views.Admin import admin_dashboard_card
from .views import city_views, state_views

urlpatterns = [
    path('login/', auth_views.login, name='login'),
    path('admin-login/', auth_views.adminLogin, name='admin Login'),
    path('signup/', auth_views.signup, name='signup'),
    path('forgot-password-request/', auth_views.send_otp_for_forgot_password, name='forgot password request'),
    path('verify-otp-for-forgot-password/', auth_views.verify_otp_for_forgot_password, name='forgot password verify otp'),
    path('verify_otp/', auth_views.verify_otp, name='verify_otp'),
    path('change-password/', auth_views.reset_password, name='change password'),
    
    
    path('send-money/', transaction_views.create_transaction, name='create_transaction'),
    path('see-balance/', transaction_views.see_balance, name='see_balance'),
    path('transaction/', transaction_views.transaction_history, name='transaction_history'),
    path('user/<int:user_id>/', user_views.get_user_by_id, name='get_user_by_id'),
    path('user/', user_views.get_authenticated_user, name='get_authenticated_user'),
    path('user/update/', user_views.update_user, name='update_user'),
    path('users/', user_views.get_all_users, name='get_all_users'),
    path('users/delete/<int:user_id>/', user_views.delete_user, name='delete_user'), # Delete Method
    path('user/account/show/', transaction_views.create_transaction, name='create_transaction'),

    
    path('admin/user-statistics/<str:period>', admin_dashboard_card.user_growth ,name='user_statistics'),
    path('admin/rollback-statistics/<str:period>', transaction_views.rollback_statistics ,name='user_statistics'),
    path('admin/transaction-statistics/<str:period>', transaction_views.transaction_growth ,name='total_transaction_amount'),
    path('admin/transaction-monthly-summary/', transaction_views.transaction_monthly_summary ,name='transaction_monthly_summary'),
    
    
    path('user/transaction-statistics-self-debit-card/<str:period>/', transaction_views.debit_card_transaction_sum_for_user ,name='total_transaction_amount'),
    path('user/transaction-statistics-self-credit-card/<str:period>/', transaction_views.credit_card_transaction_count_for_user ,name='total_transaction_amount'),

    path('all/transaction-monthly-summary-debit-card/', transaction_views.debit_card_transaction_summary ,name='transaction_monthly_summary'),
    path('all/transaction-monthly-summary-credit-card/', transaction_views.credit_card_transaction_summary ,name='transaction_monthly_summary'),
    
    
    path('admin/transaction-statistics-self-debit-card/<str:period>/', transaction_views.debit_card_transaction_sum ,name='total_transaction_amount'),
    path('admin/transaction-statistics-self-credit-card/<str:period>/', transaction_views.credit_card_transaction_count ,name='total_transaction_amount'),
    
    
    
    path('admin/transaction/all/', transaction_views.transaction_count ,name='transaction_count'),
    path('admin/user/<int:user_id>/', user_views.user_update_by_admin, name='user_update_by_admin'),
    path('admin/transaction/', transaction_views.admin_transaction_history, name='admin_transaction_history'),
    path('admin/transaction/<int:transaction_id>/', transaction_views.admin_transaction_delete, name='admin_transaction_delete'),
    path('admin/transaction/rollback/<int:transaction_id>/', transaction_views.rollback_transaction, name='admin_transaction_delete'),
    
    path('admin/account/', account_views.admin_account_list, name='admin_account_list'),
    path('admin/account/<int:account_id>/', account_views.admin_account_delete, name='admin_account_delete'),
    path('admin/account/edit/<int:account_id>/', account_views.admin_account_edit, name='admin_account_edit'),

    
    
    

    # City and state system
    path('states/create/', state_views.create_state, name='state-list-create'),
    path('states/', state_views.state_list, name='state-list-create'),
    path('states/<int:id>/', state_views.state_detail, name='state-detail'),
    
    path('cities/', city_views.city_list, name='city-list-create'),
    path('cities/create/', city_views.create_city, name='create-city'),
    path('cities/<int:id>/', city_views.city_detail, name='city-detail'),
    path('states/<int:state_id>/cities/', state_views.cities_by_state, name='city-list-by-state-id'),

    # Credit Card Area
    path('credit-card/apply/', credit_card_views.apply_for_credit_card, name='generate_card_number'),
    path('credit-card/list/', credit_card_views.get_credit_card_list, name='get_credit_card_list'),
    path('credit-card/list/pending/', credit_card_views.get_pending_credit_card_applications, name='get_pending_credit_card_applications'),
    path('credit-card/list/status/<int:credit_card_id>/', credit_card_views.change_credit_card_status, name='change_credit_card_status'),
    path('credit-card-usage/', credit_card_views.get_credit_card_usage, name='credit_card_usage'),
    path('pay-credit-card-bills/', credit_card_views.pay_credit_card_bills, name='pay_credit_card_bills'),
    
    # get_credit_card_list
    path('report/create/', report_views.create_report, name='create report'),
    path('report/see/', report_views.get_reports, name='get report'),
    

]
# 