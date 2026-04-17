# 🎓 Plataforma de Gestão de Eventos Universitários

Sistema web para gerenciamento de eventos acadêmicos, permitindo criação, inscrição e acompanhamento de participação.


## ⚙️ Tecnologias Utilizadas
| Categoria | Tecnologia |
| :--- | :--- |
| **Backend** | Django |
| **Frontend** | Django + Bootstrap |
| **Banco de Dados** |SQLite (Desenvolvimento) / PostgreSQL (Produção)|
| **Controle de Versão** | Git + GitHub |


## 🚀 Como rodar o projeto

**Clonar repositório:** 
```bash
git clone https://github.com/sounicolaslima/eventos-universitarios.git
````
**Entrar na pasta do projeto**
```bash
cd eventos-universitarios
````
**migração do banco (Django)**
```bash
python manage.py migrate
````
**Criar um ambiente virtual Python**
```bash
python -m venv venv
````
**Ativar ambiente virtual**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
````
**Instalar as dependências do projeto**
```bash
pip install -r requirements.txt
````
**Inicia o servidor local do Django**
```bash
python manage.py runserver
````


## 📊 Estrutura
* /src → código fonte
* /tests → testes
* /docs → documentação


## 📌 Gerenciamento do Projeto
**Board do Sprint 1:**
https://github.com/users/sounicolaslima/projects/2/views/1

**Board do Sprint 2:**
https://github.com/users/sounicolaslima/projects/2/views/2

**Board do Sprint 3:**
https://github.com/users/sounicolaslima/projects/2/views/3

## 👥 Integrantes e Responsabilidades
* Laura Costa Sarto Barboza 
  → Testes e Qualidade  
  → Criação de testes unitários  
  → Validação das funcionalidades implementadas  
  → Apoio na documentação

* Nadson Souza Matos  
  → Desenvolvimento Backend  
  → Implementação das regras de negócio (views, lógica)  
  → Integração entre frontend e backend
  
* Nícolas Mariano Lima 
  → Configuração do projeto e ambiente (Django, estrutura inicial)  
  → Modelagem do banco de dados (models)  
  → Integração com banco (ORM, migrations)

*  Rafaella Maciel Pereira Leite 
  → Desenvolvimento de Frontend  
  → Criação de templates (HTML + Bootstrap)  
  → Experiência do usuário (interfaces e navegação)


