import argparse
import importlib
from pathlib import Path
import sys
from colorama import Fore, Style

def print_logo():
    """Print ASCII logo for AUDIO TOOL"""
    logo = f"""{Fore.CYAN}
    █████╗ ██╗   ██╗██████╗ ██╗ ██████╗     ████████╗ ██████╗  ██████╗ ██╗
    ██╔══██╗██║   ██║██╔══██╗██║██╔═══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║
    ███████║██║   ██║██║  ██║██║██║   ██║       ██║   ██║   ██║██║   ██║██║
    ██╔══██║██║   ██║██║  ██║██║██║   ██║       ██║   ██║   ██║██║   ██║██║
    ██║  ██║╚██████╔╝██████╔╝██║╚██████╔╝       ██║   ╚██████╔╝╚██████╔╝███████╗
    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝        ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
    {Style.RESET_ALL}
    """
    print(logo)

def main():
    """Set up CLI and dynamically register commands from modules in subfolders."""
    parser = argparse.ArgumentParser(
        description="Tool for managing audio files",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--workers", type=int, help="Number of worker processes")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Dynamically import and register modules from subdirectories in 'modules'
    modules_dir = Path(__file__).parent / 'modules'
    for module_folder in modules_dir.iterdir():
        if module_folder.is_dir():
            # Only load the main module file named after the folder (e.g., album_counter.py)
            main_module_file = module_folder / f"{module_folder.name}.py"
            if main_module_file.exists():
                module_name = f"modules.{module_folder.name}.{module_folder.name}"
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, 'register_command'):
                        module.register_command(subparsers)
                    else:
                        print(f"Warning: Module {module_name} does not have a 'register_command' function.")
                except ImportError as e:
                    print(f"Error importing module {module_name}: {e}")

    # Check if no arguments were provided
    if len(sys.argv) == 1:
        print_logo()
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # If command is provided but no func is set (shouldn't happen with required=True)
    if not hasattr(args, 'func'):
        print_logo()
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Quitting job...")
