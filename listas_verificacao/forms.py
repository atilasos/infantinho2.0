from django import forms
from .models import (
    ListaVerificacao, Turma, Objetivo, CategoriaObjetivo,
    ObjetivoPredefinido, Disciplina, AprendizagemEssencial, ConfiguracaoNotificacao
)

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
    arquivo_csv = forms.FileField(
        label='Arquivo CSV',
        help_text='O arquivo deve conter duas colunas: código da aprendizagem e descrição'
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
                'title': 'Digite os números dos dias da semana (1-7) separados por vírgula. Ex: 1,2,3,4,5'
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