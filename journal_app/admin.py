from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Article)
admin.site.register(Journal)
admin.site.register(Volume)
admin.site.register(Issue)
admin.site.register(Department)
admin.site.register(DepartmentSettings)
admin.site.register(Profile)