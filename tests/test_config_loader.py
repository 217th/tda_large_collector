from tda_collector.config import load_config


def test_config_loader_parses_yaml(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
settings:
  update_interval_seconds: 30
exchanges:
  binance:
    - symbol: "BTC/USDT"
      timeframes: ["1m", "1h"]
""",
        encoding="utf-8",
    )

    cfg = load_config(str(cfg_file))
    assert cfg.settings.update_interval_seconds == 30
    assert "binance" in cfg.exchanges
    pair = cfg.exchanges["binance"][0]
    assert pair.symbol == "BTC/USDT"
    assert pair.timeframes == ["1m", "1h"]

