from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, and_
from sqlalchemy.orm import sessionmaker, relationship, DeclarativeBase
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import exists
from enum import Enum
import datetime

# Создаем соединение с базой данных PostgreSQL
engine = create_engine('postgresql://test_username:test_password@localhost:54321/test_db')


# Создаем базовый класс для объявления моделей
class Base(DeclarativeBase):
    pass


# Определяем статусы договора
class ContractStatus(Enum):
    DRAFT = "Черновик"
    ACTIVE = "Активен"
    COMPLETED = "Завершен"


# Модель для сущности "Проект"
class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    created_date = Column(Date, default=datetime.datetime.utcnow)
    contracts = relationship("Contract", back_populates="project")


# Модель для сущности "Договор"
class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    created_date = Column(Date, default=datetime.datetime.utcnow)
    signed_date = Column(Date)
    status = Column(String, default=ContractStatus.DRAFT.value)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", back_populates="contracts")


# Создаем таблицы в базе данных
Base.metadata.create_all(engine)

# Создаем сессию для взаимодействия с базой данных
Session = sessionmaker(bind=engine)
session = Session()


def create_contract():
    title = input("Введите название договора: ")
    contract = Contract(title=title)
    session.add(contract)
    session.commit()
    print(f"Договор '{contract.title}' создан в статусе '{contract.status}'")


def confirm_contract():
    contracts = session.query(Contract).filter_by(status=ContractStatus.DRAFT.value).all()
    if not contracts:
        print("Нет доступных договоров для подтверждения.")
        return

    print("Доступные для подтверждения договоры:")
    for idx, contract in enumerate(contracts, start=1):
        print(f"{idx}. {contract.title}")

    choice = int(input("Выберите номер договора для подтверждения: "))
    if 1 <= choice <= len(contracts):
        selected_contract = contracts[choice - 1]
        selected_contract.status = ContractStatus.ACTIVE.value
        selected_contract.signed_date = datetime.datetime.utcnow()
        session.commit()
        print(f"Договор '{selected_contract.title}' подтвержден и активен.")


def complete_contract():
    contracts = session.query(Contract).filter_by(status=ContractStatus.ACTIVE.value).all()
    if not contracts:
        print("Нет активных договоров для завершения.")
        return

    print("Активные договоры для завершения:")
    for idx, contract in enumerate(contracts, start=1):
        print(f"{idx}. {contract.title}")

    choice = int(input("Выберите номер договора для завершения: "))
    if 1 <= choice <= len(contracts):
        selected_contract = contracts[choice - 1]
        selected_contract.status = ContractStatus.COMPLETED.value
        session.commit()
        print(f"Договор '{selected_contract.title}' завершен.")


def create_project():
    title = input("Введите название проекта: ")
    try:
        project = Project(title=title)
        session.add(project)
        session.commit()
        print(f"Проект '{project.title}' создан.")
    except IntegrityError:
        print("SMTH WRONG")
        session.rollback()


def add_contract_to_project():
    # Выберем только те проекты, где нет активного договора или его вообще нет
    projects = session.query(Project).filter(~exists().where(and_(Contract.project_id == Project.id, Contract.status == ContractStatus.ACTIVE.value))).all()

    if not projects:
        print("Нет доступных проектов для добавления договора.")
        return

    print("Доступные проекты:")
    for idx, project in enumerate(projects, start=1):
        print(f"{idx}. {project.title}")

    choice = int(input("Выберите номер проекта для добавления договора: "))
    if 1 <= choice <= len(projects):
        selected_project = projects[choice - 1]

        active_contracts = session.query(Contract).filter_by(status=ContractStatus.ACTIVE.value).filter_by(
            project_id=None).all()
        if not active_contracts:
            print("Нет доступных активных договоров для добавления к проекту.")
            return

        print("Доступные для добавления договоры:")
        for idx, contract in enumerate(active_contracts, start=1):
            print(f"{idx}. {contract.title}")

        contract_choice = int(input("Выберите номер договора для добавления к проекту: "))
        if 1 <= contract_choice <= len(active_contracts):
            selected_contract = active_contracts[contract_choice - 1]
            selected_contract.project = selected_project
            session.commit()
            print(f"Договор '{selected_contract.title}' добавлен к проекту '{selected_project.title}'.")

while True:
    print("\nВыберите действие:")
    print("1. Создать договор")
    print("2. Подтвердить договор")
    print("3. Завершить договор")
    print("4. Создать проект")
    print("5. Добавить договор к проекту")
    print("6. Просмотреть список проектов и договоров")
    print("7. Завершить работу")

    choice = input("Введите номер действия: ")

    if choice == '1':
        create_contract()
    elif choice == '2':
        confirm_contract()
    elif choice == '3':
        complete_contract()
    elif choice == '4':
        if session.query(Contract).count() > 0:
            create_project()
        else:
            print("По условиям надо сначала добавить контракт, а потом проект!\n")
    elif choice == '5':
        add_contract_to_project()
    elif choice == '6':
        projects = session.query(Project).all()
        contracts = session.query(Contract).all()

        print("\nСписок проектов:")
        for idx, project in enumerate(projects, start=1):
            print(f"{idx}. {project.title}")

        print("\nСписок договоров:")
        for idx, contract in enumerate(contracts, start=1):
            print(f"{idx}. {contract.title} ({contract.status})")
    elif choice == '7':
        print("CREATED BY CHAMOMILE (Ilya Romaneyko)")
        break

# Завершение сессии
session.close()
