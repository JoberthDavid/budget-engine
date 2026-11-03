# Budget API

API Django REST Framework para cálculo oficial de orçamentos de engenharia.

## Contrato

- `POST /budgets/calculate` recalcula o orçamento e retorna `budget`, `issues` e `calculation_id`.
- `GET /health` retorna o estado do serviço.
- O endpoint de cálculo não persiste nem finaliza o orçamento.
- O `composition-engine` calcula as composições; esta API consolida o resultado.
- `400` representa erro estrutural da requisição. Problemas do cálculo são retornados em `issues`.

O contrato OpenAPI publicado está em [`openapi.yaml`](openapi.yaml) e deve acompanhar as alterações no payload implementado.

## Configuração

Instale as dependências com `python3 -m pip install -r requirements.txt`. Configure:

- `COMPOSITION_ENGINE_BASE_URL`
- `COMPOSITION_ENGINE_API_KEY`
- opcionalmente `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` e `DJANGO_ALLOWED_HOSTS`

## Execução

Inicie localmente com `python3 manage.py runserver 0.0.0.0:8000`. Para produção, sirva `config.wsgi:application` com um servidor WSGI ou `config.asgi:application` com um servidor ASGI.

## Decisões

- O Angular pode calcular previews, mas o resultado oficial é recalculado pelo backend.
- `reference_base_date` pertence a cada item de composição; `monetary_base_date` pertence ao Budget.
- `unit_cost` e `total_cost` são somente saída.
- Snapshots e overrides são resolvidos pelo backend; a estrutura integral dos overrides ainda precisa ser fechada.
