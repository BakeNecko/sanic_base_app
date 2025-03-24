CREATE OR REPLACE FUNCTION insert_user(
    user_name VARCHAR, 
    user_email VARCHAR,
    is_admin BOOLEAN
) RETURNS INT AS $$
DECLARE
    new_user_id INT;
BEGIN
    INSERT INTO public.user (name, email, password, is_admin, created_at, updated_at) 
    VALUES (
        user_name, 
        user_email, 
        '$2b$12$Tz74VeW7ZBNlwzV64HEE6eXxTdocwvv0PtGqEASMcVaKzDZbadSCS', 
        is_admin, 
        NOW(), 
        NOW()
    ) RETURNING id INTO new_user_id;

    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_bill(
    user_id INT,
    bill_account_id INT,
    bill_amount DECIMAL
) RETURNS INT AS $$
DECLARE
    new_bill_id INT;
BEGIN
    INSERT INTO bill (amount, user_id, account_id) 
    VALUES (bill_amount, user_id, bill_account_id)
    RETURNING id INTO new_bill_id;

    RETURN new_bill_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_transaction(
    bill_id INT, 
    trans_id VARCHAR,
    trans_amount DECIMAL
    )
RETURNS VOID AS $$
BEGIN
    INSERT INTO transaction (bill_id, transaction_id, t_amount) 
    VALUES (bill_id, trans_id, trans_amount);
END;
$$ LANGUAGE plpgsql;

-- Insert Users
DO $$
DECLARE
    user_id INT;
    bill_id INT;
BEGIN
    BEGIN
        PERFORM insert_user('admin', 'admin@mail.ru', true);
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;

    BEGIN
        user_id := insert_user('user', 'user@mail.ru', false);
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;

    BEGIN
        bill_id := insert_bill(user_id, 101, 150.00);
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;

    BEGIN
        PERFORM insert_transaction(bill_id, '9cdebccd-30f4-4a21-bb77-0b18696cb1a8', 75.00);
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;

    BEGIN
        PERFORM insert_transaction(bill_id, 'db1cc99b-379b-4038-be84-362b9158a686', 75.00);
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
    END;
END;
$$;


