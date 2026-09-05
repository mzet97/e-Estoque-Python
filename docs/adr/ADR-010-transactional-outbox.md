# ADR-010 — Sem Transactional Outbox (por paridade)

**Status:** aceito (reavaliar quando surgirem consumers). O .NET publica eventos direto ao RabbitMQ
após `SaveChanges`, sem outbox, sem consumers. Introduzir outbox criaria tabela+worker novos,
mudando o comportamento observável sem demanda real — viola "não overengineer" e precedência §2.
A porta `MessageBus` centraliza o publish; migrar para outbox depois não exige tocar nos handlers.
