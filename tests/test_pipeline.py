def test_pipeline_fails_on_mid_read_error(tmp_path: Path, caplog):
    sample_csv = _write_csv(
        tmp_path / "sample.csv",
        header=["CODE", "POSTCODE", "NUMBER_OF_PATIENTS"],
        rows=[
            ["A81001", "TS18 1HU", "100"],
            ["A81002", "TS18 2AA", "200"],
        ],
    )
    loaded_out = tmp_path / "loaded.csv"
    rejected_out = tmp_path / "rejected.jsonl"

    def failing_reader(path: str):
        for row_num, row in read_csv_chunks(path, has_header=True):
            if row_num == 2:
                raise RuntimeError("Simulated mid-file read error")
            yield row_num, row

    registry = {
        "registrations": (failing_reader, map_source2_row, sample_csv, True),
    }

    with caplog.at_level("INFO"):
        exit_code = run_pipeline(
            registry=registry,
            loaded_path=loaded_out,
            rejected_path=rejected_out,
        )

    assert exit_code == 1
    assert not loaded_out.exists()
    assert "Pipeline FAILED" in caplog.text
    