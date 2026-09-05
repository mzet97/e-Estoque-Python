# 08 — EVENT MODEL

RabbitMQ **publisher only** (paridade: o .NET não possui consumers/outbox/workers).

| Evento | Aggregate | Trigger | Exchange (topic, durable) | Routing key | Payload (camelCase) |
| --- | --- | --- | --- | --- | --- |
| CategoryCreated | Category | POST ok | `category-service` | `category-created` | `{id,name,description,shortDescription,occurredOn}` |
| CategoryUpdated | Category | PUT ok | `category-service` | `category-updated` | idem |
| CompanyCreated/Updated | Company | POST/PUT | `company-service` | `company-created`/`company-updated` | `{id,name,docId,email,description,phoneNumber,companyAddress{...},occurredOn}` |
| CustomerCreated/Updated | Customer | POST/PUT | `customer-service` | `customer-created`/`customer-updated` | idem (customerAddress) |
| InventoryCreated/Updated | Inventory | POST/PUT | `inventory-service` | `inventory-created`/`inventory-updated` | `{id,quantity,dateOrder,idProduct,occurredOn}` |
| ProductCreated | Product | POST ok | `product-service` | `product-created` | `{id,name,description,shortDescription,price,weight,height,length,idCategory,idCompany,occurredOn}` (sem image) |
| ProductUpdated | Product | PUT ok | `product-service` | `product-updated` | idem (image descartada) |
| SaleCreated/Updated | Sale | POST/PUT | `sale-service` | `sale-created`/`sale-updated` | `{id,quantity,totalPrice,totalTax,saleType,paymentType,deliveryDate,saleDate,paymentDate,idCustomer,products[],occurredOn}` |
| TaxCreated/Updated | Tax | POST/PUT | `tax-service` | `tax-created`/`tax-updated` | `{id,name,description,percentage,idCategory,occurredOn}` |
| NotificationError | — | falha handler | `noticiation-service` (typo .NET) | `notification-error` | `{eventName,description,occurredOn}` |
| ErrorNotification | — | login inválido | `noticiation-service` | `error-notification` | `{message,stackTrace}` |
| LoginUserNotification | — | login ok | `noticiation-service` | `login-user-notification` | `{username}` |

Serialização: JSON UTF-8, camelCase, null omitido (`WhenWritingNull`), `Decimal` como string/number
compatível (paridade `JsonSerializerDefaults.Web`: number).

Semântica: publish **após** persistência, fire-and-forget (sem confirm) — igual ao .NET
(`BasicPublish` sem publisher confirms). Falha de broker não derruba a request (log de erro) — melhoria
SRE sobre o .NET, que lança exceção síncrona (NFR-REL-001, ADR-009).

Outbox: **não implementado por opção** — o sistema original publica direto e não possui consumers;
adicionar outbox mudaria o comportamento observável sem demanda real. Requisito do prompt atendido como
decisão documentada (ADR-010); a arquitetura (porta `MessageBus` + evento de integração) permite evoluir
para outbox sem tocar nos handlers.

Idempotência/consumers/DLQ: n/a (não existem consumidores no sistema original).
