# file: orgs/management/commands/populate_cecab.py

import random
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import Client, Domain
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django_tenants.utils import tenant_context
from faker import Faker
from orgs.models import (
    Association,
    AssociationImage,
    BlogCategory,
    Budget,
    CatalogItem,
    CatalogItemSpecification,
    Category,
    District,
    ExtraDoc,
    ExtraImage,
    Information,
    Page,
    PageContentBlock,
    Partner,
    Post,
    PostDocument,
    PostFile,
    PostImage,
    PostVideo,
    Review,
    Role,
    Team,
    Video,
    YearGoal,
)

User = get_user_model()
fake = Faker(["pt_BR", "en_US", "fr_FR"])  # Prioritizing Portuguese for CECAB


class Command(BaseCommand):
    help = "Populate CECAB tenant with realistic data for São Tomé and Príncipe"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=20,
            help="Number of regular users to create (default: 20)",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=15,
            help="Number of blog posts to create (default: 15)",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing data before populating (use with caution)",
        )

    def handle(self, *args, **options):
        num_users = options["users"]
        num_posts = options["posts"]
        reset = options["reset"]

        self.stdout.write(self.style.SUCCESS("🚀 Starting CECAB data population..."))

        # Get or create CECAB tenant
        try:
            tenant = Client.objects.get(schema_name="cecab")
            self.stdout.write(self.style.SUCCESS("✅ Found existing tenant: cecab"))
        except Client.DoesNotExist:
            tenant = self.create_cecab_tenant()
            self.stdout.write(self.style.SUCCESS("✅ Created new tenant: cecab"))

        # Switch to tenant schema
        with tenant_context(tenant):
            self.stdout.write(
                self.style.SUCCESS(f"🔀 Switched to schema: {tenant.schema_name}")
            )

            if reset:
                self.reset_data()

            # Populate all data
            self.populate_cecab_data(tenant, num_users, num_posts)

        self.stdout.write(
            self.style.SUCCESS("🎉 CECAB data population completed successfully!")
        )

    def create_cecab_tenant(self):
        """Create the CECAB tenant with proper configuration."""
        tenant = Client.objects.create(
            schema_name="cecab",
            name="CECAB - São Tomé e Príncipe",
            paid_until=datetime.now().date() + timedelta(days=365),
            on_trial=False,
            created_on=datetime.now().date(),
        )

        # Create domain for local development
        Domain.objects.create(
            domain="cecab.localhost",
            tenant=tenant,
            is_primary=True,
        )

        return tenant

    def reset_data(self):
        """Delete all existing data in the tenant."""
        self.stdout.write("🗑️ Resetting existing data...")

        # Delete in reverse order of dependencies
        models_to_delete = [
            Review,
            CatalogItemSpecification,
            CatalogItem,
            Category,
            PostVideo,
            Video,
            PostImage,
            PostFile,
            PostDocument,
            Information,
            Post,
            BlogCategory,
            PageContentBlock,
            Page,
            AssociationImage,
            Association,
            District,
            Team,
            Role,
            Budget,
            ExtraImage,
            ExtraDoc,
            Partner,
            YearGoal,
        ]

        for model in models_to_delete:
            try:
                count = model.objects.all().delete()
                self.stdout.write(f"  - Deleted {count[0]} {model.__name__} records")
            except Exception as e:
                self.stdout.write(f"  - Error deleting {model.__name__}: {e}")

        # Delete users (except superusers if any)
        try:
            count = User.objects.filter(is_customer=False).delete()
            self.stdout.write(f"  - Deleted {count[0]} regular users")
        except Exception as e:
            self.stdout.write(f"  - Error deleting users: {e}")

        self.stdout.write(self.style.SUCCESS("✅ Data reset completed"))

    def populate_cecab_data(self, tenant, num_users, num_posts):
        """Populate the CECAB tenant with realistic data."""
        self.stdout.write("📝 Populating CECAB data...")

        # 1. Create or get customer user
        customer = self.get_or_create_customer_user(tenant)

        # 2. Create staff users
        staff_users = self.create_staff_users(tenant)

        # 3. Create regular users
        regular_users = self.create_regular_users(tenant, num_users)

        # 4. Create districts of São Tomé and Príncipe
        districts = self.create_districts()

        # 5. Create associations (cooperatives)
        associations = self.create_associations(districts)

        # 6. Create categories for products and services
        categories = self.create_categories()

        # 7. Create catalog items (chocolate, tours, accommodations)
        catalog_items = self.create_catalog_items(categories, regular_users, tenant)

        # 8. Create pages for the website
        self.create_pages()

        # 9. Create year goals (2024-2026)
        self.create_year_goals()

        # 10. Create blog categories
        blog_categories = self.create_blog_categories()

        # 11. Create blog posts
        self.create_posts(blog_categories, num_posts, tenant)

        # 12. Create videos (CECAB Band, promotional)
        self.create_videos()

        # 13. Create team members and roles
        roles = self.create_roles()
        self.create_team_members(roles)

        # 14. Create budget documents
        self.create_budget_documents()

        # 15. Create extra documents
        self.create_extra_documents()

        # 16. Create partners
        self.create_partners()

        self.stdout.write(
            self.style.SUCCESS("✅ All CECAB data populated successfully!")
        )

    def get_or_create_customer_user(self, tenant):
        """Get or create the CECAB customer/admin user."""
        customer_email = "admin@cecab.st"

        # Try to get existing customer
        try:
            customer = User.objects.get(
                email=customer_email, is_customer=True, tenant=tenant
            )
            self.stdout.write(f"ℹ️ Customer user already exists: {customer.email}")
            return customer
        except User.DoesNotExist:
            pass

        # Check if there's already a customer for this tenant
        existing_customer = User.objects.filter(tenant=tenant, is_customer=True).first()
        if existing_customer:
            self.stdout.write(
                f"ℹ️ Customer user already exists: {existing_customer.email}"
            )
            return existing_customer

        # Create new customer
        try:
            customer = User.objects.create(
                username="cecab_admin",
                email=customer_email,
                first_name="CECAB",
                last_name="Administrador",
                phone="+239 99 01 02",
                is_customer=True,
                is_staff=True,
                is_superuser=True,
                tenant=tenant,
            )
            customer.set_password("cecab2024")
            customer.save()
            self.stdout.write(
                f"✅ Created customer user: {customer.email} (password: cecab2024)"
            )
            return customer
        except IntegrityError:
            # If there's a conflict, get the existing one
            customer = User.objects.get(tenant=tenant, is_customer=True)
            self.stdout.write(f"ℹ️ Using existing customer: {customer.email}")
            return customer

    def create_staff_users(self, tenant):
        """Create CECAB staff users."""
        staff_data = [
            ("João", "Costa", "joao.costa@cecab.st", "Gerente Geral"),
            (
                "Maria",
                "Fernandes",
                "maria.fernandes@cecab.st",
                "Coordenadora de Produção",
            ),
            ("Pedro", "Santos", "pedro.santos@cecab.st", "Responsável de Marketing"),
            ("Ana", "Silva", "ana.silva@cecab.st", "Coordenadora de Turismo"),
            (
                "Carlos",
                "Mendes",
                "carlos.mendes@cecab.st",
                "Responsável de Relações Públicas",
            ),
        ]

        staff_users = []
        for first_name, last_name, email, role in staff_data:
            # Check if user exists
            if User.objects.filter(email=email, tenant=tenant).exists():
                self.stdout.write(f"ℹ️ Staff user already exists: {email}")
                continue

            try:
                user = User.objects.create(
                    username=f"{first_name.lower()}_{last_name.lower()}",
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=fake.phone_number()[:15],
                    is_customer=False,
                    is_staff=True,
                    is_superuser=False,
                    tenant=tenant,
                )
                user.set_password("cecabstaff2024")
                user.save()
                staff_users.append(user)
                self.stdout.write(f"✅ Created staff: {user.email}")
            except IntegrityError:
                self.stdout.write(f"⚠️ Could not create staff user: {email}")
                continue

        self.stdout.write(f"✅ Created {len(staff_users)} staff users")
        return staff_users

    def create_regular_users(self, tenant, num_users):
        """Create regular users for testing."""
        users = []
        first_names = [
            "António",
            "José",
            "Manuel",
            "Francisco",
            "Fernando",
            "Rui",
            "Paulo",
            "Joaquim",
            "Augusto",
            "Celso",
            "Marta",
            "Helena",
            "Teresa",
            "Cristina",
            "Alice",
            "Isabel",
            "Rosa",
            "Lúcia",
            "Sandra",
            "Carla",
        ]
        last_names = [
            "Souza",
            "Lima",
            "Carvalho",
            "Ramos",
            "Gomes",
            "Monteiro",
            "Almeida",
            "Costa",
            "Pereira",
            "Rodrigues",
            "Santos",
            "Silva",
            "Oliveira",
            "Ferreira",
            "Martins",
        ]

        for i in range(num_users):
            try:
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                email = f"{first_name.lower()}.{last_name.lower()}@example.com"

                # Ensure unique email
                if User.objects.filter(email=email, tenant=tenant).exists():
                    email = fake.email()

                user = User.objects.create(
                    username=f"user_{i}_{fake.user_name()}",
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=fake.phone_number()[:15],
                    is_customer=False,
                    is_staff=False,
                    is_superuser=False,
                    tenant=tenant,
                )
                user.set_password("password123")
                user.save()
                users.append(user)
            except IntegrityError as e:
                self.stdout.write(f"⚠️ Could not create user: {e}")
                continue

        self.stdout.write(f"✅ Created {len(users)} regular users")
        return users

    def create_districts(self):
        """Create districts of São Tomé and Príncipe."""
        districts_data = [
            "Água Grande",
            "Cantagalo",
            "Caué",
            "Lembá",
            "Lobata",
            "Mé-Zóchi",
            "Príncipe",
        ]

        districts = []
        for name in districts_data:
            district, created = District.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f"✅ Created district: {name}")
            districts.append(district)

        self.stdout.write(f"✅ Total districts: {len(districts)}")
        return districts

    def create_associations(self, districts):
        """Create associations/cooperatives for CECAB."""
        associations_data = [
            ("Cooperativa Agrícola de Cantagalo", "Cantagalo"),
            ("Cooperativa Agrícola de Lembá", "Lembá"),
            ("Associação dos Produtores de Cacau do Caué", "Caué"),
            ("Cooperativa dos Agricultores de Lobata", "Lobata"),
            ("Associação dos Produtores de Café e Cacau", "Mé-Zóchi"),
            ("Cooperativa Agrícola de Príncipe", "Príncipe"),
            ("CECAB - São Tomé", "Água Grande"),
            ("Coopérative Agricole du Sud", "Caué"),
        ]

        associations = []
        for name, district_name in associations_data:
            district = next(
                (d for d in districts if d.name == district_name),
                random.choice(districts),
            )

            try:
                association = Association.objects.create(
                    name=name,
                    registered=fake.date_between(start_date="-15y", end_date="today"),
                    address=fake.street_address(),
                    number_of_associated=random.randint(30, 300),
                    picture=fake.image_url(),
                    district=district,
                )
                associations.append(association)

                # Add images
                for _ in range(random.randint(2, 4)):
                    AssociationImage.objects.create(
                        association=association, image=fake.image_url()
                    )
            except IntegrityError:
                self.stdout.write(f"⚠️ Association already exists: {name}")
                continue

        self.stdout.write(f"✅ Created {len(associations)} associations")
        return associations

    def create_categories(self):
        """Create product and service categories."""
        categories_data = [
            ("Chocolates", "chocolates"),
            ("Produtos de Cacau", "cacau"),
            ("Alojamento", "alojamento"),
            ("Visitas Guiadas", "visitas"),
            ("Oficinas", "oficinas"),
            ("Eventos", "eventos"),
            ("Presentes", "presentes"),
        ]

        categories = []
        for name, slug in categories_data:
            category, created = Category.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )
            categories.append(category)

        self.stdout.write(f"✅ Created {len(categories)} categories")
        return categories

    def create_catalog_items(self, categories, users, tenant):
        """Create catalog items with realistic CECAB products and services."""
        catalog_items = []

        # CECAB specific products
        products_data = [
            {
                "name": "Chocolate Amargo 70% CECAB",
                "description": "Chocolate premium com 70% de cacau de São Tomé, produzido artesanalmente",
                "price": 12.50,
                "slug": "chocolate-amargo-70",
            },
            {
                "name": "Chocolate ao Leite CECAB",
                "description": "Chocolate cremoso com 40% de cacau e notas de baunilha",
                "price": 10.00,
                "slug": "chocolate-leite",
            },
            {
                "name": "Chocolate Branco com Cacau",
                "description": "Chocolate branco com nibs de cacau torrado",
                "price": 11.00,
                "slug": "chocolate-branco",
            },
            {
                "name": "Tablete de Cacau 100%",
                "description": "Puro cacau de São Tomé para confeitaria",
                "price": 8.50,
                "slug": "tablete-cacau",
            },
            {
                "name": "Roça Vila - Suite Familiar",
                "description": "Suite espaçosa na antiga roça de cacau, com vista para as plantações",
                "price": 150.00,
                "slug": "roca-vila-suite",
            },
            {
                "name": "Roça São João - Quarto Standard",
                "description": "Quarto confortável na histórica Roça São João",
                "price": 75.00,
                "slug": "roca-sao-joao",
            },
            {
                "name": "Tour da Plantação de Cacau",
                "description": "Visita guiada à plantação de cacau, do grão à amêndoa",
                "price": 25.00,
                "slug": "tour-plantacao",
            },
            {
                "name": "Oficina de Chocolate",
                "description": "Aprenda a fazer chocolate artesanal do grão à tablete",
                "price": 45.00,
                "slug": "oficina-chocolate",
            },
            {
                "name": "Tour Histórico das Roças",
                "description": "Visita às antigas roças de café e cacau de São Tomé",
                "price": 35.00,
                "slug": "tour-rocas",
            },
            {
                "name": "Cesta de Presentes CECAB",
                "description": "Conjunto de chocolates e produtos de cacau para oferecer",
                "price": 30.00,
                "slug": "cesta-presentes",
            },
        ]

        for i, product in enumerate(products_data):
            category = random.choice(categories)

            try:
                item = CatalogItem.objects.create(
                    category=category,
                    name=product["name"],
                    slug=f"{product['slug']}-{i}",
                    description=product["description"],
                    price=Decimal(str(product["price"])),
                    is_available=random.choice([True, True, True, False]),
                    picture=fake.image_url(),
                    average_rating=Decimal(str(round(random.uniform(3.5, 5.0), 2))),
                    total_reviews=random.randint(1, 30),
                )
                catalog_items.append(item)

                # Add specifications
                specs = [
                    ("Origem", "São Tomé e Príncipe"),
                    ("Certificação", "Comércio Justo"),
                    ("Categoria", "Produto Premium"),
                    ("Validade", f"{random.randint(12, 24)} meses"),
                    ("Capacidade", f"{random.randint(2, 6)} pessoas"),
                    ("Duração", f"{random.randint(1, 4)} horas"),
                ]

                for key, value in random.sample(specs, random.randint(2, 4)):
                    CatalogItemSpecification.objects.create(
                        item=item, key=key, value=value
                    )

                # Add reviews
                if users and len(users) > 0:
                    for _ in range(random.randint(1, 3)):
                        review_user = random.choice(users)
                        try:
                            Review.objects.create(
                                item=item,
                                client=review_user,
                                rating=random.randint(3, 5),
                                comment=fake.paragraph(),
                                is_approved=random.choice([True, True, True, False]),
                            )
                        except IntegrityError:
                            continue
            except IntegrityError:
                self.stdout.write(f"⚠️ Catalog item already exists: {product['name']}")
                continue

        self.stdout.write(f"✅ Created {len(catalog_items)} catalog items")
        return catalog_items

    def create_pages(self):
        """Create CECAB website pages."""
        pages_data = [
            ("Início", "inicio", True, 0),
            ("Sobre Nós", "sobre-nos", True, 1),
            ("Fábrica de Chocolate", "fabrica", True, 2),
            ("Plantações", "plantacoes", True, 3),
            ("Turismo", "turismo", True, 4),
            ("Sustentabilidade", "sustentabilidade", True, 5),
            ("Contactos", "contactos", True, 6),
        ]

        block_types = ["text", "hero", "process"]

        for title, slug, active, order in pages_data:
            page, created = Page.objects.get_or_create(
                slug=slug, defaults={"title": title, "active": active, "order": order}
            )

            # Create content blocks only if page was just created
            if created:
                for i in range(random.randint(3, 5)):
                    block_type = random.choice(block_types)
                    content = "\n\n".join(fake.paragraphs(nb=random.randint(2, 4)))

                    PageContentBlock.objects.create(
                        page=page,
                        block_type=block_type,
                        title=f"{title} - Bloco {i + 1}",
                        content=content,
                        image=fake.image_url()
                        if random.choice([True, False])
                        else None,
                        order=i,
                    )

        self.stdout.write(f"✅ Created {len(pages_data)} pages with content blocks")

    def create_year_goals(self):
        """Create CECAB goals for 2024-2026."""
        goals_data = [
            ("Produção de Cacau (toneladas)", 12000, 15000, 18000),
            ("Produção de Chocolate (toneladas)", 500, 800, 1200),
            ("Agricultores Beneficiados", 800, 1200, 2000),
            ("Associações Parceiras", 5, 8, 12),
            ("Turistas Atendidos", 2000, 3500, 5000),
            ("Rota de Café e Cacau (km)", 50, 80, 120),
        ]

        for label, v2024, v2025, v2026 in goals_data:
            for year, value in [(2024, v2024), (2025, v2025), (2026, v2026)]:
                YearGoal.objects.get_or_create(
                    year=year,
                    label=f"{label} {year}",
                    defaults={"value": Decimal(str(value)), "show_in_dashboard": True},
                )

        self.stdout.write("✅ Created year goals for 2024-2026")

    def create_blog_categories(self):
        """Create blog categories."""
        categories_data = [
            ("Notícias", "noticias"),
            ("Projetos", "projetos"),
            ("Agricultura", "agricultura"),
            ("Turismo", "turismo"),
            ("Sustentabilidade", "sustentabilidade"),
            ("Eventos", "eventos"),
            ("História", "historia"),
        ]

        categories = []
        for name, slug in categories_data:
            category, created = BlogCategory.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )
            categories.append(category)

        self.stdout.write(f"✅ Created {len(categories)} blog categories")
        return categories

    def create_posts(self, categories, num_posts, tenant):
        """Create blog posts for CECAB."""
        post_titles_pt = [
            "CECAB celebra 10 anos de produção de chocolate",
            "Nova rota turística das roças de cacau",
            "Projeto de sustentabilidade na Ilha do Príncipe",
            "CECAB presente na feira internacional de chocolate",
            "Formação de agricultores em técnicas sustentáveis",
            "CECAB e comércio justo: uma história de sucesso",
            "Visita guiada às plantações de cacau",
            "Oficina de chocolate atrai turistas",
            "CECAB investe em energias renováveis",
            "São Tomé: o paraíso do cacau",
            "CECAB lança novo chocolate com café",
            "A história das roças de São Tomé",
            "CECAB e os Objetivos de Desenvolvimento Sustentável",
            "Agricultura familiar em São Tomé",
            "O futuro do chocolate sustentável",
        ]

        for i in range(num_posts):
            category = (
                random.choice(categories) if random.choice([True, False]) else None
            )

            title = (
                random.choice(post_titles_pt)
                if i < len(post_titles_pt)
                else fake.sentence(nb_words=6)
            )

            try:
                post = Post.objects.create(
                    blog_category=category,
                    title=title,
                    slug=f"{fake.slug()}-{i}",
                    picture=fake.image_url(),
                    active=random.choice([True, True, True, False]),
                    featured=random.choice([True, True, False, False, False]),
                    is_a_service=random.choice([True, False]),
                    is_social_service=random.choice([True, False]),
                    is_to_front=random.choice([True, False]),
                    description=fake.paragraph(),
                    text="\n\n".join(fake.paragraphs(nb=random.randint(3, 6))),
                )

                # Add documents
                for _ in range(random.randint(1, 2)):
                    PostDocument.objects.create(
                        post=post, document=fake.file_name(extension="pdf")
                    )

                # Add images
                for _ in range(random.randint(2, 4)):
                    PostImage.objects.create(post=post, picture=fake.image_url())

                # Add videos (CECAB Band performances)
                if random.choice([True, False]):
                    video_title = random.choice(
                        [
                            "CECAB Band - Festival de Chocolate",
                            "CECAB Band - Concerto de Ano Novo",
                            "Apresentação da CECAB Band",
                            "Música e Tradição em São Tomé",
                        ]
                    )
                    video = Video.objects.create(
                        title=video_title,
                        link=f"https://www.youtube.com/watch?v={fake.uuid4()[:8]}",
                        picture=fake.image_url(),
                        is_band=random.choice([True, False]),
                        is_spot=random.choice([True, False]),
                        created_at=fake.date_between(
                            start_date="-1y", end_date="today"
                        ),
                    )
                    PostVideo.objects.create(post=post, video=video)

                # Add Q&A for service posts
                if post.is_a_service:
                    for _ in range(random.randint(2, 4)):
                        Information.objects.create(
                            service=post,
                            question=fake.sentence(nb_words=6) + "?",
                            information=fake.paragraph(),
                        )
            except IntegrityError:
                self.stdout.write("⚠️ Post already exists with slug")
                continue

        self.stdout.write(f"✅ Created {num_posts} blog posts")

    def create_videos(self):
        """Create videos for CECAB Band and promotional content."""
        videos_data = [
            ("CECAB Band - Performance Anual 2024", True, False),
            ("CECAB Band - Festival da Cidade", True, False),
            ("CECAB Band - Concerto de Natal", True, False),
            ("CECAB Band - Apresentação Cultural", True, False),
            ("Spot Promocional CECAB 2024", False, True),
            ("Documentário: A História do Cacau", False, True),
            ("Entrevista: Produtores de Cacau", False, False),
        ]

        for title, is_band, is_spot in videos_data:
            Video.objects.get_or_create(
                title=title,
                defaults={
                    "link": f"https://www.youtube.com/watch?v={fake.uuid4()[:8]}",
                    "picture": fake.image_url(),
                    "is_band": is_band,
                    "is_spot": is_spot,
                    "created_at": fake.date_between(start_date="-2y", end_date="today"),
                },
            )

        self.stdout.write("✅ Created videos")

    def create_roles(self):
        """Create CECAB organizational roles."""
        roles_data = [
            "Presidente",
            "Vice-Presidente",
            "Secretário-Geral",
            "Tesoureiro",
            "Coordenador de Produção",
            "Coordenador de Turismo",
            "Diretor de Sustentabilidade",
            "Diretor de Marketing",
            "Chefe de Relações Públicas",
            "Conselheiro",
        ]

        roles = []
        for title in roles_data:
            role, created = Role.objects.get_or_create(title=title)
            roles.append(role)

        self.stdout.write(f"✅ Created {len(roles)} roles")
        return roles

    def create_team_members(self, roles):
        """Create CECAB team members."""
        first_names = [
            "Manuel",
            "João",
            "José",
            "António",
            "Francisco",
            "Maria",
            "Ana",
            "Teresa",
            "Helena",
            "Cristina",
            "Pedro",
            "Carlos",
            "Rui",
            "Paulo",
            "Fernando",
        ]
        last_names = [
            "Santos",
            "Costa",
            "Silva",
            "Ramos",
            "Gomes",
            "Monteiro",
            "Almeida",
            "Lima",
            "Carvalho",
            "Pereira",
            "Souza",
            "Rodrigues",
            "Ferreira",
            "Martins",
            "Oliveira",
        ]

        for i in range(15):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            role = random.choice(roles)

            Team.objects.get_or_create(
                name=name,
                role=role,
                defaults={
                    "image": fake.image_url(),
                    "from_assembly": random.choice([True, False]),
                },
            )

        self.stdout.write("✅ Created team members")

    def create_budget_documents(self):
        """Create CECAB budget and financial documents."""
        current_year = datetime.now().year
        doc_data = [
            ("B", f"Orçamento {current_year}"),
            ("B", f"Orçamento {current_year - 1}"),
            ("R", f"Relatório Anual {current_year - 1}"),
            ("R", f"Relatório de Sustentabilidade {current_year - 1}"),
            ("L", "Estatutos da CECAB"),
            ("L", "Regulamento Interno"),
        ]

        for doc_type, title in doc_data:
            Budget.objects.get_or_create(
                title=title,
                defaults={
                    "slug": fake.slug(),
                    "text_file": fake.file_name(extension="pdf"),
                    "year": current_year if doc_type == "B" else current_year - 1,
                    "type": doc_type,
                },
            )

        self.stdout.write("✅ Created budget documents")

    def create_extra_documents(self):
        """Create additional CECAB documents."""
        doc_titles = [
            "Certificação de Comércio Justo",
            "Licença Ambiental",
            "Certificado Orgânico",
            "Declaração de Sustentabilidade",
            "Política de Qualidade",
        ]

        for title in doc_titles:
            extra, created = ExtraDoc.objects.get_or_create(
                title=title,
                defaults={
                    "slug": fake.slug(),
                    "picture": fake.image_url(),
                    "text_file": fake.file_name(extension="pdf"),
                    "active": random.choice([True, False]),
                },
            )

            if created:
                for _ in range(random.randint(1, 3)):
                    ExtraImage.objects.create(picture=fake.image_url(), extra_doc=extra)

        self.stdout.write("✅ Created extra documents")

    def create_partners(self):
        """Create CECAB partner organizations."""
        partners_data = [
            "Comércio Justo Internacional",
            "Fairtrade Foundation",
            "Rainforest Alliance",
            "Cocoa Horizons",
            "World Cocoa Foundation",
            "Instituto do Cacau de São Tomé",
            "Ministério da Agricultura",
            "Sustainable Trade Initiative",
            "EcoCert",
            "Organic Alliance",
        ]

        for name in partners_data:
            Partner.objects.get_or_create(
                title=name, defaults={"picture": fake.image_url()}
            )

        self.stdout.write("✅ Created partners")
