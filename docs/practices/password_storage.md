# How we store passwords

Since the project is personal and not intended for production use, many practices that would be essential in a production environment are simplified or omitted. However, we still try follow some basic principles to ensure a reasonable level of security where reasonable.

* [ ] Protection of databases and containers

At the moment, we configured the Docker Compose and Dockerfiles in a way that allows us to easily change the database credentials. However, the secrets themselves are still hardcoded in the `docker-compose.yml` file. This is something we might want to improve in the future.

We use the most popular and well-tested base containers.

* [x] Hashing passwords

We hash the passwords on the frontend before even sending them to the backend.



* [ ] Using a strong hash function

## Sources

* ["9 Password Storage Best Practices" article on Snyk blog](https://snyk.io/articles/password-storage-best-practices/),
* [OWASP Cheat Sheet on Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
