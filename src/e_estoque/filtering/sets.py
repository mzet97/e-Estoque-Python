"""Registro dos entity sets OData (equivalente ao ODataModel.cs do .NET)."""

from __future__ import annotations

from e_estoque.filtering.odata import EntitySetSpec
from e_estoque.inventory.infrastructure.models import InventoryModel
from e_estoque.product.infrastructure.models import (
    CategoryModel,
    CompanySummaryModel,
    ProductModel,
)
from e_estoque.sale.infrastructure.models import (
    CustomerSummaryModel,
    SaleModel,
    SaleProductModel,
)
from e_estoque.shared.infrastructure.sql_filtering import FieldDef, FieldType
from e_estoque.tax.infrastructure.models import TaxModel

_AUDIT = {
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}


_PRODUCT_FIELDS = {
    "id": FieldDef("id", FieldType.UUID),
    "name": FieldDef("name", FieldType.STRING),
    "description": FieldDef("description", FieldType.STRING),
    "shortdescription": FieldDef("short_description", FieldType.STRING),
    "price": FieldDef("price", FieldType.NUMBER),
    "weight": FieldDef("weight", FieldType.NUMBER),
    "height": FieldDef("height", FieldType.NUMBER),
    "length": FieldDef("length", FieldType.NUMBER),
    "image": FieldDef("image", FieldType.STRING),
    "idcategory": FieldDef("id_category", FieldType.UUID),
    "idcompany": FieldDef("id_company", FieldType.UUID),
    **_AUDIT,
}

_CUSTOMER_FIELDS = {
    "id": FieldDef("id", FieldType.UUID),
    "name": FieldDef("name", FieldType.STRING),
    "docid": FieldDef("doc_id", FieldType.STRING),
    "email": FieldDef("email", FieldType.STRING),
    "description": FieldDef("description", FieldType.STRING),
    "phonenumber": FieldDef("phone_number", FieldType.STRING),
    **_AUDIT,
}


def odata_sets() -> list[EntitySetSpec]:
    """Entity sets na grafia do .NET (`Taxs`, `inventories` minúsculo na tabela)."""
    return [
        EntitySetSpec(
            name="Products",
            model=ProductModel,
            fields=_PRODUCT_FIELDS,
            columns=(
                "id",
                "name",
                "description",
                "short_description",
                "price",
                "weight",
                "height",
                "length",
                "image",
                "id_category",
                "id_company",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
        EntitySetSpec(
            name="Categories",
            model=CategoryModel,
            fields={
                "id": FieldDef("id", FieldType.UUID),
                "name": FieldDef("name", FieldType.STRING),
                "description": FieldDef("description", FieldType.STRING),
                "shortdescription": FieldDef("short_description", FieldType.STRING),
                **_AUDIT,
            },
            columns=(
                "id",
                "name",
                "description",
                "short_description",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
        EntitySetSpec(
            name="Companies",
            model=CompanySummaryModel,
            fields=dict(_CUSTOMER_FIELDS),
            columns=(
                "id",
                "name",
                "doc_id",
                "email",
                "description",
                "phone_number",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
        EntitySetSpec(
            name="Customers",
            model=CustomerSummaryModel,
            fields=dict(_CUSTOMER_FIELDS),
            columns=(
                "id",
                "name",
                "doc_id",
                "email",
                "description",
                "phone_number",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
        EntitySetSpec(
            name="Inventories",
            model=InventoryModel,
            fields={
                "id": FieldDef("id", FieldType.UUID),
                "quantity": FieldDef("quantity", FieldType.NUMBER),
                "dateorder": FieldDef("date_order", FieldType.STRING),
                "idproduct": FieldDef("id_product", FieldType.UUID),
                **_AUDIT,
            },
            columns=(
                "id",
                "quantity",
                "date_order",
                "id_product",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
        EntitySetSpec(
            name="Sales",
            model=SaleModel,
            fields={
                "id": FieldDef("id", FieldType.UUID),
                "quantity": FieldDef("quantity", FieldType.NUMBER),
                "totalprice": FieldDef("total_price", FieldType.NUMBER),
                "totaltax": FieldDef("total_tax", FieldType.NUMBER),
                "saletype": FieldDef("sale_type", FieldType.NUMBER),
                "paymenttype": FieldDef("payment_type", FieldType.NUMBER),
                "deliverydate": FieldDef("delivery_date", FieldType.INSTANT),
                "saledate": FieldDef("sale_date", FieldType.INSTANT),
                "paymentdate": FieldDef("payment_date", FieldType.INSTANT),
                "idcustomer": FieldDef("id_customer", FieldType.UUID),
                **_AUDIT,
            },
            columns=(
                "id",
                "quantity",
                "total_price",
                "total_tax",
                "sale_type",
                "payment_type",
                "delivery_date",
                "sale_date",
                "payment_date",
                "id_customer",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
        EntitySetSpec(
            name="SaleProducts",
            model=SaleProductModel,
            fields={
                "id": FieldDef("id", FieldType.UUID),
                "quantity": FieldDef("quantity", FieldType.NUMBER),
                "idproduct": FieldDef("id_product", FieldType.UUID),
                "idsale": FieldDef("id_sale", FieldType.UUID),
                **_AUDIT,
            },
            columns=(
                "id",
                "quantity",
                "id_product",
                "id_sale",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
        EntitySetSpec(
            name="Taxs",
            model=TaxModel,
            fields={
                "id": FieldDef("id", FieldType.UUID),
                "name": FieldDef("name", FieldType.STRING),
                "description": FieldDef("description", FieldType.STRING),
                "percentage": FieldDef("percentage", FieldType.NUMBER),
                "idcategory": FieldDef("id_category", FieldType.UUID),
                **_AUDIT,
            },
            columns=(
                "id",
                "name",
                "description",
                "percentage",
                "id_category",
                "created_at",
                "updated_at",
                "deleted_at",
                "is_deleted",
            ),
        ),
    ]
