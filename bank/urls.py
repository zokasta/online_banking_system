# urls.py

from django.urls import path
from bank.views import auth_views
from bank.views import transaction_views
from bank.views import user_views
from bank.views.Admin import admin_dashboard_card

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

    
    path('admin/user-statistics/', admin_dashboard_card.user_growth ,name='user_statistics'),
    path('admin/transaction/all/', transaction_views.transaction_count ,name='transaction_count'),
    path('admin/user/<int:user_id>/', user_views.user_update_by_admin, name='user_update_by_admin')

    
]