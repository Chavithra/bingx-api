import json
from pathlib import Path

import polars as pl


def read_margin_tiered() -> dict:
    path = Path(
        "/home/chavithra/code/python/robot/robot_one/payload/swap_v1_quote_contract_margin_tiered.json"
    )

    margin_tiered = {}
    with path.open(mode="r") as f:
        margin_tiered = json.load(f)

    return margin_tiered


def read_maintenance_tiered_as_df(
    margin_tiered_map: dict | None = None,
) -> pl.DataFrame:
    margin_tiered_map = margin_tiered_map or read_margin_tiered()
    symbol_list = list(margin_tiered_map.keys())
    maintenance_tiered_lap = [
        margin_tiered_map[symbol]["maintenanceTiered"] for symbol in symbol_list
    ]

    maintenance_tiered_df = (
        pl.DataFrame(
            {
                "symbol": symbol_list,
                "maintenance_tiered": maintenance_tiered_lap,
            }
        )
        .with_columns(
            pl.col("maintenance_tiered")
            .str.split(";")
            .alias("row_split_maintenance_tiered")
        )
        .explode("row_split_maintenance_tiered")
        .with_columns(
            pl.col("row_split_maintenance_tiered")
            .str.split_exact(":", 4)
            .struct.rename_fields(
                [
                    "position",
                    "maintenance_rate",
                    "leverage_max",
                    "maintenance_amount",
                ],
            )
            .alias("row_split_maintenance_tiered_fields")
        )
        .unnest("row_split_maintenance_tiered_fields")
        .with_columns(
            pl.col("leverage_max").cast(pl.Int64),
            pl.col("maintenance_amount").cast(pl.Float64),
            pl.col("maintenance_rate").cast(pl.Float64),
        )
        .with_columns(
            pl.col("position")
            .str.split_exact("-", 1)
            .struct.rename_fields(
                [
                    "position_min",
                    "position_max",
                ],
            )
            .alias("position_fields")
        )
        .unnest("position_fields")
        .with_columns(
            pl.col("position_min").cast(pl.Int64),
            pl.col("position_max").cast(pl.Int64),
        )
        .drop(
            [
                "maintenance_tiered",
                "row_split_maintenance_tiered",
                "position",
            ]
        )
    )

    return maintenance_tiered_df


if __name__ == "__main__":
    pass
