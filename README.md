# Budget API — Contract v1.0

Contrato inicial do `POST /budgets/calculate`.

## Decisões

- O endpoint produz o cálculo oficial do orçamento.
- O Angular pode calcular previews localmente, mas o resultado oficial é recalculado pelo backend.
- `reference_base_date` pertence ao `CompositionItemInput`.
- `monetary_base_date` pertence ao Budget.
- `unit_cost` e `total_cost` são somente saída.
- O endpoint não persiste nem finaliza o Budget.
- Snapshots e overrides são resolvidos pelo backend.
- O `composition-engine` permanece responsável pelo cálculo técnico das composições.
- O `budget-api` consolida o cálculo do orçamento.

## Estado

Os schemas de Override são deliberadamente preliminares. O próximo passo é fechar a estrutura integral desses três tipos antes da implementação do Flask.
