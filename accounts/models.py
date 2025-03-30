from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    bio = models.TextField(
        blank=True,
        verbose_name=_('Biografia')
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name=_('Avatar')
    )

    class Meta:
        verbose_name = _('Utilizador')
        verbose_name_plural = _('Utilizadores')
        permissions = [
            ("can_approve_posts", "Pode aprovar posts"),
            ("can_moderate_comments", "Pode moderar comentários"),
            ("can_manage_classes", "Pode gerenciar turmas"),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    @property
    def is_teacher(self):
        return self.groups.filter(name='teacher').exists()

    @property
    def is_student(self):
        return self.groups.filter(name='student').exists()

    @property
    def is_guest(self):
        return self.groups.filter(name='guest').exists()

    @property
    def user_type(self):
        if self.is_superuser:
            return 'admin'
        elif self.is_teacher:
            return 'teacher'
        elif self.is_student:
            return 'student'
        elif self.is_guest:
            return 'guest'
        return 'guest'

    def get_user_type_display(self):
        user_type = self.user_type
        type_display = {
            'admin': 'Administrador',
            'teacher': 'Professor',
            'student': 'Aluno',
            'guest': 'Convidado'
        }
        return type_display.get(user_type, 'Convidado')
