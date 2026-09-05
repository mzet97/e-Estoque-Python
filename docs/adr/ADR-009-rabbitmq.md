# ADR-009 — RabbitMQ publisher (aio-pika)

**Status:** aceito. Somente publisher (paridade). `robust_connection` com reconexão; `ExchangeDeclare`
topic durable por serviço (`category-service`, `company-service`, `customer-service`, `inventory-service`,
`product-service`, `sale-service`, `tax-service`, `noticiation-service`). JSON camelCase, null omitido.
Publish após commit, best-effort (falha → log; request não falha — NFR-REL-001). Sem consumers/queues/
DLQ no sistema original; não inventados.
