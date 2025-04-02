from django import forms
from .models import Comment, Post, Category, Class
from django.utils.text import slugify
from taggit.forms import TagWidget

class CommentForm(forms.ModelForm):
    """Formulário para criar e editar comentários."""
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class PostForm(forms.ModelForm):
    """Formulário para criar e editar posts."""
    class Meta:
        model = Post
        fields = ('title', 'content', 'category', 'class_group', 'tags', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'class_group': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'data-role': 'tagsinput'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['category'].widget.attrs.update({'class': 'form-control'})
        self.fields['class_group'].widget.attrs.update({'class': 'form-control'})
        self.fields['status'].widget.attrs.update({'class': 'form-control'})
        self.fields['content'].required = False
        self.fields['class_group'].required = False
        self.fields['status'].initial = 'draft'
        
        # Filtra as turmas disponíveis para o usuário
        if user:
            if user.is_teacher:
                self.fields['class_group'].queryset = Class.objects.filter(teacher=user)
            else:
                self.fields['class_group'].queryset = Class.objects.filter(students=user)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.title)
        if commit:
            instance.save()
        return instance

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or not content.strip():
            raise forms.ValidationError('O conteúdo é obrigatório.')
        return content.strip()

    def suggest_category(self):
        """Sugere uma categoria baseada no conteúdo do post."""
        from ai_core.agents import blog_agent
        content = self.cleaned_data.get('content', '')
        if content:
            try:
                suggestions = blog_agent.suggest_categories_and_tags(content)
                if suggestions and 'category' in suggestions:
                    return suggestions['category']
            except Exception as e:
                print(f"Erro ao sugerir categoria: {str(e)}")
        return None

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome da categoria'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Digite a descrição da categoria'
            })
        }

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ('name', 'students')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control'}),
        } 