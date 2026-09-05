# ADR-002 — FastAPI (somente camada HTTP)

**Status:** aceito. FastAPI + Pydantic v2 na boundary. Routers finos: interpretam HTTP, validam
request, chamam handlers de aplicação, mapeiam resposta. Sem SQL, regra de negócio, cálculo de
imposto, alteração de estoque ou publish RabbitMQ nos routers. OpenAPI nativo substitui Swashbuckle
(diferença de UI documentada).
