from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

from ..models import AtaReuniao, AtaAssembleia


# Registramos a tag
register = template.Library()

@register.simple_tag
def imprime_tipo_ata(ata):
    if isinstance(ata, AtaAssembleia):
        return AtaAssembleia.display_tipo_ata(ata)
    elif isinstance(ata, AtaReuniao):
        return AtaReuniao.display_tipo_ata(ata)
    else:
        return ""


@register.simple_tag
def cor_alert_ata(ata):
    if isinstance(ata, AtaAssembleia):
        return "danger"
    elif isinstance(ata, AtaReuniao):
        return "warning"
    else:
        return "info"


@register.simple_tag
def ultimas_atas():
    # Pegamos as atas
    reunioes = AtaReuniao.objects.filter(visivel=True).all()[0 : settings.ATAS_BARRA_LATERAL]
    assembleias = AtaAssembleia.objects.filter(visivel=True).all()[0 : settings.ATAS_BARRA_LATERAL]

    # Fazemos uma lista de atas
    atas = []
    atas += reunioes
    atas += assembleias

    # Conferimos se não há atas
    if len(atas) == 0:
        return ""

    # Ordenamos por data
    atas.sort(key=lambda ata: ata.data_criacao, reverse=True)

    # Construímos a saída
    saida = """"""
    # Iniciamos uma linha
    saida += """<div class="row">\n"""
    # Iniciamos uma coluna
    saida += """<div class="col">\n"""

    # Fazemos uma caixa em volta de tudo
    saida += """<div class="alert alert-secondary rounded shadow-sm">\n"""
    # Fazemos um header
    saida += """<h5 class="text-center">Últimas atas</h5>\n"""
    saida += """<hr>\n"""
    # Adicionamos apenas algumas atas
    num_atas = 0

    # Para cada ata, formamos um quadrado
    for ata in atas:
        num_atas += 1

        # Abrimos a linha
        saida += """<div class="row">\n"""
        # Abrimos a coluna
        saida += """<div class="col">\n"""
        # Abrimos o alerta
        saida += """<div class="alert alert-{0} shadow-sm" role="alert">\n""".format(cor_alert_ata(ata))
        # Iniciamos o link
        saida += """<a href="{0}" class="alert-link">\n""".format(ata.get_url())

        # Adicionamos o nome da ata
        saida += """<b>{0}</b>\n""".format(ata)

        # Fechamos o link
        saida += """</a>\n"""
        # Fechamos o alerta
        saida += """</div>\n"""
        # Fechamos a coluna
        saida += """</div>\n"""
        # Fechamos a linha
        saida += """</div>\n"""

        # Paramos se já adicionamos atas suficientes
        if num_atas >= settings.ATAS_BARRA_LATERAL:
            break

    # Terminamos a caixa
    saida += """</div>\n"""

    # Terminamos a coluna
    saida += """</div>\n"""
    # Terminamos a linha
    saida += """</div>\n"""

    # Imprimimos
    return saida
