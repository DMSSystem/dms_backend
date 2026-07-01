# audit_log/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import AuditLog
from .middleware import get_current_user, get_current_ip

# Models to track
from users.models import User
from students.models import Student
from rooms.models import Room
from leave_out.models import LeaveOut
from maintenance.models import MaintenanceRequest
from duty_roster.models import DutyRoster, DutyAssignment
from inspection.models import Inspection

def log_action(instance, action, module, description):
    current_user = get_current_user()
    current_ip = get_current_ip()
    
    # Don't log if the action was created by audit logging itself (prevent loop)
    if module == 'auditlog':
        return
        
    user = current_user
    if user:
        # Check if the user still exists in the database to prevent ForeignKeyViolation.
        # This handles cases where the user deletes their own account, or is deleted
        # in a bulk deletion, but is still set in thread-local storage.
        if not User.objects.filter(pk=user.pk).exists():
            user = None

    AuditLog.objects.create(
        user=user,
        action=action,
        module=module,
        description=description,
        ip_address=current_ip
    )


# Receivers for post_save
@receiver(post_save, sender=User)
@receiver(post_save, sender=Student)
@receiver(post_save, sender=Room)
@receiver(post_save, sender=LeaveOut)
@receiver(post_save, sender=MaintenanceRequest)
@receiver(post_save, sender=DutyRoster)
@receiver(post_save, sender=DutyAssignment)
@receiver(post_save, sender=Inspection)
def model_post_save(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    module = sender._meta.model_name
    
    if sender == User:
        description = f"User '{instance.username}' (role: {instance.role}) was {action.lower()}d."
    elif sender == Student:
        description = f"Student '{instance.full_name}' (adm: {instance.admission_no}) was {action.lower()}d."
    elif sender == Room:
        description = f"Room '{instance}' was {action.lower()}d."
    elif sender == LeaveOut:
        description = f"Leave-out request for '{instance.student.full_name}' (dates: {instance.leave_date} to {instance.return_date}, status: {instance.status}) was {action.lower()}d."
    elif sender == MaintenanceRequest:
        description = f"Maintenance request for '{instance.location}' (status: {instance.status}) was {action.lower()}d."
    elif sender == DutyRoster:
        description = f"Duty roster for '{instance.dorm_name}' (date: {instance.duty_date}, task: {instance.task}) was {action.lower()}d."
    elif sender == DutyAssignment:
        description = f"Duty assignment for '{instance.student.full_name}' (status: {instance.status}) was {action.lower()}d."
    elif sender == Inspection:
        description = f"Inspection for Room '{instance.room}' (status: {instance.status}) was {action.lower()}d."
    else:
        description = f"{sender._meta.verbose_name} was {action.lower()}d."
        
    log_action(instance, action, module, description)

# Receivers for post_delete
@receiver(post_delete, sender=User)
@receiver(post_delete, sender=Student)
@receiver(post_delete, sender=Room)
@receiver(post_delete, sender=LeaveOut)
@receiver(post_delete, sender=MaintenanceRequest)
@receiver(post_delete, sender=DutyRoster)
@receiver(post_delete, sender=DutyAssignment)
@receiver(post_delete, sender=Inspection)
def model_post_delete(sender, instance, **kwargs):
    action = 'DELETE'
    module = sender._meta.model_name
    
    if sender == User:
        description = f"User '{instance.username}' was deleted."
    elif sender == Student:
        description = f"Student '{instance.full_name}' (adm: {instance.admission_no}) was deleted."
    elif sender == Room:
        description = f"Room '{instance}' was deleted."
    elif sender == LeaveOut:
        description = f"Leave-out request for '{instance.student.full_name}' (dates: {instance.leave_date} to {instance.return_date}) was deleted."
    elif sender == MaintenanceRequest:
        description = f"Maintenance request for '{instance.location}' was deleted."
    elif sender == DutyRoster:
        description = f"Duty roster for '{instance.dorm_name}' (date: {instance.duty_date}) was deleted."
    elif sender == DutyAssignment:
        description = f"Duty assignment for '{instance.student.full_name}' was deleted."
    elif sender == Inspection:
        description = f"Inspection for Room '{instance.room}' was deleted."
    else:
        description = f"{sender._meta.verbose_name} was deleted."
        
    log_action(instance, action, module, description)

# Receivers for Auth
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip_addr = None
    if request and hasattr(request, 'META'):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_addr = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        
    AuditLog.objects.create(
        user=user,
        action='LOGIN',
        module='user',
        description=f"User '{user.username}' logged in successfully.",
        ip_address=ip_addr
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ip_addr = None
    if request and hasattr(request, 'META'):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_addr = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        
    if user:
        AuditLog.objects.create(
            user=user,
            action='LOGOUT',
            module='user',
            description=f"User '{user.username}' logged out.",
            ip_address=ip_addr
        )
