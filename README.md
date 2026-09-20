## Database configuration

## Publish with Streamlit Community Cloud

1. Create a GitHub repository and upload this project, including `app.py`,
	`requirements.txt`, and `model/best.onnx`.
2. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with
	GitHub.
3. Select **Create app**, choose the repository and branch, and set the main
	file path to `app.py`.
4. Add the database connection under **Advanced settings** as a secret:

```toml
DATABASE_URL = "postgresql://user:password@host:5432/database?sslmode=require"
```

5. Deploy the app. Streamlit Community Cloud will provide a permanent public
	URL such as `https://your-app-name.streamlit.app`.

The PostgreSQL database must be reachable from the internet and must contain
the tables defined in `database/schema.sql`. Do not commit database passwords
or other secrets to GitHub.

The application supports any hosted PostgreSQL provider. Set `DATABASE_URL` in
the cloud service's environment variables, using the connection string supplied
by that provider:

```text
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
```

Do not commit the connection string. The existing local PostgreSQL settings are
used when `DATABASE_URL` is not set.

After configuring the cloud database, run `database/schema.sql` once against it
to create the application tables, then deploy the application with the same
environment variable.
