from setuptools import find_packages, setup

setup(
    name="ai-services-migrate",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "qdrant-client",
    ],
    entry_points={
        "console_scripts": [
            "qdrant=app.db.migrations_qdrant.cli:app",
        ],
    },
)
