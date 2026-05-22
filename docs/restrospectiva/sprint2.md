# Retrospectiva — Sprint 2

**Projeto:** Sistema de Venda de Ingressos  
**Formato:** Start / Stop / Continue  
**Data:** Mai/2025

---

## 🟢 Start — O que devemos começar a fazer

- **Monitorar filas Celery e Redis em ambiente de desenvolvimento:** Durante a Sprint 2, problemas com tasks assíncronas (`send_confirmation_email`) às vezes eram silenciosos — a task falhava sem feedback visível. Adicionar logs estruturados e monitoramento básico (ex: Flower) desde o início da próxima sprint.

- **Criar testes de integração para os endpoints protegidos por perfil (organizador vs comprador):** As regras de autorização ficaram mais complexas nesta sprint (cancelamento de compra, edição/exclusão de evento apenas pelo organizador dono). Testes cobrindo os casos de 403 precisam ser sistemáticos, não opcionais.

- **Estabelecer um padrão de mensagens de commit semântico (Conventional Commits):** Com a pipeline CI/CD configurada via GitHub Actions e análise SonarCloud ativa, padronizar commits (`feat:`, `fix:`, `test:`, `chore:`) facilitará rastreabilidade e geração de changelogs futuros.

- **Fazer sessões curtas de sync técnico ao introduzir novas dependências de infraestrutura:** A adição de Celery, Redis e Docker gerou dúvidas no time sobre configuração e ordem de subida dos serviços. Um alinhamento rápido de 15 minutos ao iniciar essas issues teria poupado tempo.

---

## 🔴 Stop — O que devemos parar de fazer

- **Hardcodar configurações sensíveis no código:** Apesar de o critério de aceitação do e-mail exigir configuração via `settings.py`, houve tentações de colocar valores direto no código durante testes locais. Qualquer configuração de ambiente deve sempre viver em variáveis de ambiente, nunca commitada.

- **Adiar a configuração do ambiente Docker para o final da sprint:** O `Dockerfile` e o `docker-compose.yml` foram entregues próximos ao fim da sprint, o que dificultou testar o ambiente completo (Django + Celery + Redis) de forma integrada antes. Docker deve ser configurado nas primeiras issues da sprint.

- **Ignorar o Quality Gate do SonarCloud durante o desenvolvimento:** Durante a sprint, alguns PRs foram abertos com issues apontadas pelo Sonar sem tratamento, contando com correção posterior. Com o Quality Gate configurado como obrigatório para merge, esse comportamento bloqueia o fluxo — a correção deve ocorrer antes de abrir o PR.

- **Reutilizar lógica de negócio diretamente nas views sem extrair para serviços/helpers:** A lógica de cancelamento de compra (restaurar estoque, validar status, verificar ownership) ficou concentrada na view. Isso dificulta testes unitários e reuso. Extrair para funções auxiliares ou uma camada de serviço.

---

## 🔵 Continue — O que devemos continuar fazendo

- **Usar UUIDs para identificadores expostos publicamente:** A decisão de usar UUID como payload do QR Code (ao invés de IDs sequenciais) foi acertada — evita enumeração e garante unicidade por design. Aplicar o mesmo padrão em outros recursos expostos via URL quando fizer sentido.

- **Escrever testes com mocks para integrações externas:** O uso de mock para o envio de e-mail via Celery foi bem executado — o teste valida o comportamento sem depender de SMTP real. Manter essa abordagem para qualquer integração externa (APIs, filas, storage).

- **Manter o README atualizado como documentação viva do projeto:** As instruções de build e execução via Docker adicionadas nesta sprint tornaram o onboarding muito mais simples. Qualquer nova dependência ou passo de configuração deve ser imediatamente documentado no README.

- **Garantir que regras de autorização sejam implementadas e testadas explicitamente:** O controle de acesso por perfil (organizador vs comprador vs visitante) foi tratado com cuidado nesta sprint — retornos 403 para acessos não autorizados, proteção de recursos por ownership. Essa disciplina de segurança deve ser padrão em todas as novas rotas.

- **Manter a pipeline CI/CD como portão de qualidade obrigatório:** A configuração do GitHub Actions com etapas de install → build → test → SonarCloud garantiu rastreabilidade e impediu merges com falhas. Com o Quality Gate verde e badge atualizado no README, o time tem visibilidade contínua da saúde do projeto.