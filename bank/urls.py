# urls.py

from django.urls import path
from .views import auth_views
from .views import transaction_views
from .views import user_views
from .views.Admin import admin_dashboard_card
from .views import account_views
from .views import city_state

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
    path('admin/transaction-statistics/<str:period>', transaction_views.transaction_growth ,name='total_transaction_amount'),
    path('admin/transaction-monthly-summary/', transaction_views.transaction_monthly_summary ,name='transaction_monthly_summary'),
    
    
    path('admin/transaction-statistics-self-debit-card/<str:period>/', transaction_views.debit_card_transaction_sum ,name='total_transaction_amount'),
    path('admin/transaction-statistics-self-credit-card/<str:period>/', transaction_views.credit_card_transaction_count ,name='total_transaction_amount'),
    # path('admin/transaction-monthly-summary-self/', transaction_views.transaction_monthly_summary ,name='transaction_monthly_summary'),
    
    
    
    
    path('admin/transaction/all/', transaction_views.transaction_count ,name='transaction_count'),
    path('admin/user/<int:user_id>/', user_views.user_update_by_admin, name='user_update_by_admin'),
    path('admin/transaction/', transaction_views.admin_transaction_history, name='admin_transaction_history'),
    path('admin/transaction/<int:transaction_id>/', transaction_views.admin_transaction_delete, name='admin_transaction_delete'),
    path('admin/account/', account_views.admin_account_list, name='admin_account_list'),
    path('admin/account/<int:account_id>/', account_views.admin_account_delete, name='admin_account_delete'),
    path('admin/account/edit/<int:account_id>/', account_views.admin_account_edit, name='admin_account_edit'),

    
    
    

    # City and state system
    path('states/', city_state.state_list_create, name='state-list-create'),
    path('states/<int:id>/', city_state.state_detail, name='state-detail'),
    path('cities/', city_state.city_list_create, name='city-list-create'),
    path('cities/<int:id>/', city_state.city_detail, name='city-detail'),
    path('states/<int:state_id>/cities/', city_state.cities_by_state, name='city-list-by-state-id'),

    
]
