import requests

from django.shortcuts import render, redirect
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

from paginas_estaticas.models import PaginaEstatica
from .forms import FormContato
from .models import FormularioContato

# Para os erros ao enviar e-mail
from smtplib import SMTPException


EMAIL_ASSUNTO_BASE = """[CACo] [Ouvidoria] {assunto}"""

EMAIL_MENSAGEM_BASE = """Olá, computeir*s,

Recebemos uma mensagem através do site da ouvidoria do CACo.

Remetente: {remetente}
Assunto: {assunto}

A mensagem é:
"{mensagem}"

Atenciosamente,
Centro acadêmico da computação
"""

RECAPTCHA_URL = 'https://www.google.com/recaptcha/api/siteverify'


def ContatoView(request):
    # Verificamos se estamos recebendo informação ou temos que servir o
    # formulário
    if request.method == 'POST':
        form = FormContato(request.POST)

        # Verificamos se todos os dados respeitam o formulário
        if form.is_valid():

            # Verificamos a resposta do recaptcha
            recaptcha_resposta = request.POST.get('g-recaptcha-response')
            dados = {
                'secret': settings.CAPTCHA_SECRET_KEY,
                'response': recaptcha_resposta
            }
            recaptcha_resultado = requests.post(RECAPTCHA_URL, data=dados).json()
            if settings.DEBUG:
                # Imprimimos o resultado do recaptcha se estivermos em DEBUG
                print('Resultado do recaptcha: "{}"'.format(recaptcha_resultado))

            # Verificamos se o recaptcha permitiu
            if recaptcha_resultado['success']:
                # Inserimos um modelo
                formulario = FormularioContato(
                    contato=form.cleaned_data['contato'],
                    assunto=form.cleaned_data['assunto'],
                    mensagem=form.cleaned_data['mensagem']
                )

                # Enviamos um e-mail
                try:
                    send_mail(
                        subject=EMAIL_ASSUNTO_BASE.format(
                            assunto=formulario.assunto
                        ),
                        message=EMAIL_MENSAGEM_BASE.format(
                            assunto=formulario.assunto,
                            mensagem=formulario.mensagem,
                            remetente=formulario.contato
                        ),
                        from_email=settings.EMAIL_REMETENTE,
                        recipient_list=settings.EMAIL_CONTATO_DESTINATARIO
                    )
                    formulario.email_enviado = True
                except SMTPException:
                    if settings.DEBUG:
                        # Se estamos em debugging, mostramos o erro
                        raise
                    else:
                        # Se não estamos, mostramos a falha ao usuário
                        formulario.save()
                        return redirect('falha/')

                # Salvamos o e-mail de contato
                formulario.save()

                # Será enviado para 'contato/sucesso/'
                return redirect('sucesso/')

        # Em caso de falhas, será enviado para 'contato/falha' com os erros do
        # formulário
        return redirect('falha/')
    else:

        # Tentamos conseguir a página estática de contato
        try:
            pagina = PaginaEstatica.objects.get(endereco='contato/')
        except ObjectDoesNotExist:
            pagina = None

        # Criamos o formulário
        form = FormContato()

        # Servimos
        context = {
            'pagina': pagina,
            'captcha_site_key': settings.CAPTCHA_SITE_KEY,
            'form': form
        }
        return render(request, 'contato.html', context=context)


def ContatoFalhaView(request):
    # Tentamos conseguir a página estática de contato
    try:
        pagina = PaginaEstatica.objects.get(endereco='contato/falha/')
    except ObjectDoesNotExist:
        pagina = None

    context = {
        'pagina': pagina,
        'email': settings.EMAIL_CONTATO
    }
    return render(request, 'contato_falha.html', context=context)
