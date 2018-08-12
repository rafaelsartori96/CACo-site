from django import forms
from django.contrib import admin
from .models import *
# Para editor de content da página
from ckeditor.widgets import CKEditorWidget
# Para substituir o formulário de FlatPage para outro com editor
from django.contrib.sites.models import Site
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.forms import FlatpageForm

# Colocamos o editor no formulário de administrador
class FormPaginaEstatica(FlatpageForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='toolbar_Full'))

    class Meta:
        model = PaginaEstatica
        fields = '__all__'

# Criamos o administrador para o formulário
class AdminPaginaEstatica(admin.ModelAdmin):
    form = FormPaginaEstatica
    list_display = ('title', 'url')
    fields = ('title','url','content')

    def save_model(self, request, object, form, change):
        object.save()
        # Definimos o site da página como o site atual (ou ele não aparecerá)
        object.sites.add(Site.objects.get_current())

admin.site.register(MenuDropdown)
admin.site.register(ItemMenu)

# Registramos o administrador para PaginaEstatica
admin.site.register(PaginaEstatica, AdminPaginaEstatica)
# Não queremos mostrá-los no admin
admin.site.unregister(FlatPage)
admin.site.unregister(Site)