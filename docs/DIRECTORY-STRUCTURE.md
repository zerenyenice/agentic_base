The top-level structure is standardized.
The internal implementation is adapted to the product.
Product-specific capabilities remain optional.

repository-root/
├── backend/          # Server-side application code
├── frontend/         # User-interface application code
├── infrastructure/   # Provisioning of cloud and platform resources
├── devops/           # CI/CD, build, quality, and security automation
├── deploy/           # Runtime deployment definitions
├── docs/             # Product and technical knowledge
├── tests/            # Cross-component and product-level verification
│
├── README.md
├── CLAUDE.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODEOWNERS
├── Makefile
├── .env.example
└── .gitignore