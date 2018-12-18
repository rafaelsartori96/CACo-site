# Para os erros ao enviar e-mail
from smtplib import SMTPException

from django.http import Http404
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist

from paginas_estaticas.models import PaginaEstatica
from util import util

from .models import Avaliacao, CodigoDisciplina, Disciplina, Periodo, TipoAvaliacao
from .forms import FormAvaliacao


def BancoDeProvasView(request):
    try:
        # Tentamos conseguir a página estática do banco de provas
        pagina = PaginaEstatica.objects.get(endereco='banco-de-provas/')
    except ObjectDoesNotExist:
        pagina = None

    # Pegamos os dados da query
    busca = request.GET.get('busca')

    if busca is None:
        avaliacoes = None
    else:
        # Buscamos todos os códigos de disciplinas
        disciplinas = []
        codigos = CodigoDisciplina.objects.filter(codigo__icontains=busca).all()
        for codigo in codigos:
            # Colocamos na lista de disciplinas apenas as que foram aprovadas
            # e não automaticamente criadas
            if codigo.disciplina.autorizada:
                disciplinas.append(codigo.disciplina)

        # Buscamos as avaliações com qualquer combinação desses dados
        avaliacoes = Avaliacao.objects.filter(
            Q(disciplina__in=disciplinas) | \
            Q(docente__icontains=busca) | \
            Q(tipo_avaliacao__nome__icontains=busca) | \
            Q(quantificador_avaliacao__icontains=busca) | \
            Q(periodo__nome__icontains=busca) | \
            Q(ano__icontains=busca),
            # Filtramos as avaliações visíveis
            visivel=True,
            disciplina__autorizada=True
        ).all()[0:settings.MAX_LENGTH_MAX_AVALIACOES]

    # Servimos a página
    context = {
        'pagina': pagina,
        'busca': busca,
        'avaliacoes': avaliacoes,
    }
    return render(request, 'banco_de_provas.html', context=context)


def SubmeterProvaView(request):
    # Se não estamos em POST, temos que servir a página

    try:
        # Tentamos conseguir a página estática para contribuições
        pagina = PaginaEstatica.objects.get(endereco='banco-de-provas/contribuir/')
    except ObjectDoesNotExist:
        pagina = None

    # Inicializamos contexto
    context = {
        'captcha_site_key': settings.CAPTCHA_SITE_KEY,
        'pagina': pagina,
    }

    # Verificamos se estamos recebendo informação ou temos que servir o
    # formulário
    if request.method != 'POST':

        # Criamos o formulário
        context['form'] = FormAvaliacao()

        # Apenas servimos
        return render(request, 'contribuir_formulario.html', context=context)

    else:

        # Se estamos em POST, estamos recebendo o formulário
        form = FormAvaliacao(request.POST, request.FILES)
        context['form'] = form

        # Conferimos o Recaptcha
        if not util.recaptcha_valido(request):
            # Avisamos o usuário
            messages.add_message(
                request, messages.SUCCESS,
                'Recaptcha inválido! Atualize a página e tente novamente mais tarde.',
                extra_tags='danger'
            )

            # Redirecionamos à página de contribuição novamente
            return redirect(reverse('banco-de-provas/contribuir/'))

        # Verificamos se todos os dados respeitam o formulário
        if not form.is_valid():

            # Caso o formulário não for preenchido corretamente, avisamos o
            # usuário
            form.add_error(
                None,
                'O formulário não foi preenchido corretamente!'
            )

            # Redirecionamos ao formulário
            return render(request, 'contribuir_formulario.html', context=context)

        # Obtemos as informações limpas do formulário
        # Observação: os tipos são mantidos, Django é excelente <3
        codigo_string = form.cleaned_data['codigo_disciplina']
        docente = form.cleaned_data['docente']
        # Tipo de avaliação deve possuir uma opção chave para os formulários
        # como "Não sei dizer ou não encontrei o tipo que procuro"
        tipo_avaliacao = form.cleaned_data['tipo_avaliacao']
        quantificador = form.cleaned_data['quantificador']
        periodo = form.cleaned_data['periodo']
        ano = form.cleaned_data['ano']
        arquivo = form.cleaned_data['arquivo']

        # Temos que determinar em qual disciplina colocamos. Fazemos isso pelo
        # nome
        try:
            codigo_disciplina = CodigoDisciplina.objects.get(
                codigo=codigo_string
            )

            # Se o código já foi registrado, basta pegar a disciplina
            # correspondente
            disciplina = codigo_disciplina.disciplina
        except ObjectDoesNotExist:
            # Se não há código registrado, precisamos criar uma nova

            # Criamos uma nova disciplina não autorizada
            disciplina = Disciplina(
                autorizada=False
            )
            disciplina.save()

            # Agora criamos um nome para a disciplina
            # Consideramos o nome como o mais atualizado
            codigo_disciplina = CodigoDisciplina(
                disciplina=disciplina,
                nome_atualizado=True,
                codigo=codigo_string.lower(),

            )
            codigo_disciplina.save()

        # Agora que já temos a disciplina, que era o mais difícil, basta
        # inserir numa avaliação
        avaliacao = Avaliacao(
            disciplina=disciplina,
            docente=docente,
            tipo_avaliacao=tipo_avaliacao,
            quantificador_avaliacao=quantificador,
            periodo=periodo, # aceita None (período é uma instância mesmo)
            ano=ano,
            arquivo=arquivo
        )
        avaliacao.save()

        # Agora mandamos um e-mail


        # Falamos ao usuário que o formulário foi enviado com sucesso e que
        # avaliaremos
        messages.add_message(
            request, messages.SUCCESS,
            'Avaliação enviada! Membros do centro acadêmico avaliarão e logo a prova estará disponível. Se quiser, nos envie outra avaliação!',
            extra_tags='success'
        )

        # Mostramos a página do formulário
        return render(request, 'contribuir_formulario.html', context=context)
