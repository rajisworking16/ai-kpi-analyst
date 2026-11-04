"""Shared pytest fixtures: a tiny hand-built Olist-shaped database."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from src.data_load import create_views

SCHEMA = """
CREATE TABLE orders (order_id VARCHAR, customer_id VARCHAR, order_status VARCHAR,
    order_purchase_timestamp TIMESTAMP, order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP, order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP);
CREATE TABLE order_items (order_id VARCHAR, order_item_id BIGINT, product_id VARCHAR,
    seller_id VARCHAR, shipping_limit_date TIMESTAMP, price DOUBLE, freight_value DOUBLE);
CREATE TABLE payments (order_id VARCHAR, payment_sequential BIGINT, payment_type VARCHAR,
    payment_installments BIGINT, payment_value DOUBLE);
CREATE TABLE reviews (review_id VARCHAR, order_id VARCHAR, review_score BIGINT,
    review_comment_title VARCHAR, review_comment_message VARCHAR,
    review_creation_date TIMESTAMP, review_answer_timestamp TIMESTAMP);
CREATE TABLE customers (customer_id VARCHAR, customer_unique_id VARCHAR,
    customer_zip_code_prefix BIGINT, customer_city VARCHAR, customer_state VARCHAR);
CREATE TABLE sellers (seller_id VARCHAR, seller_zip_code_prefix BIGINT,
    seller_city VARCHAR, seller_state VARCHAR);
CREATE TABLE products (product_id VARCHAR, product_category_name VARCHAR);
CREATE TABLE category_translation (product_category_name VARCHAR,
    product_category_name_english VARCHAR);
"""

DATA = """
INSERT INTO customers VALUES ('c1','u1',1,'sp','SP'),('c2','u2',2,'rj','RJ'),
    ('c3','u3',3,'sp','SP'),('c4','u4',4,'bh','MG');
INSERT INTO sellers VALUES ('s1',1,'sp','SP'),('s2',2,'rj','RJ');
INSERT INTO products VALUES ('p1','beleza_saude'),('p2','informatica_acessorios');
INSERT INTO category_translation VALUES ('beleza_saude','health_beauty'),
    ('informatica_acessorios','computers_accessories');
INSERT INTO orders VALUES
 ('o1','c1','delivered','2018-02-05 00:00','2018-02-05',NULL,'2018-02-10 00:00','2018-02-15'),
 ('o2','c2','delivered','2018-02-10 00:00','2018-02-10',NULL,'2018-02-25 00:00','2018-02-20'),
 ('o3','c3','canceled','2018-02-12 00:00',NULL,NULL,NULL,'2018-02-28'),
 ('o4','c4','delivered','2018-03-01 00:00','2018-03-01',NULL,'2018-03-04 00:00','2018-03-10');
INSERT INTO order_items VALUES
 ('o1',1,'p1','s1',NULL,100,10),
 ('o2',1,'p2','s2',NULL,200,20),
 ('o2',2,'p1','s1',NULL,50,5),
 ('o4',1,'p2','s2',NULL,300,30);
INSERT INTO payments VALUES ('o1',1,'credit_card',1,110),('o2',1,'boleto',1,275),
    ('o4',1,'credit_card',3,330);
INSERT INTO reviews VALUES ('r1','o1',5,NULL,NULL,NULL,NULL),('r2a','o2',2,NULL,NULL,NULL,NULL),
    ('r2b','o2',4,NULL,NULL,NULL,NULL),('r3','o3',1,NULL,NULL,NULL,NULL),
    ('r4','o4',4,NULL,NULL,NULL,NULL);
"""


def build_fixture_db(path: Path) -> Path:
    """Write the tiny fixture database to `path`."""
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    con.execute(DATA)
    create_views(con)
    con.close()
    return path


@pytest.fixture
def fixture_db(tmp_path: Path) -> Path:
    return build_fixture_db(tmp_path / "fixture.duckdb")


@pytest.fixture
def fixture_con(fixture_db: Path):
    con = duckdb.connect(str(fixture_db), read_only=True)
    yield con
    con.close()
