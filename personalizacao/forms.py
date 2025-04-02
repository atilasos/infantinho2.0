from django import forms
from .models import Tema, Layout, PreferenciaUsuario, Widget, DashboardUsuario, WidgetDashboard

class TemaForm(forms.ModelForm):
    """Formulário para criação e edição de temas."""
    class Meta:
        model = Tema
        fields = ['nome', 'descricao', 'cores_primarias', 'cores_secundarias', 'fonte_principal', 'fonte_secundaria']
        widgets = {
            'cores_primarias': forms.Textarea(attrs={'rows': 3}),
            'cores_secundarias': forms.Textarea(attrs={'rows': 3}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class LayoutForm(forms.ModelForm):
    """Formulário para criação e edição de layouts."""
    class Meta:
        model = Layout
        fields = ['nome', 'descricao', 'estrutura', 'configuracoes']
        widgets = {
            'estrutura': forms.Textarea(attrs={'rows': 5}),
            'configuracoes': forms.Textarea(attrs={'rows': 5}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class PreferenciaUsuarioForm(forms.ModelForm):
    """Formulário para gerenciamento das preferências do usuário."""
    class Meta:
        model = PreferenciaUsuario
        fields = ['tema', 'layout', 'tamanho_fonte', 'alto_contraste', 'reducao_movimento', 
                 'notificacoes_email', 'notificacoes_push', 'notificacoes_som', 'idioma']
        widgets = {
            'tamanho_fonte': forms.Select(choices=[
                ('pequeno', 'Pequeno'),
                ('medio', 'Médio'),
                ('grande', 'Grande'),
            ]),
            'idioma': forms.Select(choices=[
                ('pt-br', 'Português (Brasil)'),
                ('en', 'English'),
                ('es', 'Español'),
            ]),
        }

class WidgetForm(forms.ModelForm):
    """Formulário para criação e edição de widgets."""
    class Meta:
        model = Widget
        fields = ['nome', 'tipo', 'descricao', 'configuracoes', 'ativo']
        widgets = {
            'configuracoes': forms.Textarea(attrs={'rows': 5}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class WidgetDashboardForm(forms.ModelForm):
    class Meta:
        model = WidgetDashboard
        fields = ['widget', 'posicao_x', 'posicao_y', 'largura', 'altura', 'configuracoes', 'ativo']
        widgets = {
            'posicao_x': forms.NumberInput(attrs={'min': 0}),
            'posicao_y': forms.NumberInput(attrs={'min': 0}),
            'largura': forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'altura': forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'configuracoes': forms.Textarea(attrs={'rows': 5}),
        }

class DashboardUsuarioForm(forms.ModelForm):
    class Meta:
        model = DashboardUsuario
        fields = ['layout']
        widgets = {
            'layout': forms.Textarea(attrs={'rows': 5}),
        } 