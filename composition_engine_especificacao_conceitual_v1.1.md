# Composition Engine --- Especificação Conceitual e Arquitetural

**Versão:** 1.1\
**Status:** Base conceitual consolidada\
**Finalidade:** fonte de referência para decisões de domínio,
arquitetura, contratos e implementação do sistema de orçamento integrado
ao `composition-engine`.

------------------------------------------------------------------------

## 1. Objetivo

Este documento consolida as definições estabelecidas para o modelo de
domínio e a arquitetura do sistema de orçamento que utiliza o
`composition-engine` como núcleo de cálculo técnico.

Deve ser consultado durante a implementação. Se uma nova decisão
contrariar uma regra aqui definida, ela deve ser tratada como revisão
explícita da arquitetura/modelo, e não como alteração silenciosa no
código.

------------------------------------------------------------------------

## 2. Princípios fundamentais

### 2.1 Fonte oficial versus cenário do usuário

A base oficial SICRO/SINAPI/Django é somente fonte de importação.

O usuário nunca altera diretamente os dados oficiais. Ao importar dados
para um `Project`, são criados ou reutilizados snapshots imutáveis.

Alterações do usuário pertencem exclusivamente ao `Budget` em que foram
feitas e são representadas por `Override`.

### 2.2 Reprodutibilidade

Um orçamento finalizado deve poder ser reproduzido a partir dos dados
persistidos no `Project` e `Budget`.

Por isso:

-   snapshots são persistidos e imutáveis;
-   overrides são persistidos e representam integralmente o estado
    alterado;
-   datas de referência são explícitas;
-   resultados calculados são persistidos na finalização;
-   a proveniência dos dados oficiais é preservada.

### 2.3 Isolamento de cenários

Um `Project` pode possuir vários `Budget`s. Cada Budget é um cenário
independente.

Alterações em um Budget não modificam outro Budget. Snapshots oficiais
podem ser compartilhados.

------------------------------------------------------------------------

# 3. Modelo conceitual

``` text
Project
├── id
├── highway
├── uf
├── year_month
│
├── composition_snapshots[]
├── input_snapshots[]
├── monetary_value_snapshots[]
│
└── budgets[]
    └── Budget
        ├── id
        ├── monetary_base_date
        ├── type_system
        ├── status
        ├── input_cost_overrides[]
        ├── composition_overrides[]
        └── ServicesCollection
            └── ServiceItem
                ├── id
                ├── code
                ├── description
                ├── unit
                ├── reference_base_date
                ├── quantity
                ├── compositions[]
                │   └── CompositionItem
                │       ├── composition_snapshot
                │       └── factor
                ├── unit_cost
                └── total_cost
```

------------------------------------------------------------------------

# 4. Entidades e objetos

## 4.1 Project

Representa o empreendimento/contexto rodoviário.

Atributos principais:

-   `id`
-   `highway`
-   `uf`
-   `year_month`

Responsabilidades:

-   representar o contexto do empreendimento;
-   manter snapshots importados;
-   permitir compartilhamento de snapshots entre Budgets;
-   evitar duplicação de snapshots logicamente idênticos.

O Project não é responsável pelo cálculo dos custos do orçamento.

## 4.2 Budget

Representa um cenário de orçamento dentro de um Project.

Atributos principais:

-   `id`
-   `monetary_base_date`
-   `type_system`
-   `status`
-   `input_cost_overrides`
-   `composition_overrides`
-   `ServicesCollection`

É a principal fronteira de consistência do cálculo.

Responsabilidades:

-   controlar ServiceItems e CompositionItems;
-   controlar overrides;
-   validar o cenário;
-   resolver objetos efetivos;
-   calcular serviços;
-   armazenar resultados;
-   controlar o ciclo de vida;
-   impedir alterações após finalização.

## 4.3 ServicesCollection

Coleção pertencente ao Budget, responsável por agrupar `ServiceItem`s.

Não deve assumir responsabilidades de cálculo que pertençam ao Budget ou
ao engine.

## 4.4 ServiceItem

Unidade orçamentária calculável.

Atributos:

-   `id`
-   `code`
-   `description`
-   `unit`
-   `reference_base_date`
-   `quantity`
-   `compositions[]`
-   `unit_cost`
-   `total_cost`

`reference_base_date` determina qual versão estrutural/histórica da
composição deve ser utilizada.

Diferentes ServiceItems do mesmo Budget podem utilizar diferentes datas
estruturais.

Exemplo:

``` text
Budget.monetary_base_date = 2026-07

ServiceItem A.reference_base_date = 2024-01
ServiceItem B.reference_base_date = 2025-07
ServiceItem C.reference_base_date = 2026-07
```

Todos utilizam valores monetários de `2026-07`.

## 4.5 CompositionItem

Value Object que representa:

``` text
composition + factor
```

Contém referência ao `CompositionSnapshot` e um `factor`.

Não é uma entidade de negócio independente.

O CompositionItem aponta para o snapshot; o Resolver decide se o cálculo
utilizará snapshot ou override.

------------------------------------------------------------------------

# 5. Dados oficiais e snapshots

## 5.1 Composition

Representa a estrutura técnica oficial de uma composição SICRO/SINAPI.

Quando importada para um Project, passa a ser representada por um
`CompositionSnapshot`.

## 5.2 Input

Representa um insumo técnico oficial.

Quando importado para um Project, passa a ser representado por um
`InputSnapshot`.

## 5.3 MonetaryValue

Representa o valor monetário oficial associado a um insumo e a uma
data-base monetária.

Quando importado para um Project, passa a ser representado por um
`MonetaryValueSnapshot`.

## 5.4 Snapshot

É uma fotografia imutável da fonte oficial no momento da importação.

Deve armazenar os dados integrais necessários para reproduzir o cálculo
e preservar a proveniência, incluindo quando disponível:

-   `source_system`
-   `source_code`
-   referência/data-base
-   `imported_at`
-   `source_version`
-   demais metadados necessários para rastreabilidade.

Snapshots pertencem ao domínio de `Project` e podem ser compartilhados
entre Budgets.

------------------------------------------------------------------------

# 6. Deduplicação de snapshots

O Project não deve possuir múltiplos snapshots logicamente idênticos.

A importação deve usar uma operação conceitualmente equivalente a:

``` text
get_or_create
```

Exemplo:

``` text
CompositionSnapshot
source_system = SICRO
source_code = C001
reference_base_date = 2026-07
```

Se já existir no Project, deve ser reutilizado.

A lógica de `get_or_create` deve ser encapsulada no repositório ou
abstração de persistência, não espalhada pela lógica de importação.

## 6.1 Identidade lógica inicial

### CompositionSnapshot

``` text
(source_system, source_code, reference_base_date)
```

### MonetaryValueSnapshot

``` text
(source_system, input_source_code, monetary_base_date)
```

### InputSnapshot

A identidade deve considerar os atributos que determinam sua identidade
na fonte oficial. Se não depender da data-base, o InputSnapshot pode ser
compartilhado entre composições.

------------------------------------------------------------------------

# 7. Datas-base

Existem duas dimensões de data-base.

## 7.1 ServiceItem.reference_base_date

Determina a versão estrutural/histórica da composição.

``` text
ServiceItem
    ↓
reference_base_date
    ↓
CompositionSnapshot
```

Pode variar entre ServiceItems do mesmo Budget.

## 7.2 Budget.monetary_base_date

Determina a única data-base monetária de todo o Budget.

Todos os valores monetários utilizados no Budget devem obedecer a essa
data.

Não deve haver datas monetárias diferentes dentro do mesmo Budget.

## 7.3 Datas inexistentes

A API deve disponibilizar somente datas-base realmente existentes na
fonte oficial.

O Angular não deve apresentar meses inexistentes nem inferir datas.

A mesma regra vale para referências estruturais.

Se a referência estrutural solicitada não existir, deve ser gerada
crítica/erro apropriado.

Se não existir `MonetaryValue` exatamente na
`Budget.monetary_base_date`, não deve ocorrer fallback silencioso para
data anterior. Deve ser gerada crítica/erro de cálculo.

------------------------------------------------------------------------

# 8. Overrides

## 8.1 Conceito

Override total é uma representação integral e independente do objeto
original, pertencente exclusivamente a um Budget, mantendo referência
imutável ao snapshot de origem.

O snapshot nunca é modificado.

Durante o cálculo, o Resolver combina snapshot e override, dando
precedência ao override.

## 8.2 Tipos

-   `CompositionOverride`
-   `InputOverride`
-   `MonetaryValueOverride`

## 8.3 Características

Overrides:

-   pertencem exclusivamente a um Budget;
-   não modificam snapshots;
-   mantêm referência explícita ao snapshot original;
-   representam integralmente o objeto alterado;
-   são persistidos;
-   permitem reprodução do cálculo;
-   podem coexistir.

## 8.4 CompositionOverride

Pode alterar integralmente a composição, incluindo:

-   adicionar inputs;
-   remover inputs;
-   alterar inputs;
-   alterar coeficientes;
-   alterar produtividade;
-   alterar outros atributos relevantes.

A composição oficial permanece intacta.

## 8.5 InputOverride

Permite alterar integralmente um Input no contexto de um Budget.

Exemplo:

``` text
Input M0004
Valor oficial = R$ 20,00

Budget A
InputOverride(M0004)
Valor = R$ 40,00
```

Todas as composições do Budget A que utilizarem M0004 devem considerar
R\$ 40,00.

Não se deve duplicar a alteração em cada composição.

## 8.6 MonetaryValueOverride

Substitui o valor monetário oficial de um Input para a data-base
monetária do Budget, mantendo referência explícita ao valor oficial
substituído.

## 8.7 Unicidade

Deve existir um único override ativo para cada target lógico dentro de
um Budget.

Enquanto o Budget estiver editável:

``` text
criar override
    ↓
editar override
    ↓
atualizar o mesmo override
```

------------------------------------------------------------------------

# 9. Effective Object

Não é necessário persistir um terceiro objeto denominado
`Effective Object`.

Durante o cálculo, o Resolver combina:

``` text
Snapshot + Override
```

e produz um objeto efetivo transitório.

Precedência:

``` text
Budget Override
       ↓
Project Snapshot
       ↓
erro se inexistente
```

------------------------------------------------------------------------

# 10. Resolver

O Resolver é a ponte entre o domínio de orçamento e o
`composition-engine`.

Sua função principal é determinar qual objeto deve ser usado no cálculo.

## 10.1 Composition

``` text
ServiceItem.reference_base_date
        ↓
CompositionSnapshot
        ↓
CompositionOverride?
        ↓
Composition efetiva
```

## 10.2 Input

``` text
Composition efetiva
        ↓
InputSnapshot
        ↓
InputOverride?
        ↓
Input efetivo
```

## 10.3 Valor monetário

``` text
Input efetivo
        ↓
Budget.monetary_base_date
        ↓
MonetaryValueSnapshot
        ↓
MonetaryValueOverride?
        ↓
valor monetário efetivo
```

## 10.4 Responsabilidades

O Resolver deve:

-   localizar snapshots;
-   localizar overrides;
-   aplicar precedência;
-   garantir coerência das referências;
-   detectar ausência de dados;
-   produzir objetos efetivos;
-   fornecer ao cálculo os dados necessários.

O Resolver não deve:

-   calcular custo técnico da composição;
-   depender de HTTP ou Angular;
-   modificar snapshots;
-   alterar a fonte oficial.

------------------------------------------------------------------------

# 11. Composition Engine

O `composition-engine` permanece como núcleo do cálculo técnico das
composições.

Ele permanece desacoplado do domínio de orçamento.

Dependência desejada:

``` text
Project
↓
Snapshots
↓
Budget
↓
ServiceItem
↓
CompositionItem
↓
Resolver
↓
Composition Engine
```

O engine não deve depender de:

-   `Budget`;
-   `Project`;
-   Django;
-   HTTP;
-   Angular;
-   detalhes de persistência do domínio de orçamento.

A camada de orçamento/orquestração depende do engine, e não o contrário.

------------------------------------------------------------------------

# 12. CalculationContext

Pode existir um `CalculationContext` transitório contendo:

``` text
type_system
structure_date
monetary_date
composition
inputs
overrides
```

Onde:

-   `structure_date` = referência estrutural do ServiceItem;
-   `monetary_date` = `Budget.monetary_base_date`.

Não precisa ser persistido.

Funciona como contexto de execução entre domínio, Resolver e engine.

------------------------------------------------------------------------

# 13. Quantity e Factor

## 13.1 ServiceItem.quantity

Durante `DRAFT`:

``` text
quantity >= 0
```

Logo:

-   `< 0` → inválido;
-   `= 0` → permitido durante edição;
-   `> 0` → válido.

Na validação para finalização:

``` text
quantity > 0
```

`quantity = 0` gera crítica impeditiva orientando a informar quantidade
maior que zero ou excluir o ServiceItem.

## 13.2 CompositionItem.factor

Sempre:

``` text
factor > 0
```

Logo:

-   `factor = 0` → inválido imediatamente;
-   `factor < 0` → inválido imediatamente;
-   `factor > 0` → válido.

## 13.3 Composição obrigatória

Um ServiceItem deve possuir pelo menos uma composição para ser
calculável.

------------------------------------------------------------------------

# 14. Custos

`unit_cost` e `total_cost` são resultados de cálculo.

Não são editáveis manualmente.

Devem ser calculados pelo sistema e persistidos na finalização do
Budget.

------------------------------------------------------------------------

# 15. Ciclo de vida do Budget

``` text
DRAFT
  ↓
CALCULATE
  ↓
CALCULATED
  ↓
FINALIZED 🔒
```

## DRAFT

O Budget está em edição.

Podem ocorrer alterações de ServiceItems, CompositionItems, quantidades
e overrides.

`quantity = 0` é permitido.

## CALCULATED

Existe resultado calculado e validado, mas o Budget ainda não está
definitivamente congelado.

Qualquer alteração que afete o cálculo deve invalidar o resultado e
retornar a `DRAFT`.

## FINALIZED

O Budget está congelado.

Não pode ser editado.

Para criar uma variação:

``` text
FINALIZED
    ↓
duplicar/criar novo Budget
    ↓
DRAFT
```

------------------------------------------------------------------------

# 16. Finalização

A finalização deve ser uma operação de domínio, não simples alteração do
status.

Conceitualmente:

``` text
finalize()
```

deve:

1.  validar estrutura;
2.  validar quantidades;
3.  validar fatores;
4.  verificar existência das composições;
5.  resolver snapshots e overrides;
6.  verificar valores monetários;
7.  executar cálculo;
8.  persistir resultados;
9.  congelar o Budget.

Somente então o status pode ser `FINALIZED`.

------------------------------------------------------------------------

# 17. ValidationIssue

Problemas de preenchimento e consistência devem ser representados por
críticas estruturadas.

Estrutura:

``` text
ValidationIssue
├── code
├── severity
├── entity
├── entity_id
└── message
```

Exemplo:

``` text
severity:
CRITICAL

code:
SERVICE_ITEM_ZERO_QUANTITY

entity:
ServiceItem

entity_id:
123

message:
"Informe uma quantidade maior que zero ou remova o ServiceItem."
```

A crítica de quantidade zero é impeditiva na finalização, mas não impede
edição em DRAFT.

------------------------------------------------------------------------

# 18. API e Angular

Fluxo arquitetural:

``` text
Angular
   ↓
API / Routes
   ↓
Application Layer
   ↓
Domain / Budget
   ↓
Resolver
   ↓
Composition Engine
```

O Angular não acessa diretamente estruturas internas do engine.

## 18.1 Importação

A API deve permitir trabalhar com:

-   UF;
-   `type_system`;
-   código(s);
-   data-base estrutural;
-   data-base monetária.

A API retorna os dados necessários para criação e edição do cenário.

## 18.2 Cálculo síncrono

Fluxo inicial:

``` text
Angular
   ↓
envia contexto/orçamento
   ↓
Django
   ↓
Resolver
   ↓
Composition Engine
   ↓
resultado
   ↓
Angular
```

O retorno deve incluir, no mínimo, custo unitário total e informações
necessárias para críticas e resultados.

------------------------------------------------------------------------

# 19. Persistência versus estado transitório

## Persistir

-   Project;
-   Budgets;
-   ServiceItems;
-   CompositionItems;
-   CompositionSnapshots;
-   InputSnapshots;
-   MonetaryValueSnapshots;
-   CompositionOverrides;
-   InputOverrides;
-   MonetaryValueOverrides;
-   `unit_cost`;
-   `total_cost`;
-   metadados de proveniência.

## Transitório

Não é necessário persistir como entidade independente:

-   Effective Object;
-   CalculationContext;
-   estado transitório da execução do cálculo.

------------------------------------------------------------------------

# 20. Fronteiras arquiteturais

Separação desejada:

``` text
API / Django
    ↓
Application
    ↓
Domain
    ↓
Resolver / Orchestration
    ↓
Composition Engine
    ↓
Infrastructure / repositories
```

O núcleo de cálculo permanece independente da interface HTTP.

Regras de domínio não devem ser implementadas diretamente em
controllers/views.

------------------------------------------------------------------------

# 21. Invariantes

1.  Snapshot oficial é imutável.
2.  Override pertence a um único Budget.
3.  Override não altera snapshot.
4.  Override é integral, não simples delta.
5.  CompositionItem aponta para snapshot.
6.  Resolver decide snapshot versus override.
7.  Budget possui uma única `monetary_base_date`.
8.  ServiceItems podem possuir diferentes `reference_base_date`.
9.  Não existe fallback monetário silencioso.
10. `quantity = 0` é permitido em DRAFT.
11. `quantity = 0` impede finalização.
12. `quantity < 0` é inválido.
13. `factor <= 0` é inválido imediatamente.
14. ServiceItem precisa possuir composição.
15. `unit_cost` e `total_cost` não são editáveis manualmente.
16. Budget finalizado é imutável.
17. Alteração de Budget finalizado gera novo cenário.
18. Snapshots são deduplicados dentro do Project.
19. Snapshots preservam proveniência.
20. Engine não depende do domínio de Budget.
21. Domínio de Budget pode depender do engine.
22. API oferece somente referências existentes.
23. Base oficial não recebe alterações do usuário.
24. Overrides são propagados pelo Resolver.
25. Problemas de validação são representados por `ValidationIssue`.

------------------------------------------------------------------------

# 22. Exemplo completo

``` text
Project
└── CompositionSnapshot
    └── C001 / SICRO / 2025-07

Budget A
├── monetary_base_date = 2026-07
├── CompositionOverride(C001)
├── InputOverride(M0004)
└── ServiceItem
    ├── reference_base_date = 2025-07
    └── quantity = 100
```

Resolução:

``` text
ServiceItem
    ↓
reference_base_date = 2025-07
    ↓
CompositionSnapshot C001
    ↓
CompositionOverride(C001) existe
    ↓
Composition efetiva
    ↓
Input M0004
    ↓
InputOverride(M0004) existe
    ↓
Input efetivo
    ↓
Budget.monetary_base_date = 2026-07
    ↓
MonetaryValueSnapshot de 2026-07
    ↓
MonetaryValueOverride?
    ↓
valor monetário efetivo
    ↓
Composition Engine
    ↓
unit_cost
    ↓
ServiceItem.total_cost = quantity × unit_cost
```

Outro Budget pode usar os mesmos snapshots sem possuir os mesmos
overrides.

------------------------------------------------------------------------

# 23. Critério para novas decisões

Toda nova necessidade deve ser avaliada:

1.  pertence ao contexto do empreendimento (`Project`)?
2.  pertence ao cenário (`Budget`)?
3.  é dado oficial importado?
4.  é alteração específica de cenário?
5.  é estado transitório de cálculo?
6.  é responsabilidade do Resolver?
7.  é responsabilidade do Composition Engine?
8.  é responsabilidade da API/Application Layer?
9.  preserva imutabilidade e reprodutibilidade?
10. mantém Budgets independentes?

Se contrariar uma regra existente, deve ser registrada como revisão.

------------------------------------------------------------------------

---

# 24. Contrato formal do Resolver

O Resolver é a fronteira entre o domínio de orçamento e o `composition-engine`.

Sua responsabilidade é **resolver dependências**, e não calcular custos.

Ele transforma referências persistidas em objetos efetivos de cálculo, aplicando snapshots, overrides, datas-base e regras de precedência.

## 24.1 Princípio fundamental

```text
Resolver = "qual objeto deve ser usado?"
Engine   = "qual é o custo desse objeto?"
```

O Resolver deve ser essencialmente read-only durante a resolução.

Ele não:

- modifica Snapshots;
- modifica Overrides;
- modifica Budget;
- cria Snapshots;
- cria Overrides;
- persiste resultados;
- executa cálculo técnico;
- realiza fallback de data;
- conhece HTTP, Django ou Angular.

## 24.2 Estrutura conceitual

```text
Resolver
├── CompositionResolver
├── InputResolver
└── MonetaryValueResolver
```

Pode existir uma fachada de alto nível `Resolver`/`BudgetResolver`, mantendo internamente responsabilidades especializadas.

## 24.3 ResolutionContext

O Resolver utiliza um contexto transitório:

```text
ResolutionContext
├── project
├── budget
├── type_system
├── structure_date
└── monetary_date
```

Regras:

```text
structure_date = ServiceItem.reference_base_date
monetary_date  = Budget.monetary_base_date
```

O `ResolutionContext` não é persistido.

## 24.4 Separação entre ResolutionContext e CalculationContext

`ResolutionContext` responde:

> De onde os dados devem ser obtidos?

`CalculationContext` responde:

> Quais dados efetivos serão enviados ao cálculo?

Fluxo:

```text
ResolutionContext
        ↓
     Resolver
        ↓
CalculationContext
        ↓
Composition Engine
```

O `CalculationContext` existente no engine atualmente contém critérios como UF, data-base, classificação, grupo e `type_system`. Essa estrutura deverá ser adaptada gradualmente para representar o contexto efetivo de cálculo sem introduzir dependência do domínio de Budget no engine.

## 24.5 Contrato público conceitual

```text
resolve_composition(
    context,
    composition_reference
) → ResolvedComposition

resolve_input(
    context,
    input_reference
) → ResolvedInput

resolve_monetary_value(
    context,
    input_reference
) → ResolvedMonetaryValue

resolve_service(
    context,
    service_item
) → ResolvedService
```

Os nomes concretos podem ser adaptados à implementação, mas a semântica deve permanecer.

---

# 25. Resolução de Composition

Fluxo:

```text
ServiceItem.reference_base_date
        ↓
CompositionSnapshot
        ↓
CompositionOverride?
        ↓
Effective Composition
```

Regra:

```text
CompositionOverride > CompositionSnapshot
```

Se o Snapshot não existir na referência estrutural solicitada:

```text
CRITICAL
COMPOSITION_NOT_FOUND
```

Não deve existir fallback para outra data estrutural.

---

# 26. Resolução de Input

A resolução deve ocorrer sobre a **Composition efetiva**, e não sobre a composição oficial original.

Fluxo:

```text
Effective Composition
        ↓
InputSnapshot
        ↓
InputOverride?
        ↓
Effective Input
```

Isso permite que `CompositionOverride`:

- adicione inputs;
- remova inputs;
- altere inputs;
- altere coeficientes;
- altere produtividade.

Um `InputOverride` é aplicado no momento da resolução.

Não deve ser copiado para cada composição.

Exemplo:

```text
Effective Composition
├── M0001 → InputSnapshot
├── M0004 → InputOverride
└── M0010 → InputSnapshot
```

---

# 27. Resolução de MonetaryValue

Fluxo:

```text
Effective Input
        ↓
Budget.monetary_base_date
        ↓
MonetaryValueSnapshot
        ↓
MonetaryValueOverride?
        ↓
Effective MonetaryValue
```

A data monetária é exclusivamente a do Budget.

Regra absoluta:

```text
MonetaryValueSnapshot inexistente
para Budget.monetary_base_date
        ↓
CRITICAL
```

É proibido fallback silencioso para uma data anterior.

---

# 28. Resultado da resolução

A resolução deve permitir representar tanto sucesso quanto problemas de dados.

Conceitualmente:

```text
ResolutionResult
├── value
└── issues[]
```

Exemplos de problemas esperados:

```text
COMPOSITION_NOT_FOUND
INPUT_NOT_FOUND
MONETARY_VALUE_NOT_FOUND
REFERENCE_DATE_NOT_FOUND
OVERRIDE_TARGET_NOT_FOUND
```

Problemas de dados esperados devem ser representados por `ValidationIssue`.

Violações de contrato de programação devem utilizar exceções.

Regra:

```text
dado inválido/inexistente
    → ValidationIssue

contrato de programação quebrado
    → Exception
```

---

# 29. ResolvedService

`resolve_service` é uma operação composta de alto nível.

Saída conceitual:

```text
ResolvedService
├── service_id
├── code
├── description
├── unit
├── quantity
├── structure_date
├── monetary_date
├── compositions[]
│   └── ResolvedComposition
└── issues[]
```

`ResolvedService` não deve possuir `unit_cost` ou `total_cost`.

Esses valores pertencem ao resultado do cálculo.

Fluxo:

```text
ResolvedService
        ↓
CalculationContext
        ↓
Composition Engine
        ↓
CalculationResult
```

---

# 30. Determinismo e imutabilidade do Resolver

Para um mesmo estado persistido:

```text
Project + Budget + ServiceItem
```

a resolução deve ser determinística.

Conceitualmente:

```text
R(Project, Budget, ServiceItem)
=
mesmo resultado
```

desde que os dados persistidos não tenham mudado.

A operação de resolução não deve produzir efeitos colaterais.

---

# 31. Mapeamento do contrato para o composition-engine atual

O contrato novo deve ser incorporado ao engine existente, e não criar um segundo mecanismo paralelo.

## 31.1 CompositionResolver atual

O `CompositionResolver` existente está em:

```text
app/services/composition_resolver.py
```

Atualmente ele resolve a árvore estrutural de uma composição, oferecendo:

```text
resolve_tree()
resolve_tree_optimized()
```

e utiliza:

```text
CompositionRepository
OptimizedCompositionRepository
```

para carregar a estrutura.

Sua responsabilidade atual é:

```text
código da composição
        ↓
CompositionTree
```

incluindo expansão recursiva de referências `AX` e `TF`.

### Decisão arquitetural

O `CompositionResolver` atual **não deve ser simplesmente renomeado para o novo Resolver**.

São responsabilidades diferentes:

```text
CompositionResolver atual
    =
resolver estrutural do engine

Novo Budget Resolver
    =
resolver de contexto, snapshots e overrides
```

O primeiro continua sendo parte interna do `composition-engine`.

O segundo será a ponte entre o domínio de orçamento e o engine.

## 31.2 Relação entre os dois

A arquitetura desejada passa a ser:

```text
Budget Resolver
      │
      │ resolve CompositionSnapshot/Override
      ▼
Effective Composition
      │
      ▼
CompositionResolver
      │
      │ constrói árvore AX/TF
      ▼
CompositionTree
      │
      ▼
CompositionCalculator
```

Assim preservamos a responsabilidade atual do `CompositionResolver`.

---

# 32. Mapeamento para CalculationExecution

O `CalculationExecution` atual está em:

```text
app/domain/calculation_execution.py
```

Sua responsabilidade é armazenar resultados transitórios de uma execução de cálculo:

```text
CompositionNode
        ↓
CompositionCalculationResult
```

Ele é utilizado pelo `CompositionCalculator` durante o percurso pós-ordem da árvore.

Isso está conceitualmente correto.

### Decisão

`CalculationExecution` deve permanecer **dentro do mecanismo de cálculo**.

Ele não deve ser transformado em armazenamento de:

- Snapshots;
- Overrides;
- Project;
- Budget;
- ResolutionContext.

A separação deve permanecer:

```text
Resolver
    ↓
dados efetivos
    ↓
CompositionResolver
    ↓
CompositionTree
    ↓
CompositionCalculator
    ↓
CalculationExecution
```

`CalculationExecution` representa somente o estado transitório da execução do cálculo.

---

# 33. Mapeamento para MonetaryValueResolver atual

O engine já possui:

```text
app/services/monetary_value_resolver.py
```

O `MonetaryValueResolver` atual recebe:

```text
code
CalculationContext
```

e critérios opcionais como:

```text
source_file_uf
source_file_data_base
classification
group
type_system
```

Atualmente ele filtra os valores monetários e exige que exatamente um valor seja compatível.

### Compatibilidade com o novo modelo

A responsabilidade atual de selecionar um `MonetaryValue` é aproveitável, mas a autoridade sobre a data monetária precisa mudar no contexto do Budget.

No novo fluxo:

```text
Budget.monetary_base_date
        ↓
Budget Resolver
        ↓
MonetaryValueSnapshot / Override
        ↓
Composition Engine
```

O `MonetaryValueResolver` do engine deve continuar responsável por seleção/cálculo técnico quando isso fizer parte do mecanismo interno do engine.

Ele não deve passar a conhecer `Budget` ou `Project`.

### Regra

Não criar dependência:

```text
MonetaryValueResolver
        X
Budget
Project
Django
```

---

# 34. Mapeamento para CalculationContext atual

O engine já possui:

```text
app/domain/calculation_context.py
```

Atualmente contém:

```text
source_file_uf
source_file_data_base
classification
group
type_system
```

Esse objeto já cumpre parcialmente o papel de contexto transitório do engine.

Entretanto, o novo domínio introduz uma distinção explícita:

```text
structure_date
monetary_date
```

Essa distinção deve ser preservada.

### Decisão

Não misturar silenciosamente:

```text
reference_base_date
```

com:

```text
monetary_base_date
```

O novo domínio deverá fornecer ao engine um contexto coerente com ambas as dimensões, sem fazer o engine depender das entidades `Project` ou `Budget`.

---

# 35. Mapeamento para repositories

Os repositories atuais incluem:

```text
app/repositories/composition_repository.py
app/repositories/monetary_value_repository.py
app/repositories/optimized_composition_repository.py
```

O `CompositionRepository` atual utiliza `CompositionApiClient` e possui cache em memória e carregamento em lote.

Esse mecanismo pode continuar sendo utilizado pelo engine.

O novo domínio de orçamento introduzirá novos contratos para:

```text
CompositionSnapshotRepository
InputSnapshotRepository
MonetaryValueSnapshotRepository

CompositionOverrideRepository
InputOverrideRepository
MonetaryValueOverrideRepository
```

Esses repositories não devem substituir automaticamente os repositories internos já existentes.

A separação é:

```text
Repositories do engine
    ↓
dados necessários ao cálculo técnico atual

Repositories do domínio de orçamento
    ↓
Snapshots e Overrides persistidos do Project/Budget
```

Uma camada de adaptação pode conectar os dois mundos.

---

# 36. Mapeamento para CompositionRoot atual

O `CompositionRoot` atual está em:

```text
app/composition_root.py
```

Ele já funciona como ponto central de composição das dependências.

Atualmente o grafo é aproximadamente:

```text
CompositionApiClient
        │
        ├── CompositionRepository
        │
        └── OptimizedCompositionRepository
                    │
                    ▼
           CompositionResolver
                    │
                    ▼
           CompositionExplosion
```

Essa responsabilidade deve ser preservada.

### Evolução desejada

O novo grafo, quando o domínio de orçamento for incorporado, será:

```text
Django / Application
        │
        ▼
Budget Resolver
        │
        ├── Snapshot Repositories
        ├── Override Repositories
        │
        ▼
Effective Composition / CalculationContext
        │
        ▼
Composition Engine
        │
        ├── CompositionResolver
        ├── CompositionCalculator
        ├── MonetaryValueResolver
        ├── EquipmentCalculator
        ├── LaborCalculator
        ├── MaterialCalculator
        └── ...
```

O `CompositionRoot` continua sendo o lugar apropriado para montar o grafo concreto.

Não devem surgir novos composition roots implícitos em controllers, views ou serviços de aplicação.

---

# 37. Arquitetura consolidada após o mapeamento

```text
                         API / Django
                              │
                              ▼
                       Application Layer
                              │
                              ▼
                    Project / Budget Domain
                              │
                              ▼
                       Budget Resolver
                              │
             ┌────────────────┼─────────────────┐
             │                │                 │
             ▼                ▼                 ▼
       Composition          Input          MonetaryValue
        Resolver            Resolver          Resolver
             │                │                 │
             └────────────────┼─────────────────┘
                              ▼
                    Effective Objects
                              │
                              ▼
                    CalculationContext
                              │
                              ▼
                    Composition Engine
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
       CompositionResolver         CompositionCalculator
                 │                         │
                 ▼                         ▼
        CompositionTree            CalculationExecution
                                           │
                                           ▼
                                  CalculationResult
```

---

# 38. O que NÃO devemos fazer na implementação

Não devemos:

### 1. Transformar o CompositionResolver atual em um resolver de Budget

São responsabilidades diferentes.

### 2. Colocar Budget dentro do Composition Engine

Isso inverteria a dependência arquitetural.

### 3. Colocar Snapshots dentro de CalculationExecution

Snapshots são persistentes e pertencem ao Project.

### 4. Colocar Overrides dentro de CalculationExecution

Overrides pertencem ao Budget.

### 5. Fazer MonetaryValueResolver conhecer Budget

A data monetária deve chegar ao engine através do contexto efetivo.

### 6. Fazer repositories do engine conhecer Django

A infraestrutura pode ser substituída/adaptada.

### 7. Criar Effective Objects persistentes

Eles devem permanecer transitórios.

### 8. Fazer fallback automático de data-base

Ausência de referência válida deve gerar `ValidationIssue`.

### 9. Persistir custo calculado durante cada passo intermediário

O estado transitório pertence à execução. O resultado final é persistido conforme o ciclo de vida do Budget.

---

# 39. Estratégia de implementação

A implementação deve ocorrer em camadas:

```text
Fase 1
Contratos e tipos do domínio
        ↓
Fase 2
Repositories/ports de Snapshot e Override
        ↓
Fase 3
Budget Resolver
        ↓
Fase 4
Adaptação para CalculationContext
        ↓
Fase 5
Integração com CompositionResolver existente
        ↓
Fase 6
Integração com CompositionCalculator
        ↓
Fase 7
Budget.calculate()
        ↓
Fase 8
ValidationIssue
        ↓
Fase 9
finalize()
        ↓
Fase 10
API/Django/Angular
```

Cada fase deve preservar a suíte existente de testes.

---

# 40. Testes obrigatórios do Resolver

## Composition

- Snapshot encontrado;
- Snapshot inexistente;
- Override encontrado;
- Override inexistente;
- referência estrutural correta;
- referência estrutural inexistente;
- Snapshot permanece inalterado.

## Input

- Input encontrado;
- Input inexistente;
- InputOverride aplicado;
- InputOverride propagado;
- CompositionOverride adicionando Input;
- CompositionOverride removendo Input.

## MonetaryValue

- valor encontrado exatamente na data do Budget;
- valor inexistente;
- ausência sem fallback;
- MonetaryValueOverride aplicado;
- data monetária proveniente exclusivamente do Budget.

## Isolamento

```text
Budget A → override M0004 = 40
Budget B → nenhum override
```

Resultado:

```text
A → 40
B → valor oficial
```

## Imutabilidade

A resolução não pode modificar:

```text
Project
Snapshot
Budget
Override
```

## Determinismo

A mesma entrada deve produzir resolução equivalente em execuções sucessivas.

## Integração com engine

Deve ser demonstrado que:

```text
Budget Resolver
    ↓
Effective Composition
    ↓
CompositionResolver
    ↓
CompositionTree
    ↓
CompositionCalculator
    ↓
CalculationExecution
```

preserva o comportamento já existente do engine.

---

# 41. Próximo passo de implementação

Após este contrato, não devemos começar criando endpoints.

A primeira implementação deve ser feita no núcleo:

```text
domain
    ↓
ports/repositories
    ↓
resolver
    ↓
adaptação ao engine
```

A primeira entrega técnica deve ser pequena e verificável:

```text
ResolutionContext
ResolvedComposition
ResolvedInput
ResolvedMonetaryValue
ResolutionResult
interfaces dos repositories
Budget Resolver
```

seguida de testes unitários.

Somente depois devemos conectar o Resolver ao `CompositionRoot` e ao fluxo completo do engine.

---

# 42. Histórico de decisões

| Versão | Decisão |
|---|---|
| 1.1 | Contrato formal do Resolver consolidado |
| 1.1 | Resolver definido como mecanismo de resolução, não cálculo |
| 1.1 | ResolutionContext separado de CalculationContext |
| 1.1 | CompositionResolver atual preservado como resolver estrutural do engine |
| 1.1 | Budget Resolver definido como ponte entre domínio de orçamento e engine |
| 1.1 | CalculationExecution permanece exclusivamente transitório da execução de cálculo |
| 1.1 | MonetaryValueResolver atual preservado sem dependência de Budget |
| 1.1 | Snapshots/Overrides terão repositories próprios no domínio de orçamento |
| 1.1 | CompositionRoot permanece ponto central de composição das dependências |
| 1.1 | Resolver definido como operação read-only e determinística |
| 1.1 | Effective Objects permanecem transitórios |
| 1.1 | Fallback de data-base explicitamente proibido |
| 1.1 | Integração deve preservar a suíte de testes existente |

---

# 43. Status

Esta versão 1.1 incorpora o contrato formal do Resolver e seu mapeamento para a estrutura atual do `composition-engine`.

O contrato é considerado suficientemente definido para iniciar a implementação incremental.

**Fonte de verdade conceitual:** este documento.  
**Fonte de verdade comportamental:** este documento + testes automatizados.  
**Implementação:** deve obedecer às duas fontes acima.
