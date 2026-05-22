# Retrospectiva — Sprint 1

**Projeto:** Sistema de Eventos Universitários 
**Formato:** Start / Stop / Continue  
**Data:** Mai/2026

---

## 🟢 Start — O que devemos começar a fazer

- **Escrever testes antes da implementação (TDD):** Durante a Sprint 1, os testes de models e de integração foram criados após o desenvolvimento das features. Adotar TDD desde o início da Sprint 2 ajudará a reduzir retrabalho e aumentar a confiança nas entregas.

- **Definir critérios de aceitação com exemplos concretos antes de iniciar cada issue:** Algumas user stories (ex: listagem de eventos, compra de ingresso) geraram dúvidas durante o desenvolvimento sobre edge cases. Acordar exemplos de entrada/saída antes de codar evita interpretações divergentes.

- **Revisar PRs em dupla antes de fechar a issue:** Ao longo da sprint, alguns bugs só foram percebidos após o merge. Instituir revisão obrigatória por um segundo membro antes do merge aumenta a qualidade e distribui o conhecimento do código.

- **Documentar decisões técnicas relevantes no repositório (ADRs simples):** Escolhas como estrutura dos models, estratégia de autenticação e organização das views ficaram implícitas. Registrar essas decisões no próprio repo facilita o onboarding e evita discussões repetidas.

---

## 🔴 Stop — O que devemos parar de fazer

- **Deixar testes para o final da sprint:** Os testes de models (`Evento`, `Local`, `Categoria`, `Ingresso`, `Compra`) e de integração foram implementados nas últimas issues da sprint, gerando pressão e menor cobertura. Isso precisa mudar.

- **Iniciar issues sem entender completamente os critérios de aceitação:** Em alguns casos (ex: fluxo de compra e redirecionamento pós-login) o time começou a implementar antes de alinhar todos os critérios, causando retrabalho.

- **Trabalhar em silos sem comunicar bloqueios:** Alguns impedimentos (ex: dúvidas sobre o modelo de Compra e status inicial "pendente") ficaram sem comunicação por tempo demais, atrasando outras issues dependentes.

- **Comitar diretamente na branch principal sem PR:** Eventuais commits diretos na `main` durante ajustes rápidos precisam ser eliminados para manter o histórico limpo e o processo de revisão consistente.

---

## 🔵 Continue — O que devemos continuar fazendo

- **Organizar as issues com critérios de aceitação detalhados:** A Sprint 1 teve user stories bem estruturadas com critérios claros (rotas, comportamentos esperados, mensagens de erro). Isso facilitou muito o desenvolvimento e deve ser mantido em todas as sprints.

- **Separar responsabilidades em camadas claras (models, views, templates):** A arquitetura adotada no projeto Django seguiu boas práticas de separação de concerns, tornando os testes unitários de models independentes das views. Manter essa disciplina.

- **Proteger rotas sensíveis com autenticação desde o início:** O controle de acesso foi aplicado consistentemente nas views protegidas (histórico de compras, compra de ingresso), com redirecionamento correto para login. Essa prática deve continuar em todas as novas funcionalidades.

- **Usar o painel administrativo como ferramenta de suporte ao desenvolvimento:** O registro de modelos no Django Admin (`Evento`, `Categoria`, `Local`, `Ingresso`, `Compra`) com filtros e busca se mostrou útil para validar dados durante o desenvolvimento. Continuar mantendo o admin atualizado conforme novos models forem adicionados.