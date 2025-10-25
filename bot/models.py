from django.db import models
from django.core.files.storage import FileSystemStorage

import os

from nika.settings import BASE_DIR

# Хранилище для статики
static_fs = FileSystemStorage(location=f"{BASE_DIR}/media")


class GeneralInfo(models.Model):
    '''
        Общая информация для сообщений, админов и т. д.
    '''
    start_text = models.TextField(verbose_name='Стартовое сообщение', max_length=2048, default='Привет! Что ты хочешь узнать?')
    admins = models.CharField(verbose_name='Список админов', help_text='Указывать Id через |', max_length=2048, null=True, blank=True)

    def __str__(self):
        return f'Общая информация'
    
    class Meta:
        verbose_name = "Общая информация"
        verbose_name_plural = "Общая информация"
    

# Пути для доп. инфы
def optional_image_path(instance, filename):
    return os.path.join(f'images/optional/{filename}')


class OptionalInfo(models.Model):
    '''
        Дополнительная информация по лагерю
    '''
    title = models.CharField(verbose_name='Текст кнопки', help_text='Максимальная длина 60 символа', max_length=60)
    slug = models.SlugField(verbose_name='Слаг', unique=True)
    text = models.TextField(verbose_name='Текст сообщения', help_text='Максимальная длина 1024 символа, если с файлом и 4096, если без')
    file = models.FileField(verbose_name='Файл изображения', storage=static_fs, upload_to=optional_image_path, null=True, blank=True)
    is_photo = models.BooleanField(verbose_name='Сжать изображение', help_text='Отметить, если нужно отправить файл, как сжатое изображение') 

    def __str__(self):
        return f'Дополнительная информация {self.title}'
    
    class Meta:
        verbose_name = "Дополнительная информация"
        verbose_name_plural = "Дополнительные информации"
    

# class OptionalFile(models.Model):
#     info = models.ForeignKey(to=OptionalInfo)
#     file = models.FileField(verbose_name='Файл для сообщения', storage=static_fs, upload_to=optional_image_path)
#     is_main = models.BooleanField(verbose_name='Изображение', help_text='Поставить')

class Place(models.Model):
    '''
        Места где будут проходить смены
    '''
    title = models.CharField(verbose_name='Название', help_text='Максимальная длина 60 символа', max_length=60)
    slug = models.SlugField(verbose_name='Слаг', unique=True)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    latitude = models.DecimalField(verbose_name='Широта', help_text='Максимальное количество цифр после точки - 6', null=True, max_digits=9, decimal_places=6, blank=True)
    longitude = models.DecimalField(verbose_name='Долгота', help_text='Максимальное количество цифр после точки - 6', null=True, max_digits=9, decimal_places=6, blank=True)

    def __str__(self):
        return f'Место {self.title}'
    
    class Meta:
        verbose_name = "Место"
        verbose_name_plural = "Местa"
    
# Пути для баннеров смен
def session_image_path(instance, filename):
    return os.path.join(f"images/sessions/{instance.slug}.{filename.split('.')[-1]}")


class Session(models.Model):
    '''
        Модель для смен
    '''
    title = models.CharField(verbose_name='Название', help_text='Максимальная длина 60 символа', max_length=60)
    slug = models.SlugField(verbose_name='Слаг', unique=True)
    form_url = models.CharField(verbose_name='Ссылка на форму', help_text='При наличии', max_length=128, null=True, blank=True)
    place = models.ForeignKey(to=Place, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.FileField(verbose_name='Постер', storage=static_fs, upload_to=session_image_path, null=True, blank=True)
    description = models.TextField(verbose_name='Описание', help_text='Максимальная длина 1024 символа', max_length=1024, null=True, blank=True)
    start_date = models.DateField(verbose_name='Начало смены', null=True, blank=True)
    end_date = models.DateField(verbose_name='Конец смены', null=True, blank=True)
    notes = models.TextField(verbose_name='Заметки', help_text='Видит только админ', null=True, blank=True)

    def __str__(self):
        return f'Смена {self.title}'
    
    class Meta:
        verbose_name = "Смена"
        verbose_name_plural = "Смены"
    

