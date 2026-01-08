#!/usr/bin/env python3
"""CLI for running LLM Council queries without the web interface."""

import argparse
import asyncio
import sys

from backend.council import run_full_council
from backend.config import COUNCIL_MODELS, CHAIRMAN_MODEL


def print_stage1(results: list) -> None:
    """Print Stage 1 results."""
    print("\n" + "=" * 60)
    print("STAGE 1: Individual Responses")
    print("=" * 60)
    for result in results:
        print(f"\n--- {result['model']} ---")
        print(result['response'])


def print_stage2(results: list, label_to_model: dict) -> None:
    """Print Stage 2 results."""
    print("\n" + "=" * 60)
    print("STAGE 2: Peer Rankings")
    print("=" * 60)
    for result in results:
        print(f"\n--- {result['model']} ---")
        print(result['ranking'])
        if result.get('parsed_ranking'):
            print(f"\nExtracted ranking: {result['parsed_ranking']}")


def print_aggregate(aggregate_rankings: list) -> None:
    """Print aggregate rankings."""
    print("\n" + "=" * 60)
    print("AGGREGATE RANKINGS")
    print("=" * 60)
    for i, entry in enumerate(aggregate_rankings, 1):
        print(f"{i}. {entry['model']} (avg rank: {entry['average_rank']}, votes: {entry['rankings_count']})")


def print_stage3(result: dict) -> None:
    """Print Stage 3 result."""
    print("\n" + "=" * 60)
    print(f"STAGE 3: Final Synthesis (Chairman: {result['model']})")
    print("=" * 60)
    print(result['response'])


async def run_council(prompt: str, show_all: bool = False, show_rankings: bool = False) -> None:
    """Run the council and print results."""
    print(f"Council: {', '.join(COUNCIL_MODELS)}")
    print(f"Chairman: {CHAIRMAN_MODEL}")
    print(f"\nPrompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print("\nRunning council deliberation...")

    stage1, stage2, stage3, metadata = await run_full_council(prompt)

    if show_all:
        print_stage1(stage1)
        print_stage2(stage2, metadata.get('label_to_model', {}))
        print_aggregate(metadata.get('aggregate_rankings', []))

    if show_rankings and not show_all:
        print_aggregate(metadata.get('aggregate_rankings', []))

    print_stage3(stage3)


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM Council queries from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "What are the key trends in AI?"
  python cli.py --file prompt.txt
  echo "My question" | python cli.py
  python cli.py --all "Compare Python and Rust"
        """
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        help="The prompt to send to the council"
    )
    parser.add_argument(
        "-f", "--file",
        help="Read prompt from a file"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Show all stages (1, 2, and 3) instead of just the final synthesis"
    )
    parser.add_argument(
        "-r", "--rankings",
        action="store_true",
        help="Show aggregate rankings in addition to final synthesis"
    )

    args = parser.parse_args()

    # Determine the prompt source
    if args.file:
        with open(args.file, 'r') as f:
            prompt = f.read().strip()
    elif args.prompt:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    else:
        parser.print_help()
        sys.exit(1)

    if not prompt:
        print("Error: Empty prompt", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run_council(prompt, show_all=args.all, show_rankings=args.rankings))


if __name__ == "__main__":
    main()
