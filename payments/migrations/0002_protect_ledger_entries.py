from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION prevent_ledger_entry_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION
        'Ledger entries are immutable. UPDATE and DELETE operations are prohibited.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_ledger_entry_update
BEFORE UPDATE ON payments_ledgerentry
FOR EACH ROW
EXECUTE FUNCTION prevent_ledger_entry_modification();

CREATE TRIGGER prevent_ledger_entry_delete
BEFORE DELETE ON payments_ledgerentry
FOR EACH ROW
EXECUTE FUNCTION prevent_ledger_entry_modification();
"""


REVERSE_SQL = """
DROP TRIGGER IF EXISTS prevent_ledger_entry_update
ON payments_ledgerentry;

DROP TRIGGER IF EXISTS prevent_ledger_entry_delete
ON payments_ledgerentry;

DROP FUNCTION IF EXISTS prevent_ledger_entry_modification();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]