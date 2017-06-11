DROP TABLE IF EXISTS ord_order;
CREATE TABLE ord_order (
    order_type text not null,
    price float not null,
    amount float not null
);


DROP TABLE IF EXISTS txn_transaction;
CREATE TABLE txn_transaction (
    tf_date datetime not null,
    tid int not null PRIMARY KEY,
    price float not null,
    amount float not null
);
CREATE UNIQUE INDEX txn_id on txn_transaction(tid);
