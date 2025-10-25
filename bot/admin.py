from django.contrib import admin

from .models import GeneralInfo, Place, Session, OptionalInfo
from .views import refresh_general

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    '''
        Модель для смен, для отображения в общей информации
    '''
    prepopulated_fields = {"slug": ("title",)}


@admin.register(OptionalInfo)
class OptionalInfoAdmin(admin.ModelAdmin):
    '''
        Модель для доп информации в общей информации
    '''
    prepopulated_fields = {"slug": ("title",)}


@admin.register(GeneralInfo)
class GeneralInfoAdmin(admin.ModelAdmin):
    '''
        Общая информация
    '''

    def save_model(self, request, obj, form, change):   
        # Обновление данных при сохранении
        super().save_model(request, obj, form, change)
        refresh_general()
        return


@admin.register(Session)
class ProjectAdmim(admin.ModelAdmin):
    '''
        Модель для проекта
    '''
    prepopulated_fields = {"slug": ("title",)}
