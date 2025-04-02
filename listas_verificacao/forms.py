from django import forms
from .models import (
    ListaVerificacao, Turma, Objetivo, CategoriaObjetivo,
    ObjetivoPredefinido, Disciplina, AprendizagemEssencial, ConfiguracaoNotificacao,
    ConquistaColetiva, ReconhecimentoContribuicao, ProjetoColaborativo, CircuitoComunicacao,
    MetaAprendizagem, AlteracaoMeta, ReflexaoMeta, AcompanhamentoMeta, Checklist, Item, Categoria, Meta
)
from django.contrib.auth.models import User

class CategoriaObjetivoForm(forms.ModelForm):
    class Meta:
        model = CategoriaObjetivo
        fields = ['nome', 'descricao', 'ordem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class ObjetivoPredefinidoForm(forms.ModelForm):
    class Meta:
        model = ObjetivoPredefinido
        fields = ['codigo', 'titulo', 'descricao', 'categoria', 'ordem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class ListaVerificacaoForm(forms.ModelForm):
    class Meta:
        model = ListaVerificacao
        fields = ['titulo', 'descricao', 'turma', 'disciplina', 'ano_escolar', 'aprendizagens']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'aprendizagens': forms.CheckboxSelectMultiple(),
        }

class ObjetivoForm(forms.ModelForm):
    class Meta:
        model = Objetivo
        fields = ['titulo', 'descricao', 'ordem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['nome']

class ImportarAprendizagensForm(forms.Form):
    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.all(),
        label='Disciplina'
    )
    ano_escolar = forms.ChoiceField(
        choices=[(i, f'{i}º Ano') for i in range(1, 13)],
        label='Ano Escolar'
    )
    ficheiro_csv = forms.FileField(
        label='Ficheiro CSV',
        help_text='O ficheiro deve conter duas colunas: código da aprendizagem e descrição'
    )

class AprendizagemEssencialForm(forms.ModelForm):
    class Meta:
        model = AprendizagemEssencial
        fields = ['codigo', 'descricao', 'disciplina', 'dominio', 'subdominio', 'ano_escolar', 'ordem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class ConfiguracaoNotificacaoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoNotificacao
        fields = [
            'notif_baixo_progresso',
            'notif_prazos',
            'notif_duvidas',
            'notif_conquistas',
            'notif_feedback',
            'receber_emails',
            'frequencia_emails',
            'horario_inicio',
            'horario_fim',
            'dias_semana'
        ]
        widgets = {
            'horario_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time'}),
            'dias_semana': forms.TextInput(attrs={
                'pattern': '^[1-7](,[1-7])*$',
                'title': 'Introduza os números dos dias da semana (1-7) separados por vírgula. Ex: 1,2,3,4,5'
            })
        }
    
    def clean_dias_semana(self):
        dias = self.cleaned_data['dias_semana']
        try:
            # Verifica se são números válidos
            dias_list = [int(d.strip()) for d in dias.split(',')]
            # Verifica se estão no intervalo correto
            if not all(1 <= d <= 7 for d in dias_list):
                raise forms.ValidationError('Os dias devem estar entre 1 e 7.')
            # Remove duplicatas e ordena
            dias_list = sorted(set(dias_list))
            return ','.join(str(d) for d in dias_list)
        except ValueError:
            raise forms.ValidationError('Formato inválido. Use números de 1 a 7 separados por vírgula.')

class ConquistaColetivaForm(forms.ModelForm):
    """Formulário para criar e editar conquistas coletivas."""
    class Meta:
        model = ConquistaColetiva
        fields = [
            'titulo', 'descricao', 'tipo', 'turma', 'participantes',
            'aprendizagens', 'contribuicoes', 'impacto', 'beneficiarios',
            'reflexao_impacto', 'evidencias', 'links_relacionados',
            'proximos_passos'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'contribuicoes': forms.Textarea(attrs={'rows': 4}),
            'beneficiarios': forms.Textarea(attrs={'rows': 3}),
            'reflexao_impacto': forms.Textarea(attrs={'rows': 4}),
            'links_relacionados': forms.Textarea(attrs={'rows': 2}),
            'proximos_passos': forms.Textarea(attrs={'rows': 3}),
            'participantes': forms.SelectMultiple(attrs={'class': 'select2'}),
            'aprendizagens': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

class ReconhecimentoContribuicaoForm(forms.ModelForm):
    """Formulário para registrar reconhecimentos de contribuição."""
    class Meta:
        model = ReconhecimentoContribuicao
        fields = [
            'contribuidor', 'tipo', 'descricao', 'turma', 'conquista',
            'impacto', 'evidencias'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'impacto': forms.Textarea(attrs={'rows': 3}),
            'contribuidor': forms.Select(attrs={'class': 'select2'}),
            'conquista': forms.Select(attrs={'class': 'select2'}),
        }

class ProjetoColaborativoForm(forms.ModelForm):
    """Formulário para criar e editar projetos colaborativos."""
    class Meta:
        model = ProjetoColaborativo
        fields = [
            'titulo', 'descricao', 'objetivo', 'turma', 'participantes',
            'aprendizagens', 'data_inicio', 'data_fim_prevista',
            'responsabilidades', 'recursos_necessarios', 'desafios',
            'solucoes', 'resultados', 'aprendizagens_alcancadas',
            'feedback_comunidade'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'objetivo': forms.Textarea(attrs={'rows': 3}),
            'responsabilidades': forms.Textarea(attrs={'rows': 4}),
            'recursos_necessarios': forms.Textarea(attrs={'rows': 3}),
            'desafios': forms.Textarea(attrs={'rows': 3}),
            'solucoes': forms.Textarea(attrs={'rows': 3}),
            'resultados': forms.Textarea(attrs={'rows': 4}),
            'aprendizagens_alcancadas': forms.Textarea(attrs={'rows': 3}),
            'feedback_comunidade': forms.Textarea(attrs={'rows': 3}),
            'participantes': forms.SelectMultiple(attrs={'class': 'select2'}),
            'aprendizagens': forms.SelectMultiple(attrs={'class': 'select2'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim_prevista': forms.DateInput(attrs={'type': 'date'}),
        }

class CircuitoComunicacaoForm(forms.ModelForm):
    """Formulário para criar e editar circuitos de comunicação."""
    class Meta:
        model = CircuitoComunicacao
        fields = [
            'titulo', 'descricao', 'tipo', 'turma', 'participantes',
            'aprendizagens', 'data_realizacao', 'duracao',
            'pontos_principais', 'conclusoes', 'acoes_decorrentes',
            'evidencias'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'pontos_principais': forms.Textarea(attrs={'rows': 4}),
            'conclusoes': forms.Textarea(attrs={'rows': 3}),
            'acoes_decorrentes': forms.Textarea(attrs={'rows': 3}),
            'participantes': forms.SelectMultiple(attrs={'class': 'select2'}),
            'aprendizagens': forms.SelectMultiple(attrs={'class': 'select2'}),
            'data_realizacao': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class MetaAprendizagemForm(forms.ModelForm):
    """Formulário para criar e editar metas de aprendizagem."""
    class Meta:
        model = MetaAprendizagem
        fields = [
            'titulo', 'descricao', 'tipo', 'turma', 'aprendizagens',
            'participantes', 'data_inicio', 'data_fim', 'justificativa',
            'plano_acao', 'recursos_necessarios'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select select2'}),
            'turma': forms.Select(attrs={'class': 'form-select select2'}),
            'aprendizagens': forms.SelectMultiple(attrs={'class': 'form-select select2'}),
            'participantes': forms.SelectMultiple(attrs={'class': 'form-select select2'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'justificativa': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'plano_acao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recursos_necessarios': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not user.is_teacher:
            self.fields['turma'].queryset = user.turmas_aluno.all()
            self.fields['participantes'].queryset = User.objects.filter(
                turmas_aluno__in=user.turmas_aluno.all()
            ).distinct()

class AlteracaoMetaForm(forms.ModelForm):
    class Meta:
        model = AlteracaoMeta
        fields = ['tipo', 'descricao', 'justificativa']

class ReflexaoMetaForm(forms.ModelForm):
    """Formulário para registrar reflexões sobre metas."""
    class Meta:
        model = ReflexaoMeta
        fields = [
            'conteudo', 'nivel_satisfacao', 'dificuldades_encontradas',
            'estrategias_sucesso', 'sugestoes_melhoria'
        ]
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'nivel_satisfacao': forms.Select(attrs={'class': 'form-select select2'}),
            'dificuldades_encontradas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'estrategias_sucesso': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'sugestoes_melhoria': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

class AcompanhamentoMetaForm(forms.ModelForm):
    """Formulário para registrar acompanhamento de metas."""
    class Meta:
        model = AcompanhamentoMeta
        fields = ['progresso', 'observacoes', 'sugestoes', 'recursos_sugeridos']
        widgets = {
            'progresso': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'observacoes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'sugestoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recursos_sugeridos': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['titulo', 'descricao', 'categoria', 'prioridade']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'prioridade': forms.Select(choices=[
                (0, 'Baixa'),
                (1, 'Média'),
                (2, 'Alta')
            ])
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['texto', 'descricao', 'ordem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'ordem': forms.NumberInput(attrs={'min': 0})
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao', 'cor', 'icone']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'cor': forms.TextInput(attrs={'type': 'color'}),
            'icone': forms.TextInput(attrs={'placeholder': 'Ex: fa-check'})
        }

class MetaForm(forms.ModelForm):
    class Meta:
        model = Meta
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'checklist']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'})
        } 