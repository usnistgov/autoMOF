source .venv/bin/activate

timeout 600m uv run schedule_scale_test_timebudget.py
timeout 600m uv run schedule_scale_test.py
timeout 600m uv run schedule_scale_test_hs.py


