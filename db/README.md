# Database (PostgreSQL)

If you want to process and inspect the crawled dataset in a DB, you can use the following setup (the example uses PostgreSQL):

```bash
psql -c "CREATE DATABASE maalfrid_test"
psql -d maalfrid_test -f schema.sql
psql -d maalfrid_test -f indices.sql
```

You need to import the domains that you want to process to the __domains__ table prior to import, e.g.:

```sql
INSERT INTO domains(domain) VALUES('example.com');
```

Remember to set up the .env file in the project root folder accordingly (an example can be found in env-example).
