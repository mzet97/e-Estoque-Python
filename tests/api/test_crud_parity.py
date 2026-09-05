"""Paridade de CRUD nas rotas REST (status codes, envelopes e semântica .NET)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from httpx import AsyncClient

COMPANY = {
    "name": "Acme Ltda",
    "docId": "12.345.678/0001-90",
    "email": "contato@acme.com.br",
    "description": "Indústria de alimentos",
    "phoneNumber": "+55 11 4002-8922",
    "companyAddress": {
        "street": "Rua das Flores",
        "number": "123",
        "complement": "Sala 2",
        "neighborhood": "Centro",
        "district": "Distrito Central",
        "city": "São Paulo",
        "country": "Brasil",
        "zipCode": "01310-000",
        "latitude": "-23.5505",
        "longitude": "-46.6333",
    },
}

CATEGORY = {
    "name": "Bebidas",
    "description": "Refrigerantes e sucos",
    "shortDescription": "Geladas",
}


async def _create_company(client: AsyncClient) -> dict[str, object]:
    response = await client.post("/api/Companies", json=COMPANY)
    assert response.status_code == 200
    return response.json()


async def test_category_post_returns_201_with_location(client: AsyncClient) -> None:
    response = await client.post("/api/Categories", json=CATEGORY)
    assert response.status_code == 201  # único POST com 201 (CreatedAtAction .NET)
    assert response.headers["location"] is not None
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Bebidas"
    assert body["data"]["shortDescription"] == "Geladas"


async def test_category_get_search_envelope(client: AsyncClient) -> None:
    await client.post("/api/Categories", json=CATEGORY)
    response = await client.get("/api/Categories", params={"pageIndex": 1, "pageSize": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    paged = body["pagedResult"]
    assert paged["currentPage"] == 1 and paged["rowCount"] == 1
    assert paged["firstRowOnPage"] == 1 and paged["lastRowOnPage"] == 1


async def test_category_get_by_id_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/Categories/{uuid4()}")
    assert response.status_code == 404
    assert "error" in response.json()


async def test_category_invalid_post_returns_400_with_joined_message(client: AsyncClient) -> None:
    response = await client.post(
        "/api/Categories", json={"name": "", "description": "doc", "shortDescription": "ok"}
    )
    assert response.status_code == 400
    error = response.json()["error"]
    assert "The Name needs to be provided" in error
    assert "," in error  # mensagens unidas por vírgula


async def test_category_delete_returns_200_empty_object(client: AsyncClient) -> None:
    created = (await client.post("/api/Categories", json=CATEGORY)).json()
    category_id = created["data"]["id"]
    response = await client.delete(f"/api/Categories/{category_id}")
    assert response.status_code == 200
    assert response.json() == {}  # paridade: CustomResponse(true, Unit)
    missing = await client.get(f"/api/Categories/{category_id}")
    assert missing.status_code == 404


async def test_company_crud_roundtrip(client: AsyncClient) -> None:
    body = await _create_company(client)
    company_id = body["data"]["id"]
    assert body["data"]["companyAddress"]["country"] == "Brasil"

    fetched = await client.get(f"/api/Companies/{company_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["docId"] == "12.345.678/0001-90"

    updated_payload = {**COMPANY, "name": "Acme Foods"}
    updated = await client.put(f"/api/Companies/{company_id}", json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Acme Foods"

    deleted = await client.delete(f"/api/Companies/{company_id}")
    assert deleted.status_code == 200 and deleted.json() == {}


async def test_product_requires_existing_category_404(client: AsyncClient) -> None:
    payload = {
        "name": "Coca-Cola 2L",
        "description": "Refrigerante garrafa 2L",
        "shortDescription": "Coca 2L",
        "price": 9.99,
        "weight": 2.1,
        "height": 32,
        "length": 11,
        "image": "https://example.com/coca.png",
        "idCategory": str(uuid4()),
        "idCompany": str(uuid4()),
    }
    response = await client.post("/api/Products", json=payload)
    assert response.status_code == 404  # NotFound("Company not found")


async def test_product_full_flow(client: AsyncClient) -> None:
    company = (await client.post("/api/Companies", json=COMPANY)).json()["data"]
    category = (await client.post("/api/Categories", json=CATEGORY)).json()["data"]
    payload = {
        "name": "Coca-Cola 2L",
        "description": "Refrigerante garrafa 2 litros",
        "shortDescription": "Coca 2L",
        "price": 9.99,
        "weight": 2.1,
        "height": 32,
        "length": 11,
        "image": "https://example.com/coca.png",
        "idCategory": category["id"],
        "idCompany": company["id"],
    }
    created = await client.post("/api/Products", json=payload)
    assert created.status_code == 200  # POST de Product → 200 (não 201)
    product = created.json()["data"]
    assert product["price"] == 9.99  # decimal serializado como número
    assert product["category"]["name"] == "Bebidas"
    assert product["company"]["name"] == "Acme Ltda"

    listing = await client.get("/api/Products")
    assert listing.status_code == 200
    assert listing.json()["data"][0]["category"]["name"] == "Bebidas"


async def test_inventory_create_requires_product(client: AsyncClient) -> None:
    response = await client.post(
        "/api/Inventories",
        json={"quantity": 10, "dateOrder": "2026-09-04T12:00:00", "idProduct": str(uuid4())},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "Product not found"


async def test_inventory_valid_flow_keeps_date_order_string(client: AsyncClient) -> None:
    company = (await client.post("/api/Companies", json=COMPANY)).json()["data"]
    category = (await client.post("/api/Categories", json=CATEGORY)).json()["data"]
    product = (
        await client.post(
            "/api/Products",
            json={
                "name": "Guaraná 350ml",
                "description": "Refrigerante lata 350ml",
                "shortDescription": "Guaraná lata",
                "price": 4.5,
                "weight": 0.35,
                "height": 12,
                "length": 6,
                "image": "https://example.com/g.png",
                "idCategory": category["id"],
                "idCompany": company["id"],
            },
        )
    ).json()["data"]

    response = await client.post(
        "/api/Inventories",
        json={"quantity": 10, "dateOrder": "2026-09-04T12:00:00", "idProduct": product["id"]},
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["quantity"] == 10
    assert body["dateOrder"] == "2026-09-04T12:00:00"  # paridade varchar(80) (A-01)
    assert body["product"]["id"] == product["id"]


async def test_sale_flow_and_soft_delete(client: AsyncClient) -> None:
    company = (await client.post("/api/Companies", json=COMPANY)).json()["data"]
    category = (await client.post("/api/Categories", json=CATEGORY)).json()["data"]
    product_payload = {
        "name": "Coca-Cola 2L",
        "description": "Refrigerante garrafa 2 litros",
        "shortDescription": "Coca 2L",
        "price": 9.99,
        "weight": 2.1,
        "height": 32,
        "length": 11,
        "image": "https://example.com/coca.png",
        "idCategory": category["id"],
        "idCompany": company["id"],
    }
    product = (await client.post("/api/Products", json=product_payload)).json()["data"]
    customer_payload = {
        **{k: v for k, v in COMPANY.items() if k != "companyAddress"},
        "customerAddress": COMPANY["companyAddress"],
    }
    customer = (await client.post("/api/Customers", json=customer_payload)).json()["data"]

    sale_payload = {
        "quantity": 2,
        "totalPrice": 19.98,
        "totalTax": 1.99,
        "saleType": 1,
        "paymentType": 3,
        "deliveryDate": "2026-09-10T12:00:00",
        "saleDate": "2026-09-04T10:00:00",
        "paymentDate": "2026-09-04T10:30:00",
        "idCustomer": customer["id"],
        "idsProducts": [product["id"]],
    }
    created = await client.post("/api/Sales", json=sale_payload)
    assert created.status_code == 200
    sale = created.json()["data"]
    assert sale["saleType"] == 1 and sale["paymentType"] == 3
    assert sale["customer"]["name"] == "Acme Ltda"
    assert sale["products"][0]["id"] == product["id"]

    sale_id = sale["id"]
    deleted = await client.delete(f"/api/Sales/{sale_id}")
    assert deleted.status_code == 200 and deleted.json() == {}

    # Paridade .NET: Customer/Sale usam soft delete (não aparecem nas buscas? — .NET não filtra;
    # aqui GET por id ainda encontra a linha, pois o .NET também retorna).
    still_there = await client.get(f"/api/Sales/{sale_id}")
    assert still_there.status_code == 200


async def test_tax_category_missing_returns_400_parity(client: AsyncClient) -> None:
    response = await client.post(
        "/api/Taxs",
        json={
            "name": "ICMS",
            "description": "Imposto sobre circulação",
            "percentage": 18,
            "idCategory": str(uuid4()),
        },
    )
    assert response.status_code == 400  # ValidationException("Category not found") — paridade
    assert response.json()["error"] == "Category not found"


async def test_tax_crud_with_category(client: AsyncClient) -> None:
    category = (await client.post("/api/Categories", json=CATEGORY)).json()["data"]
    created = await client.post(
        "/api/Taxs",
        json={
            "name": "ICMS",
            "description": "Imposto sobre circulação de mercadorias",
            "percentage": 18,
            "idCategory": category["id"],
        },
    )
    assert created.status_code == 200
    tax = created.json()["data"]
    assert tax["category"]["id"] == category["id"]
    assert Decimal(str(tax["percentage"])) == 18


async def test_gridify_endpoint_filtering(client: AsyncClient) -> None:
    await client.post("/api/Categories", json=CATEGORY)
    await client.post(
        "/api/Categories",
        json={
            "name": "Limpeza",
            "description": "Produtos de limpeza",
            "shortDescription": "Limpadores",
        },
    )
    response = await client.get(
        "/api/Categories/gridify",
        params={"filter": "name=Bebidas", "orderBy": "name asc", "page": 1, "pageSize": 10},
    )
    assert response.status_code == 200
    body = response.json()
    assert [item["name"] for item in body["data"]] == ["Bebidas"]
    assert body["pagedResult"]["rowCount"] == 1


async def test_gridify_unknown_field_returns_400(client: AsyncClient) -> None:
    response = await client.get("/api/Categories/gridify", params={"filter": "hacker=1"})
    assert response.status_code == 400
    assert "Unknown filter field" in response.json()["error"]


async def test_paging_invalid_page_returns_422(client: AsyncClient) -> None:
    # Validação de boundary do FastAPI (diferença de framework documentada).
    response = await client.get("/api/Categories", params={"pageIndex": 0})
    assert response.status_code == 422


async def test_company_events_published_on_create(bus: object, client: AsyncClient) -> None:
    await _create_company(client)
    assert any(type(event).__name__ == "CompanyCreated" for event, _ in bus.published)  # type: ignore[union-attr]
    assert all(
        exchange == "company-service"
        for event, exchange in bus.published  # type: ignore[union-attr]
        if type(event).__name__ == "CompanyCreated"
    )
