from datetime import timedelta
import uuid

from django.db import models
from django.utils.text import slugify
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils import timezone


class Context(models.Model):
    # 2022-2023/IESPTO/DAW/PRO
    # 2023-1/EOI/NAC
    code = models.SlugField(unique=True, max_length=32)
    name = models.CharField(unique=True, max_length=128)
    start_date = models.DateField()
    end_date = models.DateField()
    max_score = models.DecimalField(decimal_places=2, max_digits=5, default=10)  # 3!
    score_limit = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=10,
        help_text='Número de ejercicios a completar correctamente para conseguir'
        ' "max_score" puntos',
    )

    @classmethod
    def create_context(cls, name, code='', start_date=None, end_date=None, duration=91):
        code = code or slugify(name)
        start_date = start_date or timezone.now().date()
        end_date = end_date or start_date + timedelta(days=duration)
        context = cls(name=name, code=code, start_date=start_date, end_date=end_date)
        context.save()
        section = Section(name='default', start_date=start_date, context=context)
        section.save()
        return context


class Section(models.Model):
    name = models.CharField(max_length=32)
    start_date = models.DateField()
    context = models.ForeignKey(
        Context,
        on_delete=models.PROTECT,
        related_name='sections',
    )


class Student(models.Model):
    username = models.SlugField(unique=True, max_length=32)
    password_hash = models.CharField(max_length=32)  # md5
    context = models.ForeignKey(
        Context,
        on_delete=models.PROTECT,
        related_name='students',
    )
    last_active = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '{self.username}@{self.context.name}'

    def touch(self):
        """Registro la actividad de un estudiante.
        """
        self.last_active = timezone.now()
        self.save()

    @classmethod
    def load_by_username(cls, username):
        """Recupera un estudiante de la base de datos usando el username.

        Si no es capaz de encontrar ningún alumno con ese
        username, devuelve `None`.
        """
        try:
            student = cls.objects.select_related('context').get(username=username)
            return student
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return None


class AuthToken(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="tokens"
    )
    value = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(blank=True, null=True, default=None)

    def is_valid(self):
        return self.valid_until is None

    def revoke_token(self):
        self.valid_until = timezone.now()
        self.save()

    @classmethod
    def issue_token_for_student(cls, student):
        token = cls(student=student)
        token.save()
        student.touch()
        return token
