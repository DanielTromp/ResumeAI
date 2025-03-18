#!/usr/bin/env python3
"""
ResumeAI Configuration Explorer

This script displays information about the ResumeAI configuration system.
It can be used to:
1. Show all available configuration options
2. Show current configuration values
3. Generate a template .env file
"""

import json
import argparse
import sys
from app.config import config
from pathlib import Path


def print_config_description():
    """Print a description of the configuration system."""
    print("ResumeAI Configuration System")
    print("=============================")
    print()
    print("This application uses a hierarchical configuration system with the following precedence:")
    print("1. Command-line arguments (highest priority)")
    print("   Format: --config.section.key=value")
    print("2. Environment variables")
    print("3. Configuration files (.env)")
    print("4. Default values (lowest priority)")
    print()
    print("Environment files are loaded in the following order:")
    print("1. .env.local (local developer overrides, not committed)")
    print("2. backend/.env (backend-specific configuration)")
    print("3. .env (project-wide configuration)")
    print()


def print_current_config(section=None):
    """Print the current configuration."""
    config_dict = config.model_dump()
    
    # Filter by section if specified
    if section and section in config_dict:
        config_dict = {section: config_dict[section]}
    
    print(json.dumps(config_dict, indent=2))


def print_env_template():
    """Generate and print a template .env file."""
    template = """# ResumeAI Environment Configuration Template
# Generated from current configuration schema

# Database Configuration
PG_HOST={database.host}
PG_PORT={database.port}
PG_USER={database.user}
PG_PASSWORD={database.password}
PG_DATABASE={database.database}

# OpenAI Configuration
OPENAI_API_KEY={openai.api_key}
AI_MODEL={openai.model}
EMBEDDING_MODEL={openai.embedding_model}

# Spinweb Scraper Configuration
SPINWEB_USER={spinweb.username}
SPINWEB_PASS={spinweb.password}
SPINWEB_LOGIN={spinweb.login_url}
SOURCE_URL={spinweb.source_url}
PROVIDER_NAME={spinweb.provider_name}

# Matching Configuration
MATCH_THRESHOLD={matching.threshold}
MATCH_COUNT={matching.count}
RESUME_RPC_FUNCTION_NAME={matching.rpc_function_name}
EXCLUDED_CLIENTS={excluded_clients}
PDF_FOLDER={matching.pdf_folder}
POSTGRES_RESUME_TABLE={matching.resume_table}

# Cron-based Processing
# The scheduled process has been moved to system cron
# No configuration needed here - use crontab -e to configure

# The prompt template can be overridden here or provided in app/prompt_template.txt
# RESUME_PROMPT_TEMPLATE=your custom prompt template here
""".format(
        database=config.database,
        openai=config.openai,
        spinweb=config.spinweb,
        matching=config.matching,
        scheduler=config.scheduler,
        excluded_clients=",".join(config.matching.excluded_clients),
        scheduler_days=",".join(config.scheduler.days)
    )
    
    print(template)


def main():
    """Main function for the configuration explorer."""
    parser = argparse.ArgumentParser(description="ResumeAI Configuration Explorer")
    parser.add_argument(
        "--show",
        choices=["all", "database", "openai", "spinweb", "matching", "scheduler", "template"],
        default="all",
        help="Show specific configuration section or template"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (if not specified, output to console)"
    )
    
    args = parser.parse_args()
    
    # Prepare the output
    output = []
    output.append(print_config_description)
    
    if args.show == "template":
        output.append(print_env_template)
    elif args.show == "all":
        output.append(lambda: print_current_config())
    else:
        output.append(lambda: print_current_config(args.show))
    
    # Capture output if needed
    if args.output:
        output_path = Path(args.output)
        original_stdout = sys.stdout
        try:
            with open(output_path, "w") as f:
                sys.stdout = f
                for func in output:
                    func()
                    print()
            print(f"Configuration information written to {output_path}")
        finally:
            sys.stdout = original_stdout
    else:
        for func in output:
            func()
            print()


if __name__ == "__main__":
    main()