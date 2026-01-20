import sys
import argparse
import requests
import json
import os

CONTRACT_VERSION = 1
EXIT_CODES = {
    "proceed": 0,
    "warnings_only": 10,
    "conflict_arbitration_required": 20,
    "hard_reject": 30,
}


def main():
    parser = argparse.ArgumentParser(description="Control Point CLI Gate Check")
    parser.add_argument("--repo", type=str, default=None)
    parser.add_argument("--path", type=str, default=None)
    parser.add_argument("--subsystem", type=str, default=None)
    parser.add_argument("--api", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--machine", action="store_true")
    parser.add_argument("--url", type=str, default="http://localhost:8000/gate/check")
    parser.add_argument("--arbitrate", action="store_true")
    args = parser.parse_args()

    scope = {
        k: v
        for k, v in vars(args).items()
        if k in ("repo", "path", "subsystem", "api") and v
    }
    if not scope:
        print("ERROR: At least one scope argument is required.", file=sys.stderr)
        sys.exit(EXIT_CODES["hard_reject"])

    def run_gate():
        payload = json.dumps(scope)
        headers = {"Content-Type": "application/json"}
        r = requests.post(args.url, data=payload, headers=headers)
        result = r.json()
        if result.get("contract_version") != CONTRACT_VERSION:
            print(
                f"ERROR: Contract version mismatch (expected {CONTRACT_VERSION}, got {result.get('contract_version')})",
                file=sys.stderr,
            )
            sys.exit(EXIT_CODES["hard_reject"])
        return result

    result = run_gate()
    summary = result["summary"]
    pass_ = result["pass_"]
    conflicted = summary["conflicted"]
    violated = summary["violated"]
    unknown = summary["unknown"]

    # Only output JSON if --machine
    if args.machine:
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))

    # If conflicts, prompt for arbitration
    while not pass_ and conflicted and not args.machine:
        for conflict in result["conflicts"]:
            print(f"\nConflict {conflict['conflict_id']}:")
            print(f"Question: {conflict['question']}")
            for idx, choice in enumerate(conflict["choices"]):
                print(
                    f"  [{choice['key'].upper()}] {choice['label']} - {choice['effect']}"
                )
            user_choice = None
            valid_keys = [c["key"] for c in conflict["choices"]]
            while user_choice not in valid_keys:
                user_choice = (
                    input(f"Enter choice ({'/'.join(valid_keys)}): ").strip().lower()
                )
            # Submit arbitration
            arbitration = {
                "conflict_id": conflict["conflict_id"],
                "decision": user_choice,
                "justification": "Arbitrated via CLI.",
                "scope": scope,
            }
            arb_url = args.url.replace("/gate/check", "/control-point/arbitrate")
            r2 = requests.post(
                arb_url,
                data=json.dumps(arbitration),
                headers={"Content-Type": "application/json"},
            )
            arb_result = r2.json()
            if arb_result.get("status") != "accepted":
                print(f"Arbitration failed: {arb_result.get('reason')}")
                sys.exit(EXIT_CODES["hard_reject"])
        # Re-run gate after arbitration
        result = run_gate()
        summary = result["summary"]
        pass_ = result["pass_"]
        conflicted = summary["conflicted"]
        violated = summary["violated"]
        unknown = summary["unknown"]
        if args.machine:
            print(json.dumps(result, separators=(",", ":")))
        else:
            print(json.dumps(result, indent=2, sort_keys=True))

    # Exit codes
    if args.dry_run:
        sys.exit(EXIT_CODES["proceed"])
    if not pass_:
        if conflicted:
            sys.exit(EXIT_CODES["conflict_arbitration_required"])
        if violated:
            sys.exit(EXIT_CODES["hard_reject"])
        if unknown:
            sys.exit(EXIT_CODES["hard_reject"])
    sys.exit(EXIT_CODES["proceed"])


if __name__ == "__main__":
    main()
