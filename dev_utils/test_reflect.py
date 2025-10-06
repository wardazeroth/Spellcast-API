import os
from sqlalchemy import create_engine, MetaData, Table, inspect, text

DATABASE_URL = "postgresql+psycopg://postgres.upztqsvobkmnmnecbpmg:Nh3x41nt3rf4c3@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
print("Has DATABASE_URL?", bool(DATABASE_URL))

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("current_user:", conn.execute(text("select current_user")).scalar())
    print("search_path :", conn.execute(text("show search_path")).scalar())
    rows = conn.execute(text("""
        select table_schema, table_name
        from information_schema.tables
        where table_name = 'users'
        order by table_schema
    """)).all()
    print("Dónde hay 'users':", rows)

insp = inspect(engine)
print("Schemas visibles:", insp.get_schema_names())
print("Tablas en 'accounts':", insp.get_table_names(schema="accounts"))

md = MetaData()
users = Table("users", md, schema="accounts", autoload_with=engine)
print("Columnas de accounts.users:", [c.name for c in users.columns])
