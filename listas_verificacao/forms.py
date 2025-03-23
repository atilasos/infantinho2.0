from django import forms
from .models import ListaVerificacao, Turma, Objetivo, CategoriaObjetivo, ObjetivoPredefinido

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
        fields = ['titulo', 'descricao', 'turma', 'objetivos_predefinidos']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'objetivos_predefinidos': forms.CheckboxSelectMultiple(),
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