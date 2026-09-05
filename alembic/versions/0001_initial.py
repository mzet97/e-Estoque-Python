"""initial schema (paridade literal da migration EF 20250327000516_001)

Revision ID: 0001
Revises:
Create Date: 2026-09-04

Tabelas com aspas preservando o PascalCase do .NET; `inventories` minúsculas;
`DateOrder` varchar(80); `Products.Name` text; FKs ON DELETE NO ACTION.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_AUDIT = [
    sa.Column("CreatedAt", sa.DateTime(), nullable=False),
    sa.Column("UpdatedAt", sa.DateTime(), nullable=True),
    sa.Column("DeletedAt", sa.DateTime(), nullable=True),
    sa.Column("IsDeleted", sa.Boolean(), nullable=False),
]


def upgrade() -> None:
    op.create_table(
        "Categories",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Name", sa.String(length=80), nullable=False),
        sa.Column("Description", sa.String(length=5000), nullable=False),
        sa.Column("ShortDescription", sa.String(length=500), nullable=False),
        *_AUDIT,
        sa.PrimaryKeyConstraint("Id", name="PK_Categories"),
        schema="public",
    )
    op.create_table(
        "Companies",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Name", sa.String(length=80), nullable=False),
        sa.Column("DocId", sa.String(length=80), nullable=False),
        sa.Column("Email", sa.String(length=250), nullable=False),
        sa.Column("PhoneNumber", sa.String(length=80), nullable=False),
        sa.Column("Description", sa.String(length=250), nullable=False),
        sa.Column("CompanyAddress_Street", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_Number", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_Complement", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_Neighborhood", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_District", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_City", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_County", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_ZipCode", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_Latitude", sa.String(length=80), nullable=False),
        sa.Column("CompanyAddress_Longitude", sa.String(length=80), nullable=False),
        *_AUDIT,
        sa.PrimaryKeyConstraint("Id", name="PK_Companies"),
        schema="public",
    )
    op.create_table(
        "Customers",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Name", sa.String(length=80), nullable=False),
        sa.Column("DocId", sa.String(length=80), nullable=False),
        sa.Column("Email", sa.String(length=80), nullable=False),
        sa.Column("PhoneNumber", sa.String(length=80), nullable=False),
        sa.Column("Description", sa.String(length=250), nullable=False),
        sa.Column("CustomerAddress_Street", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_Number", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_Complement", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_Neighborhood", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_District", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_City", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_County", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_ZipCode", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_Latitude", sa.String(length=80), nullable=False),
        sa.Column("CustomerAddress_Longitude", sa.String(length=80), nullable=False),
        *_AUDIT,
        sa.PrimaryKeyConstraint("Id", name="PK_Customers"),
        schema="public",
    )
    op.create_table(
        "Products",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Name", sa.Text(), nullable=False),
        sa.Column("Description", sa.String(length=500), nullable=False),
        sa.Column("ShortDescription", sa.String(length=250), nullable=False),
        sa.Column("Price", sa.Numeric(), nullable=False),
        sa.Column("Weight", sa.Numeric(), nullable=False),
        sa.Column("Height", sa.Numeric(), nullable=False),
        sa.Column("Length", sa.Numeric(), nullable=False),
        sa.Column("Image", sa.String(length=5000), nullable=False),
        sa.Column("IdCategory", sa.UUID(), nullable=False),
        sa.Column("IdCompany", sa.UUID(), nullable=False),
        *_AUDIT,
        sa.ForeignKeyConstraint(
            ["IdCategory"], ["Categories.Id"], name="FK_Products_Categories_IdCategory"
        ),
        sa.ForeignKeyConstraint(
            ["IdCompany"], ["Companies.Id"], name="FK_Products_Companies_IdCompany"
        ),
        sa.PrimaryKeyConstraint("Id", name="PK_Products"),
        schema="public",
    )
    op.create_index("IX_Products_IdCategory", "Products", ["IdCategory"], schema="public")
    op.create_index("IX_Products_IdCompany", "Products", ["IdCompany"], schema="public")
    op.create_table(
        "inventories",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Quantity", sa.Integer(), nullable=False),
        sa.Column("DateOrder", sa.String(length=80), nullable=False),
        sa.Column("IdProduct", sa.UUID(), nullable=False),
        *_AUDIT,
        sa.ForeignKeyConstraint(
            ["IdProduct"], ["Products.Id"], name="FK_inventories_Products_IdProduct"
        ),
        sa.PrimaryKeyConstraint("Id", name="PK_inventories"),
        schema="public",
    )
    op.create_index("IX_inventories_IdProduct", "inventories", ["IdProduct"], schema="public")
    op.create_table(
        "Sales",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Quantity", sa.Integer(), nullable=False),
        sa.Column("TotalPrice", sa.Numeric(), nullable=False),
        sa.Column("TotalTax", sa.Numeric(), nullable=False),
        sa.Column("SaleType", sa.Integer(), nullable=False),
        sa.Column("PaymentType", sa.Integer(), nullable=False),
        sa.Column("DeliveryDate", sa.DateTime(), nullable=False),
        sa.Column("SaleDate", sa.DateTime(), nullable=False),
        sa.Column("PaymentDate", sa.DateTime(), nullable=False),
        sa.Column("IdCustomer", sa.UUID(), nullable=False),
        *_AUDIT,
        sa.ForeignKeyConstraint(
            ["IdCustomer"], ["Customers.Id"], name="FK_Sales_Customers_IdCustomer"
        ),
        sa.PrimaryKeyConstraint("Id", name="PK_Sales"),
        schema="public",
    )
    op.create_index("IX_Sales_IdCustomer", "Sales", ["IdCustomer"], schema="public")
    op.create_table(
        "SaleProducts",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Quantity", sa.Integer(), nullable=False),
        sa.Column("IdProduct", sa.UUID(), nullable=False),
        sa.Column("IdSale", sa.UUID(), nullable=False),
        *_AUDIT,
        sa.ForeignKeyConstraint(
            ["IdProduct"], ["Products.Id"], name="FK_SaleProducts_Products_IdProduct"
        ),
        sa.ForeignKeyConstraint(
            ["IdSale"], ["Sales.Id"], name="FK_SaleProducts_Sales_IdSale"
        ),
        sa.PrimaryKeyConstraint("Id", name="PK_SaleProducts"),
        schema="public",
    )
    op.create_index(
        "IX_SaleProducts_IdProduct", "SaleProducts", ["IdProduct"], schema="public"
    )
    op.create_index("IX_SaleProducts_IdSale", "SaleProducts", ["IdSale"], schema="public")
    op.create_table(
        "Taxs",
        sa.Column("Id", sa.UUID(), nullable=False),
        sa.Column("Name", sa.String(length=80), nullable=False),
        sa.Column("Description", sa.String(length=250), nullable=False),
        sa.Column("Percentage", sa.Numeric(), nullable=False),
        sa.Column("IdCategory", sa.UUID(), nullable=False),
        *_AUDIT,
        sa.ForeignKeyConstraint(
            ["IdCategory"], ["Categories.Id"], name="FK_Taxs_Categories_IdCategory"
        ),
        sa.PrimaryKeyConstraint("Id", name="PK_Taxs"),
        schema="public",
    )
    op.create_index("IX_Taxs_IdCategory", "Taxs", ["IdCategory"], schema="public")


def downgrade() -> None:
    op.drop_table("Taxs", schema="public")
    op.drop_table("SaleProducts", schema="public")
    op.drop_table("Sales", schema="public")
    op.drop_table("inventories", schema="public")
    op.drop_table("Products", schema="public")
    op.drop_table("Customers", schema="public")
    op.drop_table("Companies", schema="public")
    op.drop_table("Categories", schema="public")
