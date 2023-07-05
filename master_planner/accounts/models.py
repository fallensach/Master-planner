from django.db import models, IntegrityError
from django.contrib.auth.models import User
from planning.models import Program, Scheduler

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, blank=True, null=True)
    choices = models.ManyToManyField(Scheduler, blank=True)

    def __str__(self):
        return str(self.user)

def register_account(username: str, email: str, password: str):
    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        account = Account(user=user)
        account.save()
        return True
    
    except IntegrityError:
        return False
    
def get_user(username: str) -> Account | None:
    """Retrieves user object from Account based on session.

    Args:
        request (_type_): _description_

    Returns:
        Account | None: Account object or None
    """
    try:
        user = User.objects.get(username=username)
        #account = Account.objects.get(user=user)
        return user
    
    except IntegrityError:
        return None
