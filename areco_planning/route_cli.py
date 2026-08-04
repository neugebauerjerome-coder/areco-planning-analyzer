from __future__ import annotations

import argparse
import json
from pathlib import Path

from .route_engine.service import build_ors_route_service


def main() -> int:
    parser = argparse.ArgumentParser(description="ARECO Route Engine V4.0.2")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--stop", action="append", required=True)
    parser.add_argument("--return-address")
    parser.add_argument("--cache", type=Path, default=Path("data/route_cache.sqlite"))
    parser.add_argument("--no-optimize", action="store_true")
    args = parser.parse_args()

    service, cache = build_ors_route_service(args.api_key, args.cache)
    try:
        result = service.build_route(
            start_address=args.start,
            stop_addresses=args.stop,
            return_address=args.return_address,
            optimize_order=not args.no_optimize,
        )
        print(json.dumps({
            "distance_km": result.distance_km,
            "duration_hours": result.duration_hours,
            "points": [point.label for point in result.points],
            "legs": [
                {
                    "origin": leg.origin,
                    "destination": leg.destination,
                    "distance_km": leg.distance_km,
                    "duration_hours": leg.duration_hours,
                }
                for leg in result.legs
            ],
        }, ensure_ascii=False, indent=2))
    finally:
        cache.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
