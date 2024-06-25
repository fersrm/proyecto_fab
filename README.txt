#################################
Crear profile del superuser:

python manage.py shell

from django.contrib.auth.models import User
user = User.objects.get(id=1)
from SistemaApp.models import Profile 
profile = Profile(last_activity=None,image='profile.webp',user_FK=user)
profile.save()
exit()
 