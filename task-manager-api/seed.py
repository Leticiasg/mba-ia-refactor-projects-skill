"""Script para popular o banco com dados iniciais"""
from datetime import timedelta

from app import app
from models import Category, Task, User, db
from models.database import utcnow

def seed_data():
    with app.app_context():

        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        joao = User()
        joao.name = 'João Silva'
        joao.email = 'joao@email.com'
        joao.set_password('1234')
        joao.role = 'admin'
        db.session.add(joao)

        maria = User()
        maria.name = 'Maria Santos'
        maria.email = 'maria@email.com'
        maria.set_password('abcd')
        maria.role = 'user'
        db.session.add(maria)

        pedro = User()
        pedro.name = 'Pedro Oliveira'
        pedro.email = 'pedro@email.com'
        pedro.set_password('pass')
        pedro.role = 'manager'
        db.session.add(pedro)

        db.session.commit()

        backend = Category()
        backend.name = 'Backend'
        backend.description = 'Tarefas de backend'
        backend.color = '#3498db'
        db.session.add(backend)

        frontend = Category()
        frontend.name = 'Frontend'
        frontend.description = 'Tarefas de frontend'
        frontend.color = '#2ecc71'
        db.session.add(frontend)

        devops = Category()
        devops.name = 'DevOps'
        devops.description = 'Tarefas de infraestrutura'
        devops.color = '#e74c3c'
        db.session.add(devops)

        bug = Category()
        bug.name = 'Bug'
        bug.description = 'Correção de bugs'
        bug.color = '#e67e22'
        db.session.add(bug)

        db.session.commit()

        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': backend.id, 'due_date': utcnow() - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': maria.id, 'category_id': frontend.id, 'due_date': utcnow() + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': pedro.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': bug.id, 'due_date': utcnow() - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'due_date': utcnow() + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': maria.id, 'category_id': backend.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': pedro.id, 'category_id': backend.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': maria.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': pedro.id, 'category_id': devops.id, 'due_date': utcnow() + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
        ]

        for task_data in tasks_data:
            task = Task()
            task.title = task_data['title']
            task.description = task_data['description']
            task.status = task_data['status']
            task.priority = task_data['priority']
            task.user_id = task_data['user_id']
            task.category_id = task_data['category_id']
            if 'due_date' in task_data:
                task.due_date = task_data['due_date']
            if 'tags' in task_data:
                task.tags = task_data['tags']
            db.session.add(task)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")

if __name__ == '__main__':
    seed_data()
