# Decisões do contrato — POST /budgets/calculate

1. Cálculo oficial e autoritativo no `budget-api`.
2. Angular realiza apenas pré-visualizações locais.
3. O backend recalcula e valida o resultado oficial.
4. `reference_base_date` fica em `CompositionItemInput`.
5. `monetary_base_date` fica no Budget.
6. Resultados calculados não são aceitos como entrada.
7. O endpoint calcula, mas não persiste e não finaliza.
8. `ValidationIssue` representa problemas de dados do orçamento.
9. `400` representa erro estrutural do contrato HTTP.
10. `calculation_id` identifica a execução do cálculo e é distinto de `budget_id`.
11. Overrides ainda precisam de fechamento detalhado antes da implementação.
