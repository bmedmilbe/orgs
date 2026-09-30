# Orgs — Multi-Tenant CMS API

Orgs is a Django-based multi-tenant CMS API designed to provide isolated data access for different organisations within a shared application infrastructure.

The project focuses on multi-tenant architecture, PostgreSQL data management, ORM optimisation, automated testing and containerised deployment.

## 🚀 Key Features

* Multi-tenant architecture using Django Tenants
* REST API built with Django REST Framework
* PostgreSQL database
* Tenant-isolated data access
* ORM query optimisation with `select_related` and `prefetch_related`
* Automated testing with pytest
* In-memory caching for tests
* Parallel test execution
* Docker-based development
* CI/CD with GitHub Actions
* Railway deployment
* AWS S3 media storage

## 🏗️ Architecture

The application uses Django Tenants to separate tenant data while running within a shared application infrastructure.

```text
                    Client
                      |
                      v
                Django / DRF
                      |
              Django Tenants
                      |
          +-----------+-----------+
          |                       |
          v                       v
     Tenant A                 Tenant B
          |                       |
          +-----------+-----------+
                      |
                      v
                  PostgreSQL
```

Tenant-aware requests are handled by the application and routed to the appropriate tenant context.

## ⚡ Database Optimisation

The project uses Django ORM optimisation techniques such as:

```python
select_related()
prefetch_related()
```

These techniques reduce unnecessary database queries when retrieving related objects and help improve API response times.

## 🧪 Test Performance

The test suite was optimised using several techniques, including:

* Faster Django test strategies
* In-memory caching
* HTTP and time mocking
* Parallel test execution with `pytest-xdist`
* Improved test data creation

The test suite was reduced from:

```text
191 tests

Before: 108.35s
After:   48.96s

Approximately 55% reduction
```

The benchmark includes the runtime of the complete pytest execution, including parallel worker startup overhead.

## 🛠️ Technology Stack

| Technology            | Purpose                 |
| --------------------- | ----------------------- |
| Python                | Backend development     |
| Django                | Web framework           |
| Django REST Framework | REST API                |
| Django Tenants        | Multi-tenancy           |
| PostgreSQL            | Relational database     |
| pytest                | Automated testing       |
| pytest-xdist          | Parallel test execution |
| Docker                | Containerisation        |
| GitHub Actions        | CI/CD                   |
| Railway               | Deployment              |
| AWS S3                | Media storage           |

## 🚀 Getting Started

1. Clone the repository.
2. Install the project dependencies.
3. Configure the required environment variables.
4. Configure PostgreSQL.
5. Configure the tenant settings.
6. Apply Django migrations.
7. Run the development server.
8. Run the test suite with pytest.

Refer to the project configuration files for the exact commands and environment variables.

## 📌 Engineering Focus

This project demonstrates practical experience with:

* Multi-tenant Django architecture
* REST API development
* PostgreSQL and ORM optimisation
* Database query performance
* Automated testing
* Test-suite performance optimisation
* Docker
* CI/CD
* Cloud media storage

## 👨‍💻 Author

**Edmilbe Ramos**
Python Backend Developer

* GitHub: https://github.com/bmedmilbe
* LinkedIn: https://www.linkedin.com/in/edmilbe-ramos/
