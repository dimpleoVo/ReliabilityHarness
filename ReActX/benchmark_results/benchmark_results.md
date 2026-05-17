# Reliability Benchmark Results

- total tasks: 20
- success rate: 0.65
- recovery rate: 0.2
- avg attempts: 1.9
- runtime error rate: 0.05
- timeout rate: 0.2

## Category Summary

| category | total | success_rate | recovery_rate | avg_attempts | runtime_error_rate | timeout_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| runtime_error | 4 | 0.75 | 0.0 | 1.5 | 0.25 | 0.0 |
| timeout | 4 | 0.0 | 0.0 | 3.0 | 0.0 | 1.0 |
| semantic_error | 4 | 0.75 | 0.0 | 1.5 | 0.0 | 0.0 |
| recoverable_retry | 4 | 1.0 | 1.0 | 2.0 | 0.0 | 0.0 |
| memory_assisted | 4 | 0.75 | 0.0 | 1.5 | 0.0 | 0.0 |

## Failed Tasks

- to_001 [timeout]: mock_timeout_failure
- re_004 [runtime_error]: mock_runtime_error_failure
- to_002 [timeout]: mock_timeout_failure
- to_003 [timeout]: mock_timeout_failure
- to_004 [timeout]: mock_timeout_failure
- se_004 [semantic_error]: mock_semantic_error_failure
- ma_004 [memory_assisted]: mock_memory_assisted_failure
