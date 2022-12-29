import requests

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from django.core.management.base import BaseCommand
from core.models import Context

API_LOGIN = 'http://localhost:8888/api/login'


class Command(BaseCommand):

    console = Console()
    prompt = Prompt()

    def cmd_login(self, options):
        username = options.get('username')
        self.console.print(f'Login username [bold]{username}[/bold]')
        password = self.prompt.ask("Enter password", password=True)
        params = {
            'username': username,
            'password': password,
        }
        r = requests.post(API_LOGIN, json=params)
        from icecream import ic; ic(r.text)
        if r.status == 'ok':
            self.console.print(f'TOKEN: {r.result}')
        else:
            self.console.print(f'[red]Error[/red] {r.message}')


    def cmd_ls(self, options):
        qs = Context.objects.all()
        code = options.get('code')
        if code:
            qs = qs.filter(code__icontains=code)

        count = qs.count()
        table = Table(title=f"Contexts [{count}]")
        table.add_column("Code")
        table.add_column("Name")
        table.add_column("Since")
        table.add_column("Until")
        table.add_column("N. Students", justify="right")
        for context in qs:
            print(context.code, context.name, context.students.count())
            table.add_row(
                context.code,
                context.name,
                context.start_date.isoformat(),
                context.end_date.isoformat(),
                str(context.students.count()),
            )
        self.console.print(table)

    def add_arguments(self, parser):
        self.parser = parser
        self.parser.usage = '[python] ./manage.py contexts [orden]'
        subparsers = parser.add_subparsers(help='opciones', dest='action')

        ls_parser = subparsers.add_parser("ls")
        ls_parser.add_argument('--name', help='Reference name for context')
        ls_parser.add_argument('--code', help='Reference code for context')
        ls_parser.set_defaults(func=self.cmd_ls)

        login_parser = subparsers.add_parser("login")
        login_parser.add_argument('username', help='Username to login')
        login_parser.set_defaults(func=self.cmd_login)

    def handle(self, *args, **options):
        if 'func' in options:
            action = options['func']
            action(options)
        else:
            print(self.parser.description)
            print(f"Use:\n\t{self.parser.usage}")
