from django import forms
from .models import (
    ListaVerificacao, Turma, Objetivo, CategoriaObjetivo,
    ObjetivoPredefinido, Disciplina, AprendizagemEssencial
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